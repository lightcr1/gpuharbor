from __future__ import annotations

import asyncio
import json
import os
import secrets
import signal
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

INTERNAL_URL = "http://127.0.0.1:8001"
API_KEY = os.environ["GATEWAY_API_KEY"]


def build_vllm_command() -> list[str]:
    command = [
        "vllm", "serve", os.environ["MODEL_ID"], "--host", "127.0.0.1", "--port", "8001",
        "--max-model-len", os.getenv("MAX_MODEL_LEN", "32768"),
        "--max-num-seqs", os.getenv("MAX_NUM_SEQS", "2"),
        "--gpu-memory-utilization", os.getenv("GPU_MEMORY_UTILIZATION", "0.90"),
        "--served-model-name",
        *[name.strip() for name in os.environ["SERVED_MODEL_NAMES"].split(",") if name.strip()],
    ]
    extra = json.loads(os.getenv("VLLM_EXTRA_ARGS_JSON", "[]"))
    if not isinstance(extra, list) or any(not isinstance(value, str) for value in extra):
        raise ValueError("Unsupported vLLM option format")
    validated: list[str] = []
    seen: set[str] = set()
    index = 0
    value_options = {
        "--reasoning-parser": {"qwen3"},
        "--tool-call-parser": {"qwen3_coder"},
    }
    flag_options = {"--trust-remote-code", "--enable-auto-tool-choice"}
    while index < len(extra):
        option = extra[index]
        if option in seen:
            raise ValueError("Duplicate vLLM option")
        seen.add(option)
        if option in flag_options:
            validated.append(option)
            index += 1
            continue
        if option in value_options and index + 1 < len(extra) and extra[index + 1] in value_options[option]:
            validated.extend([option, extra[index + 1]])
            index += 2
            continue
        raise ValueError("Unsupported vLLM option")
    if "--enable-auto-tool-choice" in seen and "--tool-call-parser" not in seen:
        raise ValueError("Automatic tool choice requires a tool-call parser")
    return command + validated


def build_llama_command(model_path: str) -> list[str]:
    context = int(os.getenv("MAX_MODEL_LEN", "32768"))
    parallel = int(os.getenv("MAX_NUM_SEQS", "2"))
    if context < 1 or parallel < 1:
        raise ValueError("Context and parallelism must be positive")
    return [
        "/app/llama-server", "--model", model_path, "--host", "127.0.0.1", "--port", "8001",
        "--ctx-size", str(context * parallel), "--parallel", str(parallel), "--n-gpu-layers", "99",
        "--alias", os.environ["SERVED_MODEL_NAMES"],
    ]


async def runtime_command() -> list[str]:
    backend = os.getenv("RUNTIME_BACKEND", "vllm")
    if backend == "vllm":
        return build_vllm_command()
    if backend not in {"llama", "bonsai"}:
        raise ValueError("Unknown runtime backend")
    from huggingface_hub import hf_hub_download
    filename = os.environ["GGUF_FILENAME"]
    if filename in {".", ".."} or "/" in filename or "\\" in filename or not filename.endswith(".gguf"):
        raise ValueError("Invalid GGUF filename")
    path = await asyncio.to_thread(
        hf_hub_download,
        repo_id=os.environ["MODEL_ID"],
        filename=filename,
        token=os.getenv("HF_TOKEN") or None,
    )
    return build_llama_command(path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    command = await runtime_command()
    app.state.client = httpx.AsyncClient(timeout=None)
    app.state.runtime = await asyncio.create_subprocess_exec(*command)
    try:
        yield
    finally:
        if app.state.runtime.returncode is None:
            app.state.runtime.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(app.state.runtime.wait(), timeout=20)
            except asyncio.TimeoutError:
                app.state.runtime.kill()
                await app.state.runtime.wait()
        await app.state.client.aclose()


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


def authorize(value: str | None) -> None:
    supplied = value[7:] if value and value.startswith("Bearer ") else ""
    if not secrets.compare_digest(supplied, API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
async def health(authorization: str | None = Header(default=None)) -> dict[str, str]:
    authorize(authorization)
    try:
        response = await app.state.client.get(f"{INTERNAL_URL}/health", timeout=3)
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail=f"Model loading: {error}") from error
    return {"status": "ready"}


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request, authorization: str | None = Header(default=None)):
    authorize(authorization)
    if not path or "\\" in path or any(part in {"", ".", ".."} for part in path.split("/")):
        raise HTTPException(status_code=400, detail="Invalid API path")
    query = f"?{request.url.query}" if request.url.query else ""
    upstream_request = app.state.client.build_request(
        request.method,
        f"{INTERNAL_URL}/v1/{path}{query}",
        headers={
            "Content-Type": request.headers.get("content-type", "application/json"),
            "Accept": request.headers.get("accept", "application/json"),
            "Accept-Encoding": "identity",
        },
        content=await request.body(),
    )
    try:
        upstream = await app.state.client.send(upstream_request, stream=True)
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail=f"Model unavailable: {error}") from error
    return StreamingResponse(
        upstream.aiter_raw(), status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type"),
        background=BackgroundTask(upstream.aclose),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)
