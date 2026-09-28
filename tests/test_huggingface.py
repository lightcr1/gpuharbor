from __future__ import annotations

import httpx
import pytest

from gpuharbor.huggingface import LookupError, find_context_length, lookup, summarise


def test_find_context_length_searches_nested_text_config():
    config = {
        "architectures": ["Qwen3VLMoe"],
        "text_config": {"hidden_size": 5120, "max_position_embeddings": 262144},
        "vision_config": {"depth": 27},
    }
    assert find_context_length(config) == 262144


def test_find_context_length_returns_none_without_match():
    assert find_context_length({"model_type": "gguf"}) is None
    assert find_context_length({"max_position_embeddings": 512}) is None
    assert find_context_length("not a dict") is None


def test_summarise_prefers_vllm_for_safetensors():
    payload = {"id": "org/model", "cardData": {"license": "apache-2.0"}, "downloads": 10}
    files = [
        {"rfilename": "model-00001.safetensors", "size": 10_000_000_000},
        {"rfilename": "model-00002.safetensors", "size": 6_000_000_000},
    ]
    result = summarise(payload, files, 32768)
    assert result["suggested_runtime"] == "vllm"
    assert result["license"] == "apache-2.0"
    assert result["estimated_size_gb"] == 16.0
    assert result["suggested_volume_gb"] is not None
    # 16 GB of weights need about 21 GB, so a 24 GB card is enough.
    assert result["suggested_gpus"][0] == "NVIDIA RTX A5000"


def test_summarise_suggests_48gb_card_for_a_27b_fp8_model():
    result = summarise({"id": "org/model"}, [{"rfilename": "m.safetensors", "size": 31_000_000_000}], None)
    assert result["estimated_size_gb"] == 31.0
    assert result["suggested_gpus"][0] == "NVIDIA A40"


def test_summarise_picks_gguf_and_ignores_projector():
    payload = {"id": "org/model"}
    files = [
        {"rfilename": "model-Q6_K.gguf", "size": 20_000_000_000},
        {"rfilename": "mmproj-model-f16.gguf", "size": 1_000_000_000},
    ]
    result = summarise(payload, files, None)
    assert result["suggested_runtime"] == "llama-cpp"
    assert result["suggested_gguf"] == "model-Q6_K.gguf"
    assert result["gguf_files"] == ["model-Q6_K.gguf"]


def test_summarise_does_not_preselect_between_many_gguf_files():
    payload = {"id": "org/model"}
    files = [
        {"rfilename": "model-Q4.gguf"},
        {"rfilename": "model-Q8.gguf"},
    ]
    result = summarise(payload, files, None)
    assert result["suggested_gguf"] is None
    assert any("GGUF" in note for note in result["notes"])


def test_summarise_flags_gated_models():
    result = summarise({"id": "org/model", "gated": True}, [], None)
    assert result["gated"] is True
    assert any("Gated" in note for note in result["notes"])


@pytest.mark.asyncio
async def test_lookup_rejects_bad_repository():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(LookupError, match="owner/name"):
            await lookup(client, "../../etc/passwd")
        with pytest.raises(LookupError, match="owner/name"):
            await lookup(client, "just-a-name")


@pytest.mark.asyncio
async def test_lookup_reports_missing_repository():
    transport = httpx.MockTransport(lambda request: httpx.Response(404, json={"error": "not found"}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(LookupError, match="not found"):
            await lookup(client, "org/missing")


@pytest.mark.asyncio
async def test_lookup_reads_config_and_files():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/config.json"):
            return httpx.Response(200, json={"max_position_embeddings": 40960})
        return httpx.Response(
            200,
            json={
                "id": "org/model",
                "cardData": {"license": "mit"},
                "siblings": [{"rfilename": "model.safetensors", "size": 8_000_000_000}],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await lookup(client, "org/model")
    assert result["context_length"] == 40960
    assert result["suggested_runtime"] == "vllm"
    assert result["license"] == "mit"


@pytest.mark.asyncio
async def test_lookup_caps_a_huge_architectural_context():
    maxed = {"max_position_embeddings": 262144}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/config.json"):
            return httpx.Response(200, json=maxed)
        return httpx.Response(200, json={"id": "org/model", "siblings": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await lookup(client, "org/model")
    assert result["context_length"] == 65536


def test_suggest_endpoint_uses_hugging_face(app_client):
    from unittest.mock import AsyncMock

    client, _ = app_client
    csrf = client.post(
        "/api/login", json={"username": "admin", "password": "p" * 40}
    ).json()["csrf_token"]
    client.app.state.proxy = AsyncMock()

    async def fake_lookup(_client, repository, token=None):
        return {"model_id": repository, "suggested_runtime": "vllm"}

    import gpuharbor.main as main

    main.hf_lookup = fake_lookup
    try:
        response = client.post(
            "/api/model-suggest",
            json={"model_id": "org/model"},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 200
        assert response.json()["suggested_runtime"] == "vllm"
    finally:
        main.hf_lookup = lookup
