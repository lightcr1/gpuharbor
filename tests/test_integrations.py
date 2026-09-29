"""OpenHands profile sync, tested against a small in-memory fake of its API."""
from __future__ import annotations

import json
from pathlib import Path

import httpx

from gpuharbor.integrations import PROFILE_PREFIX, desired_profiles, openhands_llm, profile_name, sync_openhands
from gpuharbor.registry import Registry

ROOT = Path(__file__).parents[1]


def models(tmp_path):
    registry = Registry(ROOT / "registry/models.json", ROOT / "registry/runtimes.json", tmp_path / "user.json")
    return registry.models()


class FakeOpenHands:
    def __init__(self, profiles=None, active=None):
        self.profiles = dict(profiles or {})
        self.active = active
        self.calls = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        assert request.headers["x-session-api-key"] == "key"
        path = request.url.path
        self.calls.append((request.method, path))
        if request.method == "GET" and path == "/api/profiles":
            return httpx.Response(200, json={
                "profiles": [{"name": name} for name in self.profiles],
                "active_profile": self.active,
            })
        name = path.removeprefix("/api/profiles/").removesuffix("/activate")
        if request.method == "POST" and path.endswith("/activate"):
            self.active = name
            return httpx.Response(200, json={})
        if request.method == "POST":
            self.profiles[name] = json.loads(request.content)["llm"]
            return httpx.Response(201, json={})
        if request.method == "DELETE":
            self.profiles.pop(name, None)
            if self.active == name:
                self.active = None
            return httpx.Response(200, json={})
        return httpx.Response(404)


async def run(fake, models_, running=""):
    async with httpx.AsyncClient(transport=httpx.MockTransport(fake.handler)) as client:
        return await sync_openhands(client, "http://openhands:8000", "key", models_, "tok", running)


def test_llm_settings_match_the_profile(tmp_path):
    catalog = models(tmp_path)
    coder = openhands_llm(catalog["qwen3-coder-30b-fp8"], "tok")
    assert coder["model"] == f"openai/{catalog['qwen3-coder-30b-fp8'].served_names[0]}"
    assert coder["base_url"] == "http://controller:8080/v1" and coder["api_key"] == "tok"
    assert coder["native_tool_calling"] is True  # this profile enables auto tool choice
    gguf = openhands_llm(catalog["ternary-bonsai-2-27b-ptq1"], "tok")
    assert gguf["native_tool_calling"] is False  # llama.cpp: prompt-based tool calls
    assert 1024 <= gguf["max_output_tokens"] <= 8192


async def test_first_sync_creates_a_profile_per_model_and_activates_one(tmp_path):
    fake = FakeOpenHands()
    result = await run(fake, models(tmp_path), running="qwen3-coder-30b-fp8")
    assert set(fake.profiles) == set(desired_profiles(models(tmp_path), "tok"))
    assert all(name.startswith(PROFILE_PREFIX) for name in fake.profiles)
    assert fake.active == profile_name("qwen3-coder-30b-fp8") == result["active"]


async def test_active_profile_follows_the_running_model(tmp_path):
    fake = FakeOpenHands()
    catalog = models(tmp_path)
    await run(fake, catalog, running="qwen38-27b-fp8")
    await run(fake, catalog, running="qwen3-coder-30b-fp8")
    assert fake.active == profile_name("qwen3-coder-30b-fp8")


async def test_a_profile_the_user_chose_is_never_touched(tmp_path):
    fake = FakeOpenHands(profiles={"mine": {"model": "openai/x"}}, active="mine")
    await run(fake, models(tmp_path), running="qwen38-27b-fp8")
    assert fake.active == "mine" and "mine" in fake.profiles
    assert ("DELETE", "/api/profiles/mine") not in fake.calls


async def test_stale_gpuharbor_profiles_are_removed(tmp_path):
    fake = FakeOpenHands(profiles={"gpuharbor-deleted-model": {}, "other": {}})
    result = await run(fake, models(tmp_path))
    assert "gpuharbor-deleted-model" not in fake.profiles and "other" in fake.profiles
    assert result["removed"] == ["gpuharbor-deleted-model"]


def test_integrations_endpoint_reports_links(app_client, monkeypatch):
    client, main = app_client
    monkeypatch.setattr(main.settings, "gpuharbor_link_openwebui", "https:8444")
    monkeypatch.setattr(main.settings, "openhands_url", "")
    login = client.post("/api/login", json={"username": "admin", "password": "p" * 40})
    assert login.status_code == 200
    data = client.get("/api/integrations").json()
    assert data["openwebui"] == {"scheme": "https", "port": 8444}
    assert data["openhands"] is None
