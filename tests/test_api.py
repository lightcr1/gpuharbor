from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).parents[1]


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    models = tmp_path / "bundled-models.json"
    runtimes = tmp_path / "runtimes.json"
    models.write_text((ROOT / "registry/models.json").read_text(encoding="utf-8"), encoding="utf-8")
    runtimes.write_text((ROOT / "registry/runtimes.json").read_text(encoding="utf-8"), encoding="utf-8")

    values = {
        "RUNPOD_API_KEY": "r" * 40,
        "CONTROL_TOKEN": "c" * 40,
        "MODEL_ACCESS_TOKEN": "m" * 40,
        "RUNTIME_GATEWAY_TOKEN": "g" * 40,
        "GPUHARBOR_ADMIN_USERNAME": "admin",
        "GPUHARBOR_ADMIN_PASSWORD": "p" * 40,
        "GPUHARBOR_SESSION_SECRET": "s" * 40,
        "GPUHARBOR_TRUSTED_HOSTS": "testserver,localhost,127.0.0.1",
        "RUNPOD_ALLOW_BILLABLE_ACTIONS": "false",
        "RUNTIME_IMAGE_VLLM": "ghcr.io/example/vllm@sha256:" + "a" * 64,
        "MODELS_PATH": str(tmp_path / "data" / "models.json"),
        "USER_CATALOG_PATH": str(tmp_path / "data" / "user-models.json"),
        "BUNDLED_MODELS_PATH": str(models),
        "RUNTIMES_PATH": str(runtimes),
        "STATE_PATH": str(tmp_path / "data" / "state.json"),
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)

    sys.modules.pop("gpuharbor.main", None)
    main = importlib.import_module("gpuharbor.main")
    with TestClient(main.app) as client:
        yield client, main
    sys.modules.pop("gpuharbor.main", None)


def login(client: TestClient) -> str:
    response = client.post("/api/login", json={"username": "admin", "password": "p" * 40})
    assert response.status_code == 200
    return response.json()["csrf_token"]


def test_security_headers_and_unauthenticated_api(app_client):
    client, _ = app_client
    response = client.get("/")
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/api/models").status_code == 401
    assert client.get("/", headers={"Host": "evil.example"}).status_code == 400


def test_login_cookie_and_rate_limit(app_client):
    client, _ = app_client
    response = client.post("/api/login", json={"username": "admin", "password": "p" * 40})
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    client.post("/api/logout", headers={"X-CSRF-Token": response.json()["csrf_token"]})
    for _ in range(5):
        assert client.post("/api/login", json={"username": "admin", "password": "wrong"}).status_code == 401
    limited = client.post("/api/login", json={"username": "admin", "password": "wrong"})
    assert limited.status_code == 429
    assert "retry-after" in limited.headers


def test_session_mutations_require_csrf_but_control_token_does_not(app_client):
    client, _ = app_client
    csrf = login(client)
    payload = {"model_id": "qwen38-27b-fp8"}
    assert client.post("/api/pod/plan", json=payload).status_code == 403
    assert client.post("/api/pod/plan", json=payload, headers={"X-CSRF-Token": csrf}).status_code == 200

    client.cookies.clear()
    response = client.post(
        "/api/pod/plan",
        json=payload,
        headers={"X-Control-Token": "c" * 40},
    )
    assert response.status_code == 200


