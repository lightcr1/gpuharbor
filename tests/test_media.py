"""Image and video models: separate pod slot, routing, and the media server."""
from __future__ import annotations

import asyncio
import importlib.util
import time
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from gpuharbor.integrations import desired_profiles, pi_models
from gpuharbor.registry import ModelDefinition, Registry
from gpuharbor.runpod import LaunchOptions, resolve_launch, runtime_env

ROOT = Path(__file__).parents[1]


def login(client) -> str:
    response = client.post("/api/login", json={"username": "admin", "password": "p" * 40})
    assert response.status_code == 200
    return response.json()["csrf_token"]


def media_profile(**overrides) -> dict:
    values = {
        "name": "Video",
        "model_id": "owner/video",
        "runtime": "diffusers",
        "served_names": ["video"],
        "capabilities": ["video"],
        "media_pipeline": "wan22-ti2v",
        "gpu_type_ids": ["NVIDIA A40"],
    }
    values.update(overrides)
    return values


def test_shipped_media_profiles_are_valid_and_use_the_media_slot(tmp_path):
    registry = Registry(ROOT / "registry/models.json", ROOT / "registry/runtimes.json", tmp_path / "user.json")
    models = registry.models()
    assert models["wan22-ti2v-5b-video"].slot == "media"
    assert models["qwen-image-20b"].slot == "media"
    assert models["hauhau-qwen38-27b-aggressive-q6"].slot == "chat"


@pytest.mark.parametrize(
    "overrides",
    [
        {"media_pipeline": None},
        {"runtime": "vllm"},
        {"capabilities": ["video", "chat"]},
        {"gguf_file": "x.gguf"},
    ],
)
def test_media_profile_rules(overrides):
    with pytest.raises(ValidationError):
        ModelDefinition(**media_profile(**overrides))


def test_chat_profile_cannot_use_the_diffusers_runtime():
    with pytest.raises(ValidationError):
        ModelDefinition(**media_profile(capabilities=["chat"], media_pipeline=None))


def test_media_models_stay_out_of_openhands_and_pi(tmp_path):
    models = Registry(ROOT / "registry/models.json", ROOT / "registry/runtimes.json", tmp_path / "user.json").models()
    media_ids = {key for key, model in models.items() if model.slot == "media"}
    assert media_ids
    assert not media_ids & {name.removeprefix("gpuharbor-") for name in desired_profiles(models, "t" * 32)}
    served = {entry["id"] for entry in pi_models(models)}
    assert "image" not in served and "video" not in served


def test_media_launch_environment_and_pod_name(app_client):
    _, main = app_client
    model = ModelDefinition(**media_profile())
    runtime = main.registry.runtimes()["diffusers"]
    launch = resolve_launch(LaunchOptions(model_id="v"), model, runtime, ["EU-SE-1"])
    env = runtime_env(launch, "g" * 40, None)
    assert env["RUNTIME_BACKEND"] == "diffusers"
    assert env["MEDIA_PIPELINE"] == "wan22-ti2v"
    assert main.settings.pod_name("media") == "gpuharbor-media"
    assert main.settings.pod_name("chat") == "gpuharbor-model"


def test_images_and_videos_go_to_the_media_pod(app_client):
    client, main = app_client
    main.stores["chat"].write(main.ControllerState(pod_id="chatpod", model_id="qwen38-27b-fp8"))
    main.stores["media"].write(main.ControllerState(pod_id="mediapod", model_id="qwen-image-20b"))
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, stream=httpx.ByteStream(b"{}"), headers={"content-type": "application/json"})

    client.app.state.proxy = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    headers = {"Authorization": "Bearer " + "m" * 40}
    client.post("/v1/images/generations", json={"prompt": "x"}, headers=headers)
    client.get("/v1/videos/video_1", headers=headers)
    client.get("/v1/models", headers=headers)
    assert seen == [
        "https://mediapod-8000.proxy.runpod.net/v1/images/generations",
        "https://mediapod-8000.proxy.runpod.net/v1/videos/video_1",
        "https://chatpod-8000.proxy.runpod.net/v1/models",
    ]


def test_media_request_without_a_media_pod_explains_it(app_client):
    client, main = app_client
    main.stores["chat"].write(main.ControllerState(pod_id="chatpod", model_id="qwen38-27b-fp8"))
    response = client.post(
        "/v1/images/generations", json={"prompt": "x"}, headers={"Authorization": "Bearer " + "m" * 40}
    )
    assert response.status_code == 503
    assert "image or video" in response.json()["error"]["message"]


def test_stop_and_status_act_on_the_requested_slot(app_client):
    client, main = app_client
    csrf = login(client)
    main.stores["chat"].write(main.ControllerState(pod_id="chatpod", model_id="qwen38-27b-fp8"))
    main.stores["media"].write(main.ControllerState(pod_id="mediapod", model_id="qwen-image-20b"))
    runpod = client.app.state.runpod
    runpod.stop_pod = AsyncMock()
    runpod.wait_for_status = AsyncMock(return_value={})
    runpod.get_pod = AsyncMock(return_value={"id": "mediapod", "status": "RUNNING"})
    assert client.post("/api/pod/stop?slot=media", headers={"X-CSRF-Token": csrf}).status_code == 200
    runpod.stop_pod.assert_awaited_once_with("mediapod")
    status = client.get("/api/status?slot=media").json()
    assert status["model_id"] == "qwen-image-20b"
    assert client.get("/api/status?slot=nope").status_code == 422


