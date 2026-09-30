"""Keep optional integrations pointed at the models GPUHarbor serves.

OpenHands stores its LLM settings as named profiles. GPUHarbor writes one profile
per model profile (``gpuharbor-<id>``), so the model works in OpenHands without
touching its settings screen. Only profiles with that prefix are ever changed;
profiles a user made themselves are left alone.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx

from .registry import ModelDefinition

log = logging.getLogger("gpuharbor.integrations")

PROFILE_PREFIX = "gpuharbor-"
CONTROLLER_V1 = "http://controller:8080/v1"
_PROFILE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def profile_name(model_id: str) -> str:
    return f"{PROFILE_PREFIX}{model_id}"[:64].rstrip("-.")


def openhands_llm(model: ModelDefinition, token: str, base_url: str = CONTROLLER_V1) -> dict[str, Any]:
    """LLM settings that make a GPUHarbor model behave in OpenHands."""
    return {
        "model": f"openai/{model.served_names[0]}",
        "base_url": base_url,
        "api_key": token,
        # Native tool calls need the server to run with --enable-auto-tool-choice.
        # Everywhere else OpenHands falls back to prompt-based function calling.
        "native_tool_calling": bool(model.enable_auto_tool_choice),
        "max_output_tokens": max(1024, min(8192, model.context_length // 4)),
        # A cold pod can take minutes to load weights before the first answer.
        "timeout": 600,
        # Options meant for hosted providers; a local OpenAI-compatible server ignores or rejects them.
        "reasoning_effort": "none",
        "enable_encrypted_reasoning": False,
        "caching_prompt": False,
    }


def pi_models(models: dict[str, ModelDefinition]) -> list[dict[str, Any]]:
    """Model entries for the ``gpuharbor`` provider in PI's models.json.

    One entry per profile, named by its first served name. A served name that an
    earlier profile already uses is skipped so the ids stay unique.
    """
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for model in models.values():
        served = model.served_names[0]
        if model.status == "disabled" or served in seen:
            continue
        seen.add(served)
        entries.append(
            {
                "id": served,
                "name": model.name,
                "reasoning": False,
                "input": ["text", "image"] if "vision" in model.capabilities else ["text"],
                "contextWindow": model.context_length,
                "maxTokens": max(1024, min(8192, model.context_length // 4)),
            }
        )
    return entries


def pi_without_tools(models: dict[str, ModelDefinition]) -> list[str]:
    """Served names of vLLM profiles that run without tool-call parsing (PI's tools would not work).

    The flag is a vLLM setting. llama.cpp profiles are not listed: whether their tool calls work depends on the model's chat template.
    """
    listed = {entry["id"] for entry in pi_models(models)}
    return sorted({m.served_names[0] for m in models.values() if m.runtime == "vllm" and not m.enable_auto_tool_choice} & listed)


def desired_profiles(models: dict[str, ModelDefinition], token: str) -> dict[str, dict[str, Any]]:
    desired: dict[str, dict[str, Any]] = {}
    for model_id, model in models.items():
        if model.status == "disabled":
            continue
        name = profile_name(model_id)
        if _PROFILE_NAME.fullmatch(name):
            desired[name] = openhands_llm(model, token)
    return desired


async def sync_openhands(
    client: httpx.AsyncClient,
    url: str,
    key: str,
    models: dict[str, ModelDefinition],
    token: str,
    running_model_id: str = "",
) -> dict[str, Any]:
    """Create or update GPUHarbor's OpenHands profiles and pick a sensible active one."""
    base = url.rstrip("/")
    headers = {"X-Session-API-Key": key}

    async def call(method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = await client.request(method, f"{base}{path}", headers=headers, timeout=20, **kwargs)
        if response.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"OpenHands {method} {path}: HTTP {response.status_code}",
                request=response.request,
                response=response,
            )
        return response

    current = (await call("GET", "/api/profiles")).json()
    existing = {entry["name"] for entry in current.get("profiles", [])}
    active = current.get("active_profile")

    desired = desired_profiles(models, token)
    for name, llm in desired.items():
        await call("POST", f"/api/profiles/{name}", json={"llm": llm, "include_secrets": True})
    stale = [name for name in existing if name.startswith(PROFILE_PREFIX) and name not in desired]
    for name in stale:
        await call("DELETE", f"/api/profiles/{name}")

    # Follow the model that is actually running, but never override a profile the user picked.
    preferred = profile_name(running_model_id) if running_model_id else ""
    ours = active is None or active in desired or active in stale
    target = None
    if ours:
        target = preferred if preferred in desired else (active if active in desired else next(iter(desired), None))
    if target and target != active:
        await call("POST", f"/api/profiles/{target}/activate")
        active = target
    return {"profiles": sorted(desired), "removed": sorted(stale), "active": active}


class IntegrationSync:
    """Background worker that retries until OpenHands is reachable, then re-syncs on demand."""

    def __init__(self) -> None:
        self.wakeup = asyncio.Event()
        self.last: dict[str, Any] = {"synced": False, "error": None}

    def request(self) -> None:
        self.wakeup.set()

    async def run(self, sync, interval: float = 600.0, first_retry: float = 15.0) -> None:
        failures = 0
        while True:
            try:
                self.last = {"synced": True, "error": None, **await sync()}
                failures = 0
                delay = interval
            except asyncio.CancelledError:
                raise
            except Exception as error:  # noqa: BLE001 - OpenHands may simply not be up yet
                failures += 1
                self.last = {"synced": False, "error": str(error)}
                log.info("OpenHands sync pending: %s", error)
                delay = min(first_retry * 2 ** (failures - 1), 120)
            try:
                await asyncio.wait_for(self.wakeup.wait(), timeout=delay)
            except asyncio.TimeoutError:
                pass
            self.wakeup.clear()
