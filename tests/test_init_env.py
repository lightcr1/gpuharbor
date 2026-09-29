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
    assert "0.0.0.0" not in values["GPUHARBOR_TRUSTED_HOSTS"], "0.0.0.0 is never a Host header"
    assert values["RUNPOD_ALLOW_BILLABLE_ACTIONS"] == "false"
    for key in ("RUNPOD_API_KEY", "CONTROL_TOKEN", "MODEL_ACCESS_TOKEN", "GPUHARBOR_ADMIN_PASSWORD"):
        assert "replace" not in values[key].lower()
    for key in ("RUNPOD_API_KEY", "CONTROL_TOKEN", "MODEL_ACCESS_TOKEN"):
        assert len(values[key]) == 64
    assert len(values["GPUHARBOR_ADMIN_PASSWORD"]) == 24  # readable groups, see the dedicated test


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
        "--bind-ip", "0.0.0.0", "--https-host", "192.0.2.10", "--tls-port", "9443",
    )
    values = read_values(target)
    assert values["GPUHARBOR_COOKIE_SECURE"] == "true"
    assert values["TLS_BIND_IP"] == "192.0.2.10"
    assert values["TLS_PORT"] == "9443"
    assert values["HOST_BIND_IP"] == "0.0.0.0"
    assert "192.0.2.10" in values["GPUHARBOR_TRUSTED_HOSTS"]


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


def test_init_env_add_trusted_host_keeps_existing(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
    target = tmp_path / ".env"

    run("--env", str(target), "--example", str(example), "--bind-ip", "192.0.2.10")
    run("--env", str(target), "--example", str(example), "--add-trusted-host", "192.168.1.5")
    hosts = read_values(target)["GPUHARBOR_TRUSTED_HOSTS"].split(",")
    assert "192.0.2.10" in hosts
    assert "192.168.1.5" in hosts


def test_show_login_and_reset_password(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text(
        "GPUHARBOR_ADMIN_USERNAME=admin\nGPUHARBOR_ADMIN_PASSWORD=replace-me\nCONTROL_TOKEN=replace-me\n",
        encoding="utf-8",
    )
    target = tmp_path / ".env"
    run("--env", str(target), "--example", str(example))
    before = read_values(target)
    shown = run("--env", str(target), "--show-login").stdout
    assert before["GPUHARBOR_ADMIN_PASSWORD"] in shown and "admin" in shown

    result = run("--env", str(target), "--example", str(example), "--reset-password")
    after = read_values(target)
    assert after["GPUHARBOR_ADMIN_PASSWORD"] != before["GPUHARBOR_ADMIN_PASSWORD"]
    assert after["CONTROL_TOKEN"] == before["CONTROL_TOKEN"]
    assert after["GPUHARBOR_ADMIN_PASSWORD"] in result.stdout


def test_upgrade_adds_settings_missing_from_an_older_env(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text(
        "CONTROL_TOKEN=replace-me\nOPEN_WEBUI_IMAGE=ghcr.io/example/open-webui@sha256:" + "a" * 64
        + "\nWEBUI_SECRET_KEY=replace-me\nTLS_PORT=8443\n",
        encoding="utf-8",
    )
    target = tmp_path / ".env"
    target.write_text("CONTROL_TOKEN=" + "c" * 64 + "\nTLS_PORT=9443\n", encoding="utf-8")
    run("--env", str(target), "--example", str(example))
    values = read_values(target)
    assert values["CONTROL_TOKEN"] == "c" * 64, "existing secrets stay"
    assert values["TLS_PORT"] == "9443", "existing settings stay"
    assert values["OPEN_WEBUI_IMAGE"].endswith("a" * 64), "new settings are added"
    assert len(values["WEBUI_SECRET_KEY"]) == 64 and "replace" not in values["WEBUI_SECRET_KEY"]


def test_generated_admin_password_is_readable_and_strong(tmp_path):
    import re

    example = tmp_path / ".env.example"
    example.write_text("GPUHARBOR_ADMIN_PASSWORD=replace-me\nCONTROL_TOKEN=replace-me\n", encoding="utf-8")
    target = tmp_path / ".env"
    run("--env", str(target), "--example", str(example))
    values = read_values(target)
    assert re.fullmatch(r"([A-HJKMNP-Z2-9]{4}-){4}[A-HJKMNP-Z2-9]{4}", values["GPUHARBOR_ADMIN_PASSWORD"])
    assert len(values["CONTROL_TOKEN"]) == 64, "machine tokens stay long hex values"
