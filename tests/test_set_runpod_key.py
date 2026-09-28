from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "set-runpod-key"


def run(env_path: Path, key: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--env", str(env_path), "--key", key, "--no-restart"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


def make_env(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(
        (ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8"
    )
    return env


def test_valid_key_replaces_placeholder(tmp_path):
    env = make_env(tmp_path)
    result = run(env, "rpa_" + "a" * 30)
    assert result.returncode == 0
    values = dict(
        line.split("=", 1)
        for line in env.read_text(encoding="utf-8").splitlines()
        if "=" in line and not line.startswith("#")
    )
    assert values["RUNPOD_API_KEY"] == "rpa_" + "a" * 30
    assert env.stat().st_mode & 0o777 == 0o600


def test_rejects_key_without_prefix(tmp_path):
    env = make_env(tmp_path)
    result = run(env, "not-a-runpod-key")
    assert result.returncode == 1
    assert "rpa_" in result.stderr
    assert "replace-with-a-random-secret" in env.read_text(encoding="utf-8")


def test_rejects_too_short_key(tmp_path):
    env = make_env(tmp_path)
    assert run(env, "rpa_short").returncode == 1
