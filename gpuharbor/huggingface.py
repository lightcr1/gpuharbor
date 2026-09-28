from __future__ import annotations

"""Read-only Hugging Face lookups used to pre-fill the model editor.

Only the fixed huggingface.co host is contacted, and the repository id must match
`owner/repository` before it is put into a URL.
"""
import re
from typing import Any

import httpx

_MODEL_REPOSITORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")
_API = "https://huggingface.co/api/models"
_RAW = "https://huggingface.co"

# GPU choice by required VRAM (weights plus runtime and KV cache), cheapest first.
_VRAM_STEPS: tuple[tuple[int, list[str]], ...] = (
    (24, ["NVIDIA RTX A5000", "NVIDIA RTX 4090"]),
    (48, ["NVIDIA A40", "NVIDIA L40S"]),
    (80, ["NVIDIA A100 80GB PCIe", "NVIDIA H100 80GB HBM3"]),
    (96, ["NVIDIA RTX PRO 6000 Blackwell Server Edition"]),
)
_MAX_GPUS = ["NVIDIA H200", "NVIDIA B200", "NVIDIA B300 SXM6 AC"]


class LookupError(RuntimeError):
    pass


def _gigabytes(value: int | float | None) -> float | None:
    if not value:
        return None
    return round(float(value) / 1_000_000_000, 1)


def _suggest_gpus(size_gb: float | None) -> list[str]:
    if size_gb is None:
        return []
    # Weights plus roughly a third for the runtime and KV cache.
    needed = size_gb * 1.3
    for vram, gpus in _VRAM_STEPS:
        if needed <= vram:
            return gpus
    return list(_MAX_GPUS)


def _suggest_volume(size_gb: float | None) -> int | None:
    if size_gb is None:
        return None
    return max(20, int(size_gb * 1.5) + 10)


_CONTEXT_KEYS = (
    "max_position_embeddings",
    "n_positions",
    "seq_length",
    "max_sequence_length",
    "model_max_length",
)


def find_context_length(data: Any, depth: int = 0) -> int | None:
    """Find a context length in a config, including nested text_config blocks."""
    if depth > 4 or not isinstance(data, dict):
        return None
    for key in _CONTEXT_KEYS:
        value = data.get(key)
        if isinstance(value, int) and value >= 1024:
            return min(value, 262144)
    for value in data.values():
        if isinstance(value, dict):
            found = find_context_length(value, depth + 1)
            if found:
                return found
    return None


def summarise(payload: dict[str, Any], files: list[dict[str, Any]], context: int | None) -> dict[str, Any]:
    names = [str(entry.get("rfilename") or "") for entry in files]
    sizes = {str(entry.get("rfilename")): entry.get("size") for entry in files}

    gguf = [name for name in names if name.lower().endswith(".gguf")]
    # Ignore multimodal projector files when guessing the main one.
    main_gguf = [name for name in gguf if "mmproj" not in name.lower()]
    safetensors = [name for name in names if name.endswith(".safetensors")]

    if safetensors:
        runtime = "vllm"
        size_gb = _gigabytes(sum(sizes.get(name) or 0 for name in safetensors))
    elif main_gguf:
        runtime = "llama-cpp"
        chosen = main_gguf[0]
        size_gb = _gigabytes(sizes.get(chosen))
    else:
        runtime = None
        size_gb = None

    card = payload.get("cardData") or {}
    license_name = card.get("license")
    if isinstance(license_name, list):
        license_name = ", ".join(str(item) for item in license_name)

    notes: list[str] = []
    if len(main_gguf) > 1:
        notes.append(f"{len(main_gguf)} GGUF files found; pick the quantisation you want.")
    if payload.get("gated"):
        notes.append("Gated model: needs a Hugging Face token and an access grant.")
    if size_gb:
        notes.append(f"Weights are about {size_gb} GB; budget roughly 1.3x VRAM.")

    return {
        "model_id": payload.get("id"),
        "gated": bool(payload.get("gated")),
        "private": bool(payload.get("private")),
        "license": license_name or "unknown",
        "downloads": payload.get("downloads"),
        "suggested_runtime": runtime,
        "gguf_files": main_gguf[:12],
        "suggested_gguf": main_gguf[0] if runtime == "llama-cpp" and len(main_gguf) == 1 else None,
        "context_length": context,
        "estimated_size_gb": size_gb,
        "suggested_volume_gb": _suggest_volume(size_gb),
        "suggested_gpus": _suggest_gpus(size_gb),
        "notes": notes,
    }


async def lookup(client: httpx.AsyncClient, repository: str, token: str | None = None) -> dict[str, Any]:
    repository = repository.strip()
    if not _MODEL_REPOSITORY.fullmatch(repository):
        raise LookupError("Repository must look like owner/name")

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = await client.get(
            f"{_API}/{repository}",
            params={"blobs": "true"},
            headers=headers,
            timeout=20,
            follow_redirects=True,
        )
    except httpx.HTTPError as error:
        raise LookupError(f"Hugging Face not reachable: {error}") from error

    if response.status_code == 404:
        raise LookupError("Repository not found on Hugging Face")
    if response.status_code in {401, 403}:
        raise LookupError("Repository is private or gated and the token was not accepted")
    if response.status_code >= 400:
        raise LookupError(f"Hugging Face returned HTTP {response.status_code}")

    payload = response.json()
    files = payload.get("siblings") or []

    context = None
    try:
        config = await client.get(
            f"{_RAW}/{repository}/raw/main/config.json",
            headers=headers,
            timeout=20,
            follow_redirects=True,
        )
        if config.status_code == 200:
            context = find_context_length(config.json())
    except (httpx.HTTPError, ValueError):
        context = None

    # The architectural maximum is rarely a good default: it costs a lot of VRAM.
    if context:
        context = min(context, 65536)

    result = summarise(payload, files, context)
    result["model_id"] = payload.get("id") or repository
    return result
