from __future__ import annotations

import asyncio
import json
import time
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel, Field, model_validator

from .config import Settings
from .registry import ModelDefinition, RuntimeDefinition


class RunpodError(RuntimeError):
    pass


class LaunchOptions(BaseModel):
    model_id: str
    context_length: int | None = Field(default=None, ge=1024, le=262144)
    max_sequences: int | None = Field(default=None, ge=1, le=32)
    gpu_memory_utilization: float | None = Field(default=None, ge=0.5, le=0.99)
    gpu_type_id: str | None = None
    datacenter_id: str | None = None
    volume_gb: int | None = Field(default=None, ge=10, le=1000)


class ResolvedLaunch(BaseModel):
    profile_id: str
    profile: ModelDefinition
    runtime: RuntimeDefinition
    context_length: int
    max_sequences: int
    gpu_memory_utilization: float
    gpu_type_ids: list[str]
    datacenter_ids: list[str]
    volume_gb: int

    @model_validator(mode="after")
    def ensure_candidates(self) -> "ResolvedLaunch":
        if not self.gpu_type_ids or not self.datacenter_ids:
            raise ValueError("At least one GPU and datacenter are required")
        return self


def resolve_launch(
    options: LaunchOptions,
    model: ModelDefinition,
    runtime: RuntimeDefinition,
    default_datacenters: list[str],
) -> ResolvedLaunch:
    if options.gpu_type_id and options.gpu_type_id not in model.gpu_type_ids:
        raise ValueError("Selected GPU is not allowed by this model profile")
    if options.datacenter_id and options.datacenter_id not in default_datacenters:
        raise ValueError("Selected datacenter is not configured")
    return ResolvedLaunch(
        profile_id=options.model_id,
        profile=model,
        runtime=runtime,
        context_length=options.context_length or model.context_length,
        max_sequences=options.max_sequences or model.max_sequences,
        gpu_memory_utilization=options.gpu_memory_utilization or model.gpu_memory_utilization,
        gpu_type_ids=[options.gpu_type_id] if options.gpu_type_id else model.gpu_type_ids,
        datacenter_ids=[options.datacenter_id] if options.datacenter_id else default_datacenters,
        volume_gb=options.volume_gb or model.volume_gb,
    )


def runtime_env(launch: ResolvedLaunch, gateway_token: str, hf_token: str | None) -> dict[str, str]:
    vllm_args: list[str] = []
    if launch.profile.trust_remote_code:
        vllm_args.append("--trust-remote-code")
    if launch.profile.reasoning_parser:
        vllm_args.extend(["--reasoning-parser", launch.profile.reasoning_parser])
    if launch.profile.enable_auto_tool_choice:
        vllm_args.append("--enable-auto-tool-choice")
    if launch.profile.tool_call_parser:
        vllm_args.extend(["--tool-call-parser", launch.profile.tool_call_parser])
    env = {
        "GATEWAY_API_KEY": gateway_token,
        "RUNTIME_BACKEND": launch.runtime.backend,
        "MODEL_ID": launch.profile.model_id,
        "SERVED_MODEL_NAMES": ",".join(launch.profile.served_names),
        "MAX_MODEL_LEN": str(launch.context_length),
        "MAX_NUM_SEQS": str(launch.max_sequences),
        "GPU_MEMORY_UTILIZATION": str(launch.gpu_memory_utilization),
        "VLLM_EXTRA_ARGS_JSON": json.dumps(vllm_args),
        "HF_HOME": "/workspace/huggingface",
        "HUGGINGFACE_HUB_CACHE": "/workspace/huggingface/hub",
    }
    if launch.profile.gguf_file:
        env["GGUF_FILENAME"] = launch.profile.gguf_file
    if hf_token:
        env["HF_TOKEN"] = hf_token
    return env


def pod_status(pod: dict[str, Any]) -> str:
    return str(pod.get("status", "")).upper()


def proxy_url(pod_id: str) -> str:
    return f"https://{pod_id}-8000.proxy.runpod.net"


class RunpodClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url=settings.runpod_api_base.rstrip("/"),
            headers={"Authorization": f"Bearer {settings.runpod_api_key.get_secret_value()}"},
            timeout=30,
            transport=transport,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self.client.request(method, path, **kwargs)
        except httpx.HTTPError as error:
            raise RunpodError(f"RunPod network error: {error}") from error
        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise RunpodError(f"RunPod {method} {path}: HTTP {response.status_code}: {detail}")
        return response.json() if response.content else None

    def create_payload(self, launch: ResolvedLaunch, gpu: str, datacenter: str) -> dict[str, Any]:
        hf_token = (
            self.settings.huggingface_token.get_secret_value()
            if self.settings.huggingface_token
            else None
        )
        return {
            "name": self.settings.runpod_pod_name,
            "image": self.settings.runtime_image(launch.profile.runtime),
            "cloud": "SECURE",
            "gpu": {"id": gpu, "count": 1},
            "dataCenterIds": [datacenter],
            "disk": self.settings.runpod_container_disk_gb,
            "mounts": {"persistent": {"size": launch.volume_gb, "path": "/workspace"}},
            "env": runtime_env(
                launch,
                self.settings.runtime_gateway_token.get_secret_value(),
                hf_token,
            ),
            "ports": ["8000/http"],
            "startSsh": False,
        }

    def create_candidates(self, launch: ResolvedLaunch) -> list[dict[str, Any]]:
        return [
            {
                "gpu_type_id": gpu,
                "datacenter_id": datacenter,
                "payload": self.create_payload(launch, gpu, datacenter),
            }
            for gpu in launch.gpu_type_ids
            for datacenter in launch.datacenter_ids
        ]

    async def list_pods(self) -> list[dict[str, Any]]:
        result = await self.request("GET", "/pods")
        pods = result.get("pods") if isinstance(result, dict) else None
        if not isinstance(pods, list):
            raise RunpodError("Unexpected RunPod pod-list response")
        return pods

    async def get_pod(self, pod_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/pods/{pod_id}")

    async def get_gpu(self, gpu_type_id: str) -> dict[str, Any]:
        return await self.request(
            "GET",
            f"/catalog/gpus/{quote(gpu_type_id, safe='')}",
            params={"include": "AVAILABILITY", "product": "POD", "count": 1},
        )

    async def create_pod(self, launch: ResolvedLaunch) -> dict[str, Any]:
        existing = [
            pod for pod in await self.list_pods()
            if pod.get("name") == self.settings.runpod_pod_name
            and pod_status(pod) != "TERMINATED"
        ]
        if existing:
            raise RunpodError("A managed GPUHarbor pod already exists; refusing duplicate creation")
        last_error = "No placement candidate was attempted"
        for candidate in self.create_candidates(launch):
            try:
                response = await self.client.post("/pods", json=candidate["payload"])
            except httpx.HTTPError as error:
                raise RunpodError(
                    "Create response was lost. Check RunPod before retrying to avoid duplicate pods"
                ) from error
            if response.status_code == 201:
                pod = response.json()
                pod["_gpuharbor_gpu_type_id"] = candidate["gpu_type_id"]
                pod["_gpuharbor_datacenter_id"] = candidate["datacenter_id"]
                return pod
            last_error = f"{candidate['gpu_type_id']} / {candidate['datacenter_id']}: HTTP {response.status_code}"
            if response.status_code in {402, 422, 429} or response.status_code >= 500:
                raise RunpodError(last_error)
        raise RunpodError(f"No configured placement was available. {last_error}")

    async def start_pod(self, pod_id: str) -> None:
        await self.request("POST", f"/pods/{pod_id}/action", json={"action": "start"})

    async def stop_pod(self, pod_id: str) -> None:
        await self.request("POST", f"/pods/{pod_id}/action", json={"action": "stop"})

    async def delete_pod(self, pod_id: str) -> None:
        await self.request("DELETE", f"/pods/{pod_id}")

    async def configure(self, pod_id: str, launch: ResolvedLaunch) -> None:
        hf_token = self.settings.huggingface_token.get_secret_value() if self.settings.huggingface_token else None
        await self.request(
            "PATCH",
            f"/pods/{pod_id}",
            json={"env": runtime_env(launch, self.settings.runtime_gateway_token.get_secret_value(), hf_token)},
        )

    async def wait_for_status(self, pod_id: str, desired: set[str], timeout: int = 300) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        last: dict[str, Any] = {}
        while time.monotonic() < deadline:
            last = await self.get_pod(pod_id)
            status = pod_status(last)
            if status in desired:
                return last
            if status in {"ERROR", "TERMINATED"}:
                raise RunpodError(f"Pod entered {status}")
            await asyncio.sleep(3)
        raise RunpodError(f"Timed out waiting for {sorted(desired)}; last state: {last}")
