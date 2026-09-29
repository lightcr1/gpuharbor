"""doctor, trust-ca and the installer's dry run."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def script(name: str, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name), *args],
        capture_output=True, text=True, cwd=ROOT, check=check,
    )


def test_doctor_flags_a_fresh_env_that_was_never_initialised(tmp_path):
    env = tmp_path / ".env"
    env.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
    result = script("doctor", "--offline", "--env", str(env))
    assert result.returncode == 1
    assert "Not set up yet" in result.stdout and "./scripts/init-env" in result.stdout


def test_doctor_is_happy_with_a_generated_env(tmp_path):
    env = tmp_path / ".env"
    script("init-env", "--env", str(env), "--example", str(ROOT / ".env.example"), check=True)
    result = script("doctor", "--offline", "--env", str(env))
    assert result.returncode == 0, result.stdout
    assert "all passwords and tokens are generated" in result.stdout
    assert "cost lock is on" in result.stdout


def test_doctor_reports_a_missing_env(tmp_path):
    result = script("doctor", "--offline", "--env", str(tmp_path / "missing"))
    assert result.returncode == 1 and "Run ./scripts/install" in result.stdout


def test_trust_ca_dry_run_prints_steps_and_changes_nothing(tmp_path):
    ca = tmp_path / "local-ca.crt"
    subprocess.run(
        [str(ROOT / "scripts" / "generate-local-tls"), "localhost", str(tmp_path)],
        check=True, capture_output=True,
    )
    result = script("trust-ca", "--ca", str(ca), "--dry-run")
    assert result.returncode == 0
    assert "Trust the GPUHarbor local CA" in result.stdout


def test_trust_ca_refuses_without_a_certificate(tmp_path):
    result = script("trust-ca", "--ca", str(tmp_path / "none.crt"), "--dry-run")
    assert result.returncode == 1 and "Run ./scripts/install first" in result.stderr


def test_installer_dry_run_wires_both_apps():
    result = script("install", "--dry-run", "--webui", "--openhands", check=True)
    for overlay in ("compose.openwebui.tls.yml", "compose.openhands.tls.yml"):
        assert overlay in result.stdout
    assert "generate-local-tls 127.0.0.1" in result.stdout


def test_a_certificate_is_kept_while_it_is_valid(tmp_path):
    generate = str(ROOT / "scripts" / "generate-local-tls")
    subprocess.run([generate, "192.0.2.10", str(tmp_path)], check=True, capture_output=True)
    first = (tmp_path / "local-ca.crt").read_bytes()
    again = subprocess.run([generate, "192.0.2.10", str(tmp_path)], check=True, capture_output=True, text=True)
    assert "keeping it" in again.stdout and (tmp_path / "local-ca.crt").read_bytes() == first
    subprocess.run([generate, "192.0.2.10,other.lan", str(tmp_path)], check=True, capture_output=True)
    assert (tmp_path / "local-ca.crt").read_bytes() != first, "a new name needs a new certificate"
