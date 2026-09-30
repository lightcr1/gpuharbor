"""PI integration: the running-model endpoint and scripts/connect-pi against a fake controller."""
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


def test_running_model_endpoint(app_client):
    client, main = app_client
    headers = {"Authorization": f"Bearer {TOKEN}"}
    assert client.get("/api/running-model").status_code == 401
    assert client.get("/api/running-model", headers={"Authorization": "Bearer " + "c" * 40}).status_code == 401
    assert client.get("/api/running-model", headers=headers).json() == {"running": False, "pi_models": []}

    main.store.write(main.ControllerState(pod_id="pod-1", model_id="qwen38-27b-fp8", gpu_type_id="NVIDIA A40"))
    info = client.get("/api/running-model", headers=headers).json()
    assert info["running"] and info["served_names"][0] == "default" and info["gpu"] == "NVIDIA A40"
    assert info["tool_calls"] is True
    [entry] = info["pi_models"]
    assert entry["id"] == "default" and entry["name"] == "Qwen3.8 27B FP8"
    assert entry["contextWindow"] == 65536 and entry["maxTokens"] == 8192
    assert entry["compat"]["maxTokensField"] == "max_tokens"
    text = json.dumps(info)
    assert "pod-1" not in text and TOKEN not in text and "c" * 40 not in text


def test_only_the_running_model_is_listed(app_client):
    client, main = app_client
    headers = {"Authorization": f"Bearer {TOKEN}"}
    main.store.write(main.ControllerState(pod_id="pod-1", model_id="qwen3-coder-30b-fp8"))
    ids = [m["id"] for m in client.get("/api/running-model", headers=headers).json()["pi_models"]]
    assert ids == ["coding-max"]


class FakeController(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path != "/api/running-model" or self.headers.get("Authorization") != f"Bearer {TOKEN}":
            self.send_response(401)
            self.end_headers()
            return
        data = json.dumps({"running": False, "pi_models": []}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def serve(handler):
    server = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture()
def controller():
    server = serve(FakeController)
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture()
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text(f"MODEL_ACCESS_TOKEN={TOKEN}\nCONTROL_TOKEN={'c' * 40}\n", encoding="utf-8")
    return path


def run(*args, check=True):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=check)


def args_for(tmp_path, env_file, controller):
    return ("--env", str(env_file), "--url", controller, "--agent-dir", str(tmp_path / "agent"))


def test_installs_extension_and_settings(tmp_path, controller, env_file):
    agent = tmp_path / "agent"
    run(*args_for(tmp_path, env_file, controller))

    settings = agent / "gpuharbor.json"
    assert json.loads(settings.read_text(encoding="utf-8")) == {"url": controller, "apiKey": TOKEN}
    assert (settings.stat().st_mode & 0o777) == 0o600
    extension = (agent / "extensions" / "gpuharbor.ts").read_text(encoding="utf-8")
    assert "registerProvider" in extension and "/modelinfo" not in extension.split("\n", 1)[0]
    assert not (agent / "models.json").exists(), "models.json is not touched when there is no old entry"


def test_token_from_env_keeps_the_token_out_of_the_file(tmp_path, controller, env_file):
    run(*args_for(tmp_path, env_file, controller), "--token-from-env")
    text = (tmp_path / "agent" / "gpuharbor.json").read_text(encoding="utf-8")
    assert TOKEN not in text
    api_key = json.loads(text)["apiKey"]
    assert api_key.startswith("!") and "--print-token" in api_key
    assert subprocess.run(api_key[1:], shell=True, capture_output=True, text=True).stdout == TOKEN


def test_old_models_json_entry_is_moved_out_and_others_are_kept(tmp_path, controller, env_file):
    agent = tmp_path / "agent"
    agent.mkdir()
    other = {"providers": {"openai-codex": {"modelOverrides": {"x": {"contextWindow": 1}}}}}
    (agent / "models.json").write_text(json.dumps({"providers": {**other["providers"], "gpuharbor": {"baseUrl": "x"}}}), encoding="utf-8")

    run(*args_for(tmp_path, env_file, controller))

    assert json.loads((agent / "models.json").read_text(encoding="utf-8")) == other
    assert "gpuharbor" in (agent / "models.json.bak").read_text(encoding="utf-8")


def test_remove_takes_everything_of_ours_out(tmp_path, controller, env_file):
    agent = tmp_path / "agent"
    run(*args_for(tmp_path, env_file, controller))
    run("--env", str(env_file), "--agent-dir", str(agent), "--remove")
    assert not (agent / "gpuharbor.json").exists()
    assert not (agent / "extensions" / "gpuharbor.ts").exists()


def test_foreign_extension_with_the_same_name_is_never_touched(tmp_path, controller, env_file):
    ext = tmp_path / "agent" / "extensions" / "gpuharbor.ts"
    ext.parent.mkdir(parents=True)
    ext.write_text("// my own\n", encoding="utf-8")
    result = run(*args_for(tmp_path, env_file, controller), check=False)
    assert result.returncode == 1 and ext.read_text(encoding="utf-8") == "// my own\n"
    assert not (tmp_path / "agent" / "gpuharbor.json").exists()
    run("--env", str(env_file), "--agent-dir", str(tmp_path / "agent"), "--remove")
    assert ext.read_text(encoding="utf-8") == "// my own\n"


def test_dry_run_changes_nothing_and_hides_the_token(tmp_path, controller, env_file):
    result = run(*args_for(tmp_path, env_file, controller), "--dry-run")
    assert TOKEN not in result.stdout and "<token>" in result.stdout
    assert not (tmp_path / "agent").exists()


def test_refuses_plain_http_to_a_remote_host(tmp_path, env_file):
    result = run("--env", str(env_file), "--url", "http://192.0.2.10:8080", "--agent-dir", str(tmp_path / "a"), check=False)
    assert result.returncode == 1 and "plain HTTP" in result.stderr


def test_refuses_placeholder_token(tmp_path, controller):
    env = tmp_path / ".env"
    env.write_text("MODEL_ACCESS_TOKEN=replace-with-a-model-only-random-secret\n", encoding="utf-8")
    result = run("--env", str(env), "--url", controller, "--agent-dir", str(tmp_path / "a"), check=False)
    assert result.returncode == 1 and not (tmp_path / "a").exists()


def test_wrong_token_gives_a_hint(tmp_path, controller):
    env = tmp_path / ".env"
    env.write_text("MODEL_ACCESS_TOKEN=" + "x" * 40 + "\n", encoding="utf-8")
    result = run("--env", str(env), "--url", controller, "--agent-dir", str(tmp_path / "a"), check=False)
    assert result.returncode == 1 and "401" in result.stderr


def test_old_controller_gets_an_update_hint(tmp_path, env_file):
    class Old(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(404)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = serve(Old)
    try:
        result = run("--env", str(env_file), "--url", f"http://127.0.0.1:{server.server_port}", "--agent-dir", str(tmp_path / "a"), check=False)
    finally:
        server.shutdown()
    assert result.returncode == 1 and "--build controller" in result.stderr
