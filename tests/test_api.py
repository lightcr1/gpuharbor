from __future__ import annotations

import json
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient


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


def test_runtimes_report_image_status(app_client):
    client, _ = app_client
    login(client)
    data = client.get("/api/runtimes").json()
    assert data["vllm"]["ready"] is True
    assert data["vllm"]["image"].startswith("ghcr.io/example/vllm@sha256:")
    assert data["bonsai"]["ready"] is False


def test_docs_favicon_and_presets_are_available(app_client):
    client, _ = app_client
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "Documentation" in docs.text
    assert "Trust Hugging Face remote code" in docs.text
    assert docs.headers["cache-control"] == "no-store"
    german = client.get("/docs/de")
    assert german.status_code == 200
    assert "Dokumentation" in german.text
    assert german.headers["cache-control"] == "no-store"
    icon = client.get("/favicon.svg")
    assert icon.status_code == 200
    assert icon.headers["content-type"].startswith("image/svg+xml")
    csrf = login(client)
    assert csrf
    presets = client.get("/api/model-presets").json()
    assert {"vllm-chat", "vllm-coding", "gguf-chat", "bonsai"} <= set(presets)
    assert client.get("/api/model-presets").status_code == 200


def test_gpu_options_and_regions_degrade_when_runpod_fails(app_client):
    from gpuharbor.runpod import RunpodError

    client, _ = app_client
    login(client)
    client.app.state.runpod.list_gpus = AsyncMock(side_effect=RunpodError("no key"))
    client.app.state.runpod.list_datacenters = AsyncMock(side_effect=RunpodError("no key"))

    gpus = client.get("/api/gpu-options").json()
    assert gpus["source"] == "fallback"
    assert any(entry["id"] == "NVIDIA A40" for entry in gpus["gpus"])

    regions = client.get("/api/regions").json()
    assert regions["source"] == "fallback"
    assert regions["regions"][0]["datacenters"]


def test_gpu_options_and_regions_use_live_catalog(app_client):
    client, _ = app_client
    login(client)
    client.app.state.runpod.list_gpus = AsyncMock(
        return_value=[
            {
                "id": "NVIDIA A40",
                "name": "A40",
                "memory": 48,
                "availability": "LOW",
                "price": {"secure": 0.49},
                "dataCenters": [{"id": "EU-SE-1", "availability": "LOW"}],
            }
        ]
    )
    client.app.state.runpod.list_datacenters = AsyncMock(
        return_value=[
            {"id": "EU-SE-1", "region": "EUROPE"},
            {"id": "US-KS-2", "region": "NORTH_AMERICA"},
        ]
    )
    gpus = client.get("/api/gpu-options").json()
    assert gpus["source"] == "live"
    assert gpus["gpus"][0]["secure_price"] == 0.49

    regions = client.get("/api/regions").json()
    assert regions["source"] == "live"
    by_id = {entry["id"]: entry for entry in regions["regions"]}
    assert by_id["EUROPE"]["datacenters"] == ["EU-SE-1"]
    assert by_id["EUROPE"]["label"] == "Europa"


def test_region_choice_expands_to_datacenters(app_client):
    client, _ = app_client
    csrf = login(client)
    client.app.state.runpod.list_datacenters = AsyncMock(
        return_value=[{"id": "EU-SE-1", "region": "EUROPE"}]
    )
    response = client.post(
        "/api/pod/plan",
        json={"model_id": "qwen38-27b-fp8", "region": "EUROPE"},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    candidates = response.json()["candidates"]
    assert {item["datacenter_id"] for item in candidates} == {"EU-SE-1"}


def test_region_and_datacenter_together_are_rejected(app_client):
    client, _ = app_client
    csrf = login(client)
    client.app.state.runpod.list_datacenters = AsyncMock(
        return_value=[{"id": "EU-SE-1", "region": "EUROPE"}]
    )
    response = client.post(
        "/api/pod/plan",
        json={"model_id": "qwen38-27b-fp8", "region": "EUROPE", "datacenter_id": "EU-SE-1"},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 422


def test_model_ready_reports_no_pod(app_client):
    client, _ = app_client
    login(client)
    assert client.get("/api/model/ready").json()["ready"] is False


def test_logout_requires_csrf_and_invalidates_session(app_client):
    client, _ = app_client
    csrf = login(client)
    assert client.post("/api/logout").status_code == 403
    assert client.post("/api/logout", headers={"X-CSRF-Token": csrf}).status_code == 200
    assert client.get("/api/me").json()["authenticated"] is False


def test_controller_settings_report_version_and_update_flag(app_client):
    client, _ = app_client
    login(client)
    settings = client.get("/api/controller-settings").json()
    assert settings["version"]
    assert settings["update_check_enabled"] is False


def test_update_check_is_disabled_by_default(app_client):
    client, _ = app_client
    login(client)
    result = client.get("/api/update-check").json()
    assert result["enabled"] is False
    assert result["current"]


def test_update_check_reports_available_release(app_client, monkeypatch):
    client, main = app_client
    csrf = login(client)
    saved = client.put("/api/settings", json={"update_notifications": True}, headers={"X-CSRF-Token": csrf})
    assert saved.status_code == 200
    monkeypatch.setattr(
        main,
        "fetch_latest",
        AsyncMock(return_value={"tag": "v9.9.9", "url": "https://example/release", "published_at": ""}),
    )
    result = client.get("/api/update-check").json()
    assert result["enabled"] is True
    assert result["update_available"] is True
    assert result["url"] == "https://example/release"


def test_settings_update_notifications_roundtrip(app_client):
    client, _ = app_client
    csrf = login(client)
    assert client.get("/api/settings").json()["update_notifications"] is False
    assert client.put("/api/settings", json={"update_notifications": True}).status_code == 403
    client.put("/api/settings", json={"update_notifications": True}, headers={"X-CSRF-Token": csrf})
    assert client.get("/api/settings").json()["update_notifications"] is True
    settings = client.get("/api/controller-settings").json()
    assert settings["update_check_enabled"] is True


def test_compose_service_name_is_an_accepted_host(app_client):
    """Open WebUI calls http://controller:8080/v1 inside the Compose network."""
    client, _ = app_client
    assert client.get("/health", headers={"Host": "controller:8080"}).status_code == 200
    assert client.get("/health", headers={"Host": "evil.example"}).status_code == 400