def test_plan_is_non_billable_and_redacts_runtime_token(app_client):
    client, _ = app_client
    csrf = login(client)
    response = client.post(
        "/api/pod/plan",
        json={"model_id": "qwen38-27b-fp8", "context_length": 32768},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    plan = response.json()
    assert plan["billable_actions_enabled"] is False
    assert plan["candidates"][0]["payload"]["env"]["GATEWAY_API_KEY"] == "***"
    assert "g" * 40 not in response.text


def test_model_crud_is_validated_and_persistent(app_client):
    client, _ = app_client
    csrf = login(client)
    model = {
        "name": "Eigenes Modell",
        "description": "Test",
        "model_id": "example/model",
        "runtime": "vllm",
        "served_names": ["custom"],
        "capabilities": ["chat"],
        "context_length": 8192,
        "max_sequences": 1,
        "gpu_memory_utilization": 0.8,
        "gpu_type_ids": ["NVIDIA A40"],
        "volume_gb": 20,
        "status": "experimental",
        "verified": False,
    }
    response = client.put(
        "/api/models/custom-model",
        json=model,
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    custom = client.get("/api/models").json()["custom-model"]
    assert custom["name"] == "Eigenes Modell"
    assert custom["source"] == "custom"

    invalid = {**model, "served_names": ["--host"]}
    response = client.put(
        "/api/models/unsafe-model",
        json=invalid,
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 422

    response = client.delete(
        "/api/models/custom-model", headers={"X-CSRF-Token": csrf}
    )
    assert response.status_code == 200
    assert "custom-model" not in client.get("/api/models").json()


def test_builtin_edit_creates_override_and_reset_restores_default(app_client):
    client, _ = app_client
    csrf = login(client)
    original = client.get("/api/models").json()["qwen38-27b-fp8"]
    editable = {
        key: value
        for key, value in original.items()
        if key not in {"active", "runtime_ready", "source", "overridden", "revision"}
    }
    editable["context_length"] = 32768
    response = client.put(
        "/api/models/qwen38-27b-fp8",
        json=editable,
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    changed = client.get("/api/models").json()["qwen38-27b-fp8"]
    assert changed["source"] == "override" and changed["overridden"] is True
    response = client.post(
        "/api/models/qwen38-27b-fp8/reset", headers={"X-CSRF-Token": csrf}
    )
    assert response.status_code == 200
    restored = client.get("/api/models").json()["qwen38-27b-fp8"]
    assert restored["source"] == "builtin"
    assert restored["context_length"] == original["context_length"]


def test_user_catalog_export_and_import(app_client):
    client, _ = app_client
    csrf = login(client)
    exported = client.get("/api/models-export").json()
    assert exported == {"schema_version": 1, "custom": {}, "overrides": {}}
    payload = {
        "schema_version": 1,
        "custom": {
            "imported-model": {
                "name": "Imported",
                "model_id": "example/imported",
                "runtime": "vllm",
                "served_names": ["imported"],
                "gpu_type_ids": ["NVIDIA A40"],
            }
        },
        "overrides": {},
    }
    response = client.post(
        "/api/models-import",
        json={"catalog": payload, "replace": False},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    assert client.get("/api/models").json()["imported-model"]["source"] == "custom"


def test_changed_profile_cannot_silently_restart_existing_pod(app_client):
    client, main = app_client
    csrf = login(client)
    main.settings.runpod_allow_billable_actions = True
    main.store.write(
        main.ControllerState(
            pod_id="existing-pod",
            model_id="qwen38-27b-fp8",
            runtime_id="vllm",
            profile_revision="old-revision",
            gpu_type_id="NVIDIA A40",
            datacenter_id="EU-SE-1",
            volume_gb=64,
        )
    )
    client.app.state.runpod.get_pod = AsyncMock(side_effect=AssertionError("must not query"))
    response = client.post(
        "/api/pod/start",
        json={"model_id": "qwen38-27b-fp8"},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 409
    assert "profile changed" in response.json()["detail"]
    client.app.state.runpod.get_pod.assert_not_called()


def test_billable_start_is_blocked_before_runpod_call(app_client):
    client, _ = app_client
    csrf = login(client)
    client.app.state.runpod.create_pod = AsyncMock(side_effect=AssertionError("must not run"))
    response = client.post(
        "/api/pod/start",
        json={"model_id": "qwen38-27b-fp8"},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 403
    client.app.state.runpod.create_pod.assert_not_called()


def test_model_proxy_rejects_oversized_request_before_upstream(app_client):
    client, _ = app_client
    response = client.post(
        "/v1/chat/completions",
        content=b"{}",
        headers={
            "Authorization": "Bearer " + "m" * 40,
            "Content-Type": "application/json",
            "Content-Length": str(21 * 1024 * 1024),
        },
    )
    assert response.status_code == 413


def test_logout_requires_csrf_and_invalidates_session(app_client):
    client, _ = app_client
    csrf = login(client)
    assert client.post("/api/logout").status_code == 403
    assert client.post("/api/logout", headers={"X-CSRF-Token": csrf}).status_code == 200
    assert client.get("/api/me").json()["authenticated"] is False
