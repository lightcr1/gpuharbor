"""PI integration: the model list endpoint and scripts/connect-pi against a fake controller."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "connect-pi"
TOKEN = "m" * 40


def test_pi_models_endpoint_needs_the_inference_token(app_client):
    app_client, _ = app_client
    assert app_client.get("/api/pi-models").status_code == 401
    assert app_client.get("/api/pi-models", headers={"Authorization": "Bearer " + "c" * 40}).status_code == 401
    body = app_client.get("/api/pi-models", headers={"Authorization": f"Bearer {TOKEN}"}).json()
    ids = [model["id"] for model in body["models"]]
    assert ids[:2] == ["default", "coding-max"] and len(ids) == len(set(ids))
    first = body["models"][0]
    assert first["contextWindow"] == 65536 and first["maxTokens"] == 8192
    assert "default" not in body["without_tool_calls"] and set(body["without_tool_calls"]) <= set(ids)
    assert TOKEN not in json.dumps(body) and "c" * 40 not in json.dumps(body)


class FakeController(BaseHTTPRequestHandler):
    payload = {"models": [{"id": "default", "name": "Qwen", "reasoning": False, "input": ["text"], "contextWindow": 65536, "maxTokens": 8192}], "without_tool_calls": ["default"]}

    def do_GET(self):  # noqa: N802
        if self.path != "/api/pi-models" or self.headers.get("Authorization") != f"Bearer {TOKEN}":
            self.send_response(401)
            self.end_headers()
            return
        data = json.dumps(self.payload).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture()
def controller():
    server = HTTPServer(("127.0.0.1", 0), FakeController)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture()
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text(f"MODEL_ACCESS_TOKEN={TOKEN}\nCONTROL_TOKEN={'c' * 40}\n", encoding="utf-8")
    return path


def run(*args, check=True):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=check)


def test_writes_provider_and_keeps_everything_else(tmp_path, controller, env_file):
    models = tmp_path / "models.json"
    other = {"providers": {"openai-codex": {"modelOverrides": {"x": {"contextWindow": 1}}}}}
    models.write_text(json.dumps(other), encoding="utf-8")

    result = run("--env", str(env_file), "--url", controller, "--models-file", str(models))

    data = json.loads(models.read_text(encoding="utf-8"))
    assert data["providers"]["openai-codex"] == other["providers"]["openai-codex"]
    provider = data["providers"]["gpuharbor"]
    assert provider["baseUrl"] == f"{controller}/v1" and provider["api"] == "openai-completions"
    assert provider["models"][0]["id"] == "default"
    assert TOKEN not in models.read_text(encoding="utf-8"), "the token must not be copied into models.json"
    assert provider["apiKey"].startswith("!") and "--print-token" in provider["apiKey"]
    assert (models.stat().st_mode & 0o777) == 0o600
    assert json.loads((tmp_path / "models.json.bak").read_text(encoding="utf-8")) == other
    assert "does not parse tool calls" in result.stdout


def test_token_command_prints_the_token(env_file):
    assert run("--env", str(env_file), "--print-token").stdout == TOKEN


def test_remove_only_removes_our_provider(tmp_path, controller, env_file):
    models = tmp_path / "models.json"
    models.write_text(json.dumps({"providers": {"mine": {"baseUrl": "http://x"}}, "other": 1}), encoding="utf-8")
    run("--env", str(env_file), "--url", controller, "--models-file", str(models))
    run("--env", str(env_file), "--models-file", str(models), "--remove")
    assert json.loads(models.read_text(encoding="utf-8")) == {"providers": {"mine": {"baseUrl": "http://x"}}, "other": 1}


def test_dry_run_changes_nothing(tmp_path, controller, env_file):
    models = tmp_path / "models.json"
    result = run("--env", str(env_file), "--url", controller, "--models-file", str(models), "--dry-run")
    assert "gpuharbor" in result.stdout and not models.exists()


def test_broken_models_file_is_never_overwritten(tmp_path, controller, env_file):
    models = tmp_path / "models.json"
    models.write_text("{not json", encoding="utf-8")
    result = run("--env", str(env_file), "--url", controller, "--models-file", str(models), check=False)
    assert result.returncode == 1 and models.read_text(encoding="utf-8") == "{not json"


def test_refuses_plain_http_to_a_remote_host(tmp_path, env_file):
    result = run("--env", str(env_file), "--url", "http://192.0.2.10:8080", "--models-file", str(tmp_path / "m.json"), check=False)
    assert result.returncode == 1 and "plain HTTP" in result.stderr


def test_refuses_placeholder_token(tmp_path, controller):
    env = tmp_path / ".env"
    env.write_text("MODEL_ACCESS_TOKEN=replace-with-a-model-only-random-secret\n", encoding="utf-8")
    result = run("--env", str(env), "--url", controller, "--models-file", str(tmp_path / "m.json"), check=False)
    assert result.returncode == 1 and not (tmp_path / "m.json").exists()


def test_wrong_token_gives_a_hint(tmp_path, controller):
    env = tmp_path / ".env"
    env.write_text("MODEL_ACCESS_TOKEN=" + "x" * 40 + "\n", encoding="utf-8")
    result = run("--env", str(env), "--url", controller, "--models-file", str(tmp_path / "m.json"), check=False)
    assert result.returncode == 1 and "401" in result.stderr
