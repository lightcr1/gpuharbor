from pathlib import Path

from gpuharbor.idle import should_stop_for_idle
import pytest

from gpuharbor.security import LoginLimiter, redact_secrets
from gpuharbor.state import ControllerState


def test_login_limiter_blocks_within_window_and_expires():
    limiter = LoginLimiter(maximum=2, window_seconds=60)
    limiter.failure("client", now=10)
    assert not limiter.blocked("client", now=20)
    limiter.failure("client", now=20)
    assert limiter.blocked("client", now=30)
    assert not limiter.blocked("client", now=81)


def test_login_limiter_success_clears_failures():
    limiter = LoginLimiter(maximum=1, window_seconds=60)
    limiter.failure("client", now=10)
    assert limiter.blocked("client", now=11)
    limiter.success("client")
    assert not limiter.blocked("client", now=12)


def test_idle_policy_can_be_disabled_and_obeys_boundary():
    assert not should_stop_for_idle(100000, 0)
    assert not should_stop_for_idle(1799, 30)
    assert should_stop_for_idle(1800, 30)


def test_controller_state_rejects_host_or_path_injection():
    with pytest.raises(ValueError, match="pod ID"):
        ControllerState(pod_id="../../metadata")
    with pytest.raises(ValueError, match="pod ID"):
        ControllerState(pod_id="evil.example/path")


def test_recursive_secret_redaction():
    value = {
        "env": {"HF_TOKEN": "secret", "MODEL_ID": "safe"},
        "nested": [{"apiKey": "secret-2", "status": "ok"}],
    }
    redacted = redact_secrets(value)
    assert redacted["env"] == {"HF_TOKEN": "***", "MODEL_ID": "safe"}
    assert redacted["nested"][0]["apiKey"] == "***"


def test_secure_equals_handles_non_ascii_and_empty_values():
    from gpuharbor.security import bearer_token, secure_equals

    assert secure_equals("secret", "secret")
    assert not secure_equals("secret", "secrèt")
    assert not secure_equals("secret", None)
    assert not secure_equals("", "")
    assert bearer_token("bearer abc") == "abc"
    assert bearer_token("Basic abc") == ""
    assert bearer_token(None) == ""


def test_non_ascii_credentials_are_rejected_not_crashed(app_client):
    client, _ = app_client
    assert client.get("/api/status", headers={"X-Control-Token": "tökén".encode()}).status_code == 401
    assert client.get("/v1/models", headers={"Authorization": "Bearer tökén".encode()}).status_code == 401
    login = client.post("/api/login", json={"username": "ädmin", "password": "pässword"})
    assert login.status_code == 401


def test_template_placeholder_credentials_are_refused(monkeypatch):
    import pytest
    from gpuharbor.config import Settings

    values = {
        "RUNPOD_API_KEY": "r" * 40,
        "CONTROL_TOKEN": "c" * 40,
        "MODEL_ACCESS_TOKEN": "m" * 40,
        "RUNTIME_GATEWAY_TOKEN": "g" * 40,
        "GPUHARBOR_ADMIN_PASSWORD": "replace-with-a-long-random-password",
        "GPUHARBOR_SESSION_SECRET": "s" * 40,
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match="GPUHARBOR_ADMIN_PASSWORD"):
        Settings(_env_file=None)


def test_logout_revokes_a_copied_session_cookie(app_client):
    client, _ = app_client
    login = client.post("/api/login", json={"username": "admin", "password": "p" * 40})
    assert login.status_code == 200
    stolen = client.cookies.get("gpuharbor_session")
    csrf = login.json()["csrf_token"]
    assert client.post("/api/logout", headers={"X-CSRF-Token": csrf}).status_code == 200

    from fastapi.testclient import TestClient

    with TestClient(client.app, cookies={"gpuharbor_session": stolen}) as other:
        assert other.get("/api/status").status_code == 401
        assert other.get("/api/me").json()["authenticated"] is False


def _settings_env(monkeypatch, **overrides):
    values = {
        "RUNPOD_API_KEY": "r" * 40, "CONTROL_TOKEN": "c" * 40, "MODEL_ACCESS_TOKEN": "m" * 40,
        "RUNTIME_GATEWAY_TOKEN": "g" * 40, "GPUHARBOR_ADMIN_PASSWORD": "p" * 24, "GPUHARBOR_SESSION_SECRET": "s" * 40,
    }
    values.update(overrides)
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_every_credential_from_env_example_is_refused(monkeypatch):
    """Copying .env.example unchanged must never produce a running controller."""
    import pytest
    from gpuharbor.config import Settings

    example = {}
    for line in (Path(__file__).parents[1] / ".env.example").read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            example[key] = value
    placeholders = [key for key, value in example.items() if value.startswith("replace")]
    assert {"CONTROL_TOKEN", "MODEL_ACCESS_TOKEN", "RUNTIME_GATEWAY_TOKEN", "GPUHARBOR_ADMIN_PASSWORD",
            "GPUHARBOR_SESSION_SECRET", "WEBUI_SECRET_KEY", "OPENHANDS_BACKEND_API_KEY"} <= set(placeholders)
    for key in placeholders:
        if key == "RUNPOD_API_KEY":
            continue  # a placeholder key is harmless: it cannot start a pod
        _settings_env(monkeypatch, **{key: example[key]})
        with pytest.raises(ValueError, match=key):
            Settings(_env_file=None)


def test_short_credentials_are_refused_at_startup(monkeypatch):
    import pytest
    from gpuharbor.config import Settings

    _settings_env(monkeypatch, GPUHARBOR_ADMIN_PASSWORD="admin123")
    with pytest.raises(ValueError, match="too short"):
        Settings(_env_file=None)
    _settings_env(monkeypatch)
    assert Settings(_env_file=None).gpuharbor_admin_password.get_secret_value() == "p" * 24