def test_connection_reports_the_media_model(app_client):
    client, main = app_client
    login(client)
    assert client.get("/api/connection").json()["media"]["running"] is False
    main.stores["media"].write(main.ControllerState(pod_id="mediapod", model_id="qwen-image-20b"))
    media = client.get("/api/connection").json()["media"]
    assert media["running"] is True
    assert media["served_names"][0] == "qwen-image"


# --- media server -----------------------------------------------------------


class FakeImage:
    def save(self, buffer, format):  # noqa: A002 - PIL signature
        buffer.write(b"PNGDATA")


class FakePipeline:
    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        callback = kwargs.get("callback_on_step_end")
        if callback:
            callback(self, 0, 0, {})
        time.sleep(0.05)
        return type("Out", (), {"images": [FakeImage()], "frames": [["frame"]]})()


def load_media_server(monkeypatch, tmp_path, pipeline_name="qwen-image", served="qwen-image,image"):
    monkeypatch.setenv("MEDIA_PIPELINE", pipeline_name)
    monkeypatch.setenv("SERVED_MODEL_NAMES", served)
    monkeypatch.setenv("MODEL_ID", "owner/model")
    monkeypatch.setenv("MEDIA_OUTPUT_DIR", str(tmp_path / "out"))
    spec = importlib.util.spec_from_file_location("gpuharbor_media_server", ROOT / "runtime/media_server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pipeline = FakePipeline()
    monkeypatch.setattr(module, "load_pipeline", lambda name, repo, token: pipeline)
    monkeypatch.setattr(module, "make_generator", lambda seed: seed)
    monkeypatch.setattr(
        module, "encode_video", lambda frames, path: path.write_bytes(b"MP4DATA")
    )
    return module, pipeline


def ready_client(module):
    from fastapi.testclient import TestClient

    client = TestClient(module.app)
    client.__enter__()
    for _ in range(100):
        if client.get("/health").status_code == 200:
            return client
        time.sleep(0.02)
    raise AssertionError("media server never became ready")


def test_health_is_503_until_the_pipeline_is_loaded(monkeypatch, tmp_path):
    module, _ = load_media_server(monkeypatch, tmp_path)
    assert module.media.pipeline is None
    from fastapi.testclient import TestClient

    # No lifespan started, so nothing has loaded.
    assert TestClient(module.app).get("/health").status_code == 503


def test_image_generation_returns_base64_and_checks_the_model(monkeypatch, tmp_path):
    module, pipeline = load_media_server(monkeypatch, tmp_path)
    client = ready_client(module)
    try:
        response = client.post("/v1/images/generations", json={"prompt": "a harbor", "model": "image", "size": "1024x1024"})
        assert response.status_code == 200
        assert response.json()["data"][0]["b64_json"] == "UE5HREFUQQ=="
        assert pipeline.calls[0]["width"] == 1024
        assert client.post("/v1/images/generations", json={"prompt": "x", "model": "other"}).status_code == 404
        assert client.post("/v1/images/generations", json={"prompt": "x", "size": "1000x1000"}).status_code == 400
        assert client.post("/v1/images/generations", json={"prompt": "x", "size": "4096x4096"}).status_code == 400
        assert client.post("/v1/videos", json={"prompt": "x"}).status_code == 400  # this pod serves images
    finally:
        client.__exit__(None, None, None)


def test_video_job_lifecycle(monkeypatch, tmp_path):
    module, pipeline = load_media_server(monkeypatch, tmp_path, "wan22-ti2v", "wan-video,video")
    client = ready_client(module)
    try:
        created = client.post("/v1/videos", json={"prompt": "waves", "seconds": 2, "model": "video"})
        assert created.status_code == 202
        job = created.json()
        assert job["object"] == "video" and job["size"] == "1280x704"
        assert "_task" not in job
        for _ in range(100):
            state = client.get(f"/v1/videos/{job['id']}").json()
            if state["status"] == "completed":
                break
            time.sleep(0.02)
        assert state["status"] == "completed" and state["progress"] == 100
        assert pipeline.calls[0]["num_frames"] == 2 * 24 + 1
        content = client.get(f"/v1/videos/{job['id']}/content")
        assert content.status_code == 200 and content.content == b"MP4DATA"
        assert client.get("/v1/videos/missing").status_code == 404
        assert client.post("/v1/videos", json={"prompt": "x", "seconds": 60}).status_code == 400
        assert client.post("/v1/videos", json={"prompt": "x", "size": "1280x704x1"}).status_code == 400
    finally:
        client.__exit__(None, None, None)


def test_gateway_starts_the_media_server_for_the_diffusers_backend(monkeypatch):
    monkeypatch.setenv("GATEWAY_API_KEY", "g" * 40)
    monkeypatch.setenv("RUNTIME_BACKEND", "diffusers")
    spec = importlib.util.spec_from_file_location("gpuharbor_gateway_media", ROOT / "runtime/gateway.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    command = asyncio.run(module.runtime_command())
    assert command == ["python3", "/opt/gpuharbor/media_server.py"]
