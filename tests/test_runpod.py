import json
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from gpuharbor.config import Settings
from gpuharbor.registry import ModelDefinition, RuntimeDefinition
from gpuharbor.runpod import (
    LaunchOptions,
    RunpodClient,
    RunpodError,
    resolve_launch,
    runtime_env,
)


def settings(**overrides):
    values = {
        "runpod_api_key": SecretStr("r" * 40),
        "control_token": SecretStr("c" * 40),
        "model_access_token": SecretStr("m" * 40),
        "runtime_gateway_token": SecretStr("g" * 40),
        "gpuharbor_admin_password": SecretStr("p" * 40),
        "gpuharbor_session_secret": SecretStr("s" * 40),
        "runtime_image_vllm": "ghcr.io/example/vllm@sha256:" + "a" * 64,
        "state_path": Path("state.json"),
    }
    values.update(overrides)
    return Settings(**values)


def model():
    return ModelDefinition(
        name="Example", model_id="org/model", runtime="vllm",
        served_names=["chat", "code"], gpu_type_ids=["NVIDIA A40", "NVIDIA RTX A6000"],
        context_length=32768, max_sequences=2, volume_gb=64,
    )


def runtime():
    return RuntimeDefinition(label="vLLM", image_env="RUNTIME_IMAGE_VLLM", backend="vllm")


def test_launch_overrides_are_resolved():
    launch = resolve_launch(
        LaunchOptions(model_id="example", context_length=65536, gpu_type_id="NVIDIA A40", volume_gb=80),
        model(), runtime(), ["EU-SE-1", "CA-MTL-1"],
    )
    assert launch.context_length == 65536
    assert launch.gpu_type_ids == ["NVIDIA A40"]
    assert launch.volume_gb == 80


def test_disallowed_gpu_is_rejected():
    with pytest.raises(ValueError, match="not allowed"):
        resolve_launch(
            LaunchOptions(model_id="example", gpu_type_id="NVIDIA H100"),
            model(), runtime(), ["EU-SE-1"],
        )


def test_payload_contains_ui_overrides_and_no_ssh():
    launch = resolve_launch(LaunchOptions(model_id="example", context_length=65536), model(), runtime(), ["EU-SE-1"])
    client = RunpodClient(settings())
    payload = client.create_candidates(launch)[0]["payload"]
    assert payload["env"]["MAX_MODEL_LEN"] == "65536"
    assert payload["mounts"]["persistent"]["size"] == 64
    assert payload["startSsh"] is False
    assert payload["image"].endswith("a" * 64)


def test_runtime_environment_uses_separate_gateway_secret():
    launch = resolve_launch(LaunchOptions(model_id="example"), model(), runtime(), ["EU-SE-1"])
    env = runtime_env(launch, "gateway-only", None)
    assert env["GATEWAY_API_KEY"] == "gateway-only"
    assert env["SERVED_MODEL_NAMES"] == "chat,code"


def test_vllm_options_are_generated_from_validated_fields():
    profile = model().model_copy(update={
        "trust_remote_code": True,
        "reasoning_parser": "qwen3",
        "tool_call_parser": "qwen3_coder",
        "enable_auto_tool_choice": True,
    })
    launch = resolve_launch(LaunchOptions(model_id="example"), profile, runtime(), ["EU-SE-1"])
    env = runtime_env(launch, "gateway-only", None)
    assert "--trust-remote-code" in env["VLLM_EXTRA_ARGS_JSON"]
    assert "qwen3_coder" in env["VLLM_EXTRA_ARGS_JSON"]


def test_billable_configuration_accepts_distinct_secrets_and_digest():
    assert settings().live_errors("vllm") == []


def response(request, status, payload=None):
    if payload is None:
        return httpx.Response(status, request=request)
    return httpx.Response(status, request=request, json=payload)


@pytest.mark.asyncio
async def test_create_uses_next_candidate_after_capacity_rejection():
    posts = []

    def handler(request):
        if request.method == "GET":
            return response(request, 200, {"pods": []})
        payload = json.loads(request.content)
        posts.append(payload)
        if len(posts) == 1:
            return response(request, 400, {"detail": "no capacity"})
        return response(request, 201, {"id": "pod-1", "status": "PROVISIONING"})

    client = RunpodClient(settings(), httpx.MockTransport(handler))
    launch = resolve_launch(LaunchOptions(model_id="example"), model(), runtime(), ["EU-SE-1", "CA-MTL-1"])
    try:
        pod = await client.create_pod(launch)
    finally:
        await client.close()
    assert pod["id"] == "pod-1"
    assert pod["_gpuharbor_datacenter_id"] == "CA-MTL-1"
    assert len(posts) == 2


@pytest.mark.asyncio
async def test_create_refuses_duplicate_managed_pod():
    post_count = 0

    def handler(request):
        nonlocal post_count
        if request.method == "POST":
            post_count += 1
        return response(request, 200, {"pods": [{"id": "existing", "name": "gpuharbor-model", "status": "EXITED"}]})

    client = RunpodClient(settings(), httpx.MockTransport(handler))
    launch = resolve_launch(LaunchOptions(model_id="example"), model(), runtime(), ["EU-SE-1"])
    try:
        with pytest.raises(RunpodError, match="already exists"):
            await client.create_pod(launch)
    finally:
        await client.close()
    assert post_count == 0


@pytest.mark.asyncio
async def test_create_aborts_on_payment_error():
    post_count = 0

    def handler(request):
        nonlocal post_count
        if request.method == "GET":
            return response(request, 200, {"pods": []})
        post_count += 1
        return response(request, 402, {"detail": "insufficient balance"})

    client = RunpodClient(settings(), httpx.MockTransport(handler))
    launch = resolve_launch(LaunchOptions(model_id="example"), model(), runtime(), ["EU-SE-1", "CA-MTL-1"])
    try:
        with pytest.raises(RunpodError, match="HTTP 402"):
            await client.create_pod(launch)
    finally:
        await client.close()
    assert post_count == 1


@pytest.mark.asyncio
async def test_lifecycle_uses_runpod_v2_endpoints():
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path, json.loads(request.content) if request.content else None))
        return response(request, 200, {})

    client = RunpodClient(settings(), httpx.MockTransport(handler))
    try:
        await client.start_pod("pod-1")
        await client.stop_pod("pod-1")
        await client.delete_pod("pod-1")
    finally:
        await client.close()
    assert calls == [
        ("POST", "/v2/pods/pod-1/action", {"action": "start"}),
        ("POST", "/v2/pods/pod-1/action", {"action": "stop"}),
        ("DELETE", "/v2/pods/pod-1", None),
    ]


@pytest.mark.asyncio
async def test_lost_create_response_is_not_automatically_retried():
    post_count = 0

    def handler(request):
        nonlocal post_count
        if request.method == "GET":
            return response(request, 200, {"pods": []})
        post_count += 1
        raise httpx.ReadTimeout("response lost", request=request)

    client = RunpodClient(settings(), httpx.MockTransport(handler))
    launch = resolve_launch(LaunchOptions(model_id="example"), model(), runtime(), ["EU-SE-1", "CA-MTL-1"])
    try:
        with pytest.raises(RunpodError, match="avoid duplicate"):
            await client.create_pod(launch)
    finally:
        await client.close()
    assert post_count == 1
