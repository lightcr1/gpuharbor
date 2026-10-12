"""Image and video server for the diffusers runtime.

Runs inside the pod on 127.0.0.1:8001; gateway.py authenticates and proxies to it.
The pipeline is chosen from a fixed list (MEDIA_PIPELINE); nothing from a request or
from a model repository selects code to run.

    POST /v1/images/generations   OpenAI image API, base64 result
    POST /v1/videos               start a render job (OpenAI videos shape)
    GET  /v1/videos/{id}          job status and progress
    GET  /v1/videos/{id}/content  the finished MP4
    GET  /health                  503 while loading; {"busy": true} while rendering
"""
from __future__ import annotations

import asyncio
import base64
import io
import os
import re
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

OUTPUT_DIR = Path(os.getenv("MEDIA_OUTPUT_DIR", "/workspace/outputs"))
MAX_VIDEO_SECONDS = 10
VIDEO_FPS = 24
MAX_VIDEO_PIXELS = 1280 * 720
MAX_IMAGE_PIXELS = 1664 * 1664
SIZE = re.compile(r"^(\d{3,4})x(\d{3,4})$")

# Fixed pipelines. The class is imported lazily so this module loads without torch (tests).
PIPELINES: dict[str, dict[str, Any]] = {
    "wan22-ti2v": {
        "kind": "video",
        "default_size": "1280x704",
        "default_steps": 50,
        "offload": False,
    },
    "qwen-image": {
        "kind": "image",
        "default_size": "1328x1328",
        "default_steps": 50,
        "offload": True,
    },
}


class ImageRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    model: str | None = None
    n: int = Field(default=1, ge=1, le=1)
    size: str | None = None
    response_format: str = "b64_json"
    seed: int | None = Field(default=None, ge=0, le=2**31 - 1)
    steps: int | None = Field(default=None, ge=4, le=100)


class VideoRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    model: str | None = None
    size: str | None = None
    seconds: int | str = 5
    seed: int | None = Field(default=None, ge=0, le=2**31 - 1)
    steps: int | None = Field(default=None, ge=4, le=100)


def parse_size(value: str | None, default: str, max_pixels: int) -> tuple[int, int]:
    match = SIZE.fullmatch(value or default)
    if not match:
        raise HTTPException(status_code=400, detail="size must look like 1280x704")
    width, height = int(match.group(1)), int(match.group(2))
    if width % 32 or height % 32:
        raise HTTPException(status_code=400, detail="width and height must be multiples of 32")
    if width * height > max_pixels:
        raise HTTPException(status_code=400, detail=f"size is too large (at most {max_pixels} pixels)")
    return width, height


def frames_for(seconds: int | str) -> int:
    try:
        value = int(seconds)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail="seconds must be a whole number") from error
    if not 1 <= value <= MAX_VIDEO_SECONDS:
        raise HTTPException(status_code=400, detail=f"seconds must be between 1 and {MAX_VIDEO_SECONDS}")
    return value * VIDEO_FPS + 1  # the video VAE wants 4n+1 frames


def load_pipeline(name: str, repository: str, token: str | None):
    """Build the diffusers pipeline for a fixed pipeline name. Needs torch and a GPU."""
    import torch

    spec = PIPELINES[name]
    if name == "wan22-ti2v":
        from diffusers import AutoencoderKLWan, WanPipeline

        vae = AutoencoderKLWan.from_pretrained(repository, subfolder="vae", torch_dtype=torch.float32, token=token)
        pipeline = WanPipeline.from_pretrained(repository, vae=vae, torch_dtype=torch.bfloat16, token=token)
    else:
        from diffusers import DiffusionPipeline

        pipeline = DiffusionPipeline.from_pretrained(repository, torch_dtype=torch.bfloat16, token=token)
    if spec["offload"]:
        pipeline.enable_model_cpu_offload()
    else:
        pipeline.to("cuda")
    return pipeline


def make_generator(seed: int | None):
    import torch

    return torch.Generator(device="cpu").manual_seed(secrets.randbelow(2**31) if seed is None else seed)


def encode_video(frames: Any, path: Path) -> None:
    from diffusers.utils import export_to_video

    export_to_video(frames, str(path), fps=VIDEO_FPS)


class Media:
    """One pipeline, one render at a time."""

    def __init__(self) -> None:
        self.pipeline: Any = None
        self.name = os.environ.get("MEDIA_PIPELINE", "")
        self.kind = PIPELINES.get(self.name, {}).get("kind", "")
        self.served = {
            value.strip() for value in os.environ.get("SERVED_MODEL_NAMES", "").split(",") if value.strip()
        }
        self.error: str | None = None
        self.lock = asyncio.Lock()
        self.jobs: dict[str, dict[str, Any]] = {}

    @property
    def busy(self) -> bool:
        return self.lock.locked()


media = Media()


