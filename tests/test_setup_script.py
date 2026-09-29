from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "setup"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )


def test_setup_dry_run_combines_all_overlays():
    result = run(
        "--dry-run", "--bind", "192.0.2.10",
        "--https", "192.0.2.10", "--https-port", "9443",
        "--webui", "--openhands", "--start",
    )
    assert "compose.tls.yml" in result.stdout
    assert "compose.openwebui.yml" in result.stdout
    assert "compose.openhands.yml" in result.stdout
    assert "up -d --build" in result.stdout
    assert "--https-host 192.0.2.10" in result.stdout


def test_setup_dry_run_local_only_has_no_tls():
    result = run("--dry-run", "--bind", "127.0.0.1")
    assert "compose.tls.yml" not in result.stdout
    assert "compose.openwebui.yml" not in result.stdout
    assert "up -d" not in result.stdout


def test_setup_rejects_invalid_bind_address():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run", "--bind", "not a host"],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert result.returncode == 1
    assert "Ungültige Bind-Adresse" in result.stderr


def test_setup_yes_uses_defaults():
    result = run("--yes", "--dry-run")
    assert "Bind-Adresse : 127.0.0.1" in result.stdout
    assert "Open WebUI   : nein" in result.stdout
