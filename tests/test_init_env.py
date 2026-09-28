from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "init-env"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def read_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.strip().startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value
    return values


def test_init_env_generates_secrets_and_bind_ip(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
    target = tmp_path / ".env"

    run("--env", str(target), "--example", str(example), "--bind-ip", "0.0.0.0")
    values = read_values(target)

    assert values["HOST_BIND_IP"] == "0.0.0.0"
    assert "0.0.0.0" in values["GPUHARBOR_TRUSTED_HOSTS"]
    assert values["RUNPOD_ALLOW_BILLABLE_ACTIONS"] == "false"
    for key in ("RUNPOD_API_KEY", "CONTROL_TOKEN", "MODEL_ACCESS_TOKEN", "GPUHARBOR_ADMIN_PASSWORD"):
        assert "replace" not in values[key].lower()
        assert len(values[key]) == 64


def test_init_env_is_idempotent(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
    target = tmp_path / ".env"

    run("--env", str(target), "--example", str(example))
    first = target.read_text(encoding="utf-8")
    run("--env", str(target), "--example", str(example))
    assert target.read_text(encoding="utf-8") == first


def test_init_env_https_flags_enable_secure_cookie(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
    target = tmp_path / ".env"

    run(
        "--env", str(target), "--example", str(example),
        "--bind-ip", "0.0.0.0", "--https-host", "10.10.40.100", "--tls-port", "9443",
    )
    values = read_values(target)
    assert values["GPUHARBOR_COOKIE_SECURE"] == "true"
    assert values["TLS_BIND_IP"] == "10.10.40.100"
    assert values["TLS_PORT"] == "9443"
    assert values["HOST_BIND_IP"] == "0.0.0.0"
    assert "10.10.40.100" in values["GPUHARBOR_TRUSTED_HOSTS"]


def test_init_env_secrets_are_distinct(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
    target = tmp_path / ".env"

    run("--env", str(target), "--example", str(example))
    values = read_values(target)
    secrets_used = [values[key] for key in (
        "RUNPOD_API_KEY",
        "CONTROL_TOKEN",
        "MODEL_ACCESS_TOKEN",
        "RUNTIME_GATEWAY_TOKEN",
        "GPUHARBOR_ADMIN_PASSWORD",
        "GPUHARBOR_SESSION_SECRET",
    )]
    assert len(set(secrets_used)) == len(secrets_used)