async def load_in_background() -> None:
    try:
        if media.name not in PIPELINES:
            raise ValueError("Unknown media pipeline")
        token = os.getenv("HF_TOKEN") or None
        media.pipeline = await asyncio.to_thread(load_pipeline, media.name, os.environ["MODEL_ID"], token)
    except Exception as error:  # noqa: BLE001 - reported on /health, the pod keeps answering
        media.error = f"{type(error).__name__}: {error}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    task = asyncio.create_task(load_in_background())
    yield
    task.cancel()


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, Any]:
    if media.error:
        raise HTTPException(status_code=500, detail=media.error)
    if media.pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline is loading")
    return {"status": "ready", "busy": media.busy}


def require_ready(kind: str, model: str | None) -> None:
    if media.error:
        raise HTTPException(status_code=500, detail=media.error)
    if media.pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline is loading")
    if media.kind != kind:
        raise HTTPException(status_code=400, detail=f"This pod serves a {media.kind or 'unknown'} model, not {kind}")
    if model and media.served and model not in media.served:
        raise HTTPException(status_code=404, detail=f"Unknown model {model}; use one of {sorted(media.served)}")


def run_image(request: ImageRequest, width: int, height: int) -> str:
    steps = request.steps or PIPELINES[media.name]["default_steps"]
    result = media.pipeline(
        prompt=request.prompt,
        negative_prompt=" ",
        width=width,
        height=height,
        num_inference_steps=steps,
        true_cfg_scale=4.0,
        generator=make_generator(request.seed),
    )
    buffer = io.BytesIO()
    result.images[0].save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


@app.post("/v1/images/generations")
async def generate_image(request: ImageRequest) -> dict[str, Any]:
    require_ready("image", request.model)
    if request.response_format != "b64_json":
        raise HTTPException(status_code=400, detail="Only response_format b64_json is supported")
    width, height = parse_size(request.size, PIPELINES[media.name]["default_size"], MAX_IMAGE_PIXELS)
    async with media.lock:
        encoded = await asyncio.to_thread(run_image, request, width, height)
    return {"created": int(time.time()), "data": [{"b64_json": encoded}]}


def run_video(job: dict[str, Any], request: VideoRequest, width: int, height: int, frames: int) -> None:
    steps = request.steps or PIPELINES[media.name]["default_steps"]
    total = steps

    def progress(_pipe: Any, step: int, _timestep: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
        job["progress"] = min(99, int((step + 1) * 100 / total))
        return kwargs

    output = media.pipeline(
        prompt=request.prompt,
        height=height,
        width=width,
        num_frames=frames,
        guidance_scale=5.0,
        num_inference_steps=steps,
        generator=make_generator(request.seed),
        callback_on_step_end=progress,
    )
    encode_video(output.frames[0], OUTPUT_DIR / f"{job['id']}.mp4")


async def render(job: dict[str, Any], request: VideoRequest, width: int, height: int, frames: int) -> None:
    async with media.lock:
        job["status"] = "in_progress"
        try:
            await asyncio.to_thread(run_video, job, request, width, height, frames)
            job["status"], job["progress"] = "completed", 100
        except Exception as error:  # noqa: BLE001 - reported on the job
            job["status"], job["error"] = "failed", {"message": f"{type(error).__name__}: {error}"}


def job_view(job: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in job.items() if not key.startswith("_")}


@app.post("/v1/videos", status_code=202)
async def create_video(request: VideoRequest) -> dict[str, Any]:
    require_ready("video", request.model)
    width, height = parse_size(request.size, PIPELINES[media.name]["default_size"], MAX_VIDEO_PIXELS)
    frames = frames_for(request.seconds)
    if sum(1 for job in media.jobs.values() if job["status"] in {"queued", "in_progress"}) >= 4:
        raise HTTPException(status_code=429, detail="Too many queued videos; wait for one to finish")
    job_id = "video_" + secrets.token_hex(8)
    job = {
        "id": job_id,
        "object": "video",
        "model": request.model or next(iter(sorted(media.served)), media.name),
        "status": "queued",
        "progress": 0,
        "created_at": int(time.time()),
        "seconds": str(request.seconds),
        "size": f"{width}x{height}",
    }
    media.jobs[job_id] = job
    job["_task"] = asyncio.create_task(render(job, request, width, height, frames))
    return job_view(job)


def find_job(job_id: str) -> dict[str, Any]:
    job = media.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return job


@app.get("/v1/videos/{job_id}")
async def get_video(job_id: str) -> dict[str, Any]:
    return job_view(find_job(job_id))


@app.get("/v1/videos/{job_id}/content")
async def video_content(job_id: str) -> FileResponse:
    job = find_job(job_id)
    path = OUTPUT_DIR / f"{job['id']}.mp4"
    if job["status"] != "completed" or not path.exists():
        raise HTTPException(status_code=409, detail=f"Video is {job['status']}")
    return FileResponse(path, media_type="video/mp4", filename=f"{job_id}.mp4")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, access_log=False)
