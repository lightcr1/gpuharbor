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
