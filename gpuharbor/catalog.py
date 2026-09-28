from __future__ import annotations

"""Static helper catalogs for the dashboard.

RunPod's live catalog is preferred whenever the API is reachable. These lists
are fallbacks for display and for offline setup, not a source of truth.
"""
from typing import Any

# Region name used by RunPod -> label shown in the dashboard.
REGION_LABELS: dict[str, str] = {
    "EUROPE": "Europa",
    "NORTH_AMERICA": "Nordamerika",
    "ASIA": "Asien",
    "ASIA_PACIFIC": "Asien/Pazifik",
    "OCEANIA": "Ozeanien",
    "SOUTH_AMERICA": "Südamerika",
    "AFRICA": "Afrika",
}

# Fallback heuristic when the datacenter catalog is unavailable.
_PREFIX_REGION: tuple[tuple[str, str], ...] = (
    ("EUR-", "EUROPE"),
    ("EU-", "EUROPE"),
    ("US-", "NORTH_AMERICA"),
    ("CA-", "NORTH_AMERICA"),
    ("AP-", "ASIA_PACIFIC"),
)


def region_for_datacenter(datacenter_id: str) -> str:
    upper = datacenter_id.upper()
    for prefix, region in _PREFIX_REGION:
        if upper.startswith(prefix):
            return region
    return "OTHER"


def region_label(region: str) -> str:
    return REGION_LABELS.get(region, region.replace("_", " ").title())


def group_datacenters(datacenters: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Group datacenter records (with an optional `region`) by region."""
    grouped: dict[str, list[str]] = {}
    for entry in datacenters:
        datacenter_id = str(entry.get("id") or "").strip()
        if not datacenter_id:
            continue
        region = str(entry.get("region") or "").strip().upper() or region_for_datacenter(datacenter_id)
        grouped.setdefault(region, []).append(datacenter_id)
    for ids in grouped.values():
        ids.sort()
    return grouped


# Common RunPod GPUs, used when the live catalog cannot be read.
GPU_FALLBACK: list[dict[str, Any]] = [
    {"id": "NVIDIA RTX A4000", "name": "RTX A4000", "memory": 16, "secure_price": 0.24},
    {"id": "NVIDIA RTX A5000", "name": "RTX A5000", "memory": 24, "secure_price": 0.27},
    {"id": "NVIDIA RTX 4090", "name": "RTX 4090", "memory": 24, "secure_price": 0.69},
    {"id": "NVIDIA RTX PRO 4500 Blackwell Server Edition", "name": "RTX PRO 4500", "memory": 32, "secure_price": 0.72},
    {"id": "NVIDIA L40S", "name": "L40S", "memory": 48, "secure_price": 1.09},
    {"id": "NVIDIA A40", "name": "A40", "memory": 48, "secure_price": 0.49},
    {"id": "NVIDIA RTX A6000", "name": "RTX A6000", "memory": 48, "secure_price": 0.53},
    {"id": "NVIDIA A100 80GB PCIe", "name": "A100 PCIe", "memory": 80, "secure_price": 1.59},
    {"id": "NVIDIA A100-SXM4-80GB", "name": "A100 SXM4", "memory": 80, "secure_price": 1.59},
    {"id": "NVIDIA H100 80GB HBM3", "name": "H100", "memory": 80, "secure_price": 3.49},
    {"id": "NVIDIA RTX PRO 6000 Blackwell Server Edition", "name": "RTX PRO 6000 Blackwell", "memory": 96, "secure_price": 2.09},
    {"id": "NVIDIA H200", "name": "H200", "memory": 141, "secure_price": 4.59},
    {"id": "NVIDIA B200", "name": "B200", "memory": 180, "secure_price": 6.79},
]


# Starting points for the model editor. They are hints, not restrictions.
MODEL_PRESETS: dict[str, dict[str, Any]] = {
    "vllm-chat": {
        "label": "vLLM · Chat (FP8/BF16)",
        "description": "Standard server for safetensors models such as Qwen.",
        "runtime": "vllm",
        "defaults": {
            "context_length": 65536,
            "max_sequences": 2,
            "gpu_memory_utilization": 0.9,
            "volume_gb": 64,
        },
        "gpu_memory_gb": 48,
        "hint": "Requires roughly 1.3x the model size in VRAM.",
    },
    "vllm-coding": {
        "label": "vLLM · Coding / Agenten (Tools)",
        "description": "Like vLLM chat but with tool-call support enabled.",
        "runtime": "vllm",
        "defaults": {
            "context_length": 65536,
            "max_sequences": 2,
            "gpu_memory_utilization": 0.9,
            "volume_gb": 64,
        },
        "gpu_memory_gb": 48,
        "hint": "Only enable the tool parser for models that support it.",
    },
    "gguf-chat": {
        "label": "llama.cpp · GGUF",
        "description": "Quantised GGUF file served through llama.cpp.",
        "runtime": "llama-cpp",
        "defaults": {
            "context_length": 32768,
            "max_sequences": 2,
            "gpu_memory_utilization": 0.9,
            "volume_gb": 64,
        },
        "gpu_memory_gb": 24,
        "hint": "Enter the exact .gguf filename from the model repository.",
    },
    "bonsai": {
        "label": "Bonsai · Ternary GGUF (experimental)",
        "description": "Special runtime for Ternary Bonsai models.",
        "runtime": "bonsai",
        "defaults": {
            "context_length": 65536,
            "max_sequences": 4,
            "gpu_memory_utilization": 0.9,
            "volume_gb": 24,
        },
        "gpu_memory_gb": 24,
        "hint": "Experimental; the runtime image is a third-party fork.",
    },
}
