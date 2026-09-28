from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def load_gateway(monkeypatch):
    monkeypatch.setenv("GATEWAY_API_KEY", "g" * 40)
    path = Path(__file__).parents[1] / "runtime/gateway.py"
    spec = importlib.util.spec_from_file_location("gpuharbor_runtime_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_vllm_command_contains_only_validated_options(monkeypatch):
    gateway = load_gateway(monkeypatch)
    monkeypatch.setenv("MODEL_ID", "example/model")
    monkeypatch.setenv("SERVED_MODEL_NAMES", "chat,code")
    monkeypatch.setenv(
        "VLLM_EXTRA_ARGS_JSON",
        json.dumps(["--trust-remote-code", "--reasoning-parser", "qwen3"]),
    )
    command = gateway.build_vllm_command()
    assert command[:3] == ["vllm", "serve", "example/model"]
    assert command[-3:] == ["--trust-remote-code", "--reasoning-parser", "qwen3"]


def test_vllm_command_rejects_argument_injection(monkeypatch):
    gateway = load_gateway(monkeypatch)
    monkeypatch.setenv("MODEL_ID", "example/model")
    monkeypatch.setenv("SERVED_MODEL_NAMES", "chat")
    monkeypatch.setenv("VLLM_EXTRA_ARGS_JSON", json.dumps(["--host", "0.0.0.0"]))
    with pytest.raises(ValueError, match="Unsupported"):
        gateway.build_vllm_command()


def test_llama_context_is_per_parallel_slot(monkeypatch):
    gateway = load_gateway(monkeypatch)
    monkeypatch.setenv("MAX_MODEL_LEN", "8192")
    monkeypatch.setenv("MAX_NUM_SEQS", "2")
    monkeypatch.setenv("SERVED_MODEL_NAMES", "chat")
    command = gateway.build_llama_command("/models/example.gguf")
    assert command[command.index("--ctx-size") + 1] == "16384"
    assert command[command.index("--parallel") + 1] == "2"
