"""Shared fixtures for the API-level tests."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).parents[1]


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    """Controller app with isolated settings, a temporary catalog and no network."""
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
        "GPUHARBOR_UPDATE_CHECK": "false",
        "RUNPOD_ALLOW_BILLABLE_ACTIONS": "false",
        "GPUHARBOR_COOKIE_SECURE": "false",
        "RUNTIME_IMAGE_VLLM": "ghcr.io/example/vllm@sha256:" + "a" * 64,
        "RUNTIME_IMAGE_LLAMA_CPP": "",
        "RUNTIME_IMAGE_BONSAI": "",
        "MODELS_PATH": str(tmp_path / "data" / "models.json"),
        "USER_CATALOG_PATH": str(tmp_path / "data" / "user-models.json"),
        "BUNDLED_MODELS_PATH": str(models),
        "RUNTIMES_PATH": str(runtimes),
        "STATE_PATH": str(tmp_path / "data" / "state.json"),
        "PREFERENCES_PATH": str(tmp_path / "data" / "preferences.json"),
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    # Never pick up a developer's real .env from the project folder.
    monkeypatch.chdir(tmp_path)

    sys.modules.pop("gpuharbor.main", None)
    main = importlib.import_module("gpuharbor.main")
    with TestClient(main.app) as client:
        yield client, main
    sys.modules.pop("gpuharbor.main", None)
