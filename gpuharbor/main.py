from __future__ import annotations

import asyncio
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Settings
from .idle import should_stop_for_idle
from .registry import ModelDefinition, Registry
from .runpod import LaunchOptions, RunpodClient, RunpodError, pod_status, proxy_url, resolve_launch
from .security import LoginLimiter, SecurityHeadersMiddleware, redact_secrets
from .state import ControllerState, StateStore


settings = Settings()
registry = Registry(
    settings.bundled_models_path,
    settings.runtimes_path,
    settings.user_catalog_path,
    settings.models_path,
)
store = StateStore(settings.state_path, settings.runpod_pod_id)
operation_lock = asyncio.Lock()
login_limiter = LoginLimiter(
    settings.gpuharbor_login_max_attempts,
    settings.gpuharbor_login_window_seconds,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.models()
    app.state.runpod = RunpodClient(settings)
    app.state.proxy = httpx.AsyncClient(timeout=None)
    app.state.last_inference = time.monotonic()
    app.state.idle_task = asyncio.create_task(idle_stop_loop(app))
    yield
    app.state.idle_task.cancel()
    try:
        await app.state.idle_task
    except asyncio.CancelledError:
        pass
    await app.state.runpod.close()
    await app.state.proxy.aclose()


async def idle_stop_loop(application: FastAPI) -> None:
    """Stop GPU billing after the configured period without inference traffic."""
    while True:
        await asyncio.sleep(60)
        idle_seconds = time.monotonic() - application.state.last_inference
        if not should_stop_for_idle(idle_seconds, settings.runpod_idle_stop_minutes) or operation_lock.locked():
            continue
        state = store.read()
        if not state.pod_id:
            continue
        try:
            pod = await application.state.runpod.get_pod(state.pod_id)
            if pod_status(pod) != "RUNNING":
                continue
            async with operation_lock:
                await application.state.runpod.stop_pod(state.pod_id)
                await application.state.runpod.wait_for_status(state.pod_id, {"EXITED"})
        except RunpodError:
            # Retry on the next interval; status and manual controls stay available.
            continue


app = FastAPI(title="GPUHarbor", version="0.1.0-dev", lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.gpuharbor_session_secret.get_secret_value(),
    session_cookie="gpuharbor_session",
    max_age=12 * 60 * 60,
    same_site="lax",
    https_only=settings.gpuharbor_cookie_secure,
)


def require_control(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_control_token: Annotated[str | None, Header()] = None,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> None:
    expected = settings.control_token.get_secret_value()
    bearer = authorization.removeprefix("Bearer ") if authorization else ""
    if any(secrets.compare_digest(expected, supplied) for supplied in (bearer, x_control_token or "")):
        return
    if request.session.get("authenticated"):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            session_token = str(request.session.get("csrf_token", ""))
            if not session_token or not x_csrf_token or not secrets.compare_digest(session_token, x_csrf_token):
                raise HTTPException(status_code=403, detail="Invalid CSRF token")
        return
    raise HTTPException(status_code=401, detail="Authentication required")


def require_model_token(authorization: Annotated[str | None, Header()] = None) -> None:
    expected = settings.model_access_token.get_secret_value()
    bearer = authorization.removeprefix("Bearer ") if authorization else ""
    if not secrets.compare_digest(expected, bearer):
        raise HTTPException(status_code=401, detail="Invalid model token")


class LoginRequest(BaseModel):
    username: str
    password: str


class CatalogImportRequest(BaseModel):
    catalog: dict
    replace: bool = False


@app.get("/", include_in_schema=False)
async def dashboard() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/login")
async def login(body: LoginRequest, request: Request) -> dict[str, str | bool]:
    client_key = request.client.host if request.client else "unknown"
    if login_limiter.blocked(client_key):
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts",
            headers={"Retry-After": str(settings.gpuharbor_login_window_seconds)},
        )
    username_ok = secrets.compare_digest(body.username, settings.gpuharbor_admin_username)
    password_ok = secrets.compare_digest(body.password, settings.gpuharbor_admin_password.get_secret_value())
    if not (username_ok and password_ok):
        login_limiter.failure(client_key)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    login_limiter.success(client_key)
    request.session.clear()
    request.session["authenticated"] = True
    request.session["csrf_token"] = secrets.token_urlsafe(32)
    return {"ok": True, "csrf_token": request.session["csrf_token"]}


@app.post("/api/logout", dependencies=[Depends(require_control)])
async def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"ok": True}


@app.get("/api/me")
async def me(request: Request) -> dict[str, str | bool]:
    authenticated = bool(request.session.get("authenticated"))
    return {
        "authenticated": authenticated,
        "csrf_token": str(request.session.get("csrf_token", "")) if authenticated else "",
    }


@app.get("/api/runtimes", dependencies=[Depends(require_control)])
async def runtimes() -> dict:
    return {key: value.model_dump() for key, value in registry.runtimes().items()}


@app.get("/api/controller-settings", dependencies=[Depends(require_control)])
async def controller_settings() -> dict:
    """Safe UI settings only; credentials and runtime image locations stay private."""
    return {
        "datacenter_ids": settings.datacenter_ids,
        "billable_actions_enabled": settings.runpod_allow_billable_actions,
        "idle_stop_minutes": settings.runpod_idle_stop_minutes,
    }


@app.get("/api/models", dependencies=[Depends(require_control)])
async def models() -> dict:
    active = store.read().model_id
    return {
        key: {
            **record.model.model_dump(),
            "active": key == active,
            "runtime_ready": settings.runtime_image_ready(record.model.runtime),
            "source": record.source,
            "overridden": record.overridden,
            "revision": record.revision,
        }
        for key, record in registry.records().items()
    }


@app.get("/api/models-export", dependencies=[Depends(require_control)])
async def export_models() -> dict:
    return registry.export_user_catalog()


@app.post("/api/models-import", dependencies=[Depends(require_control)])
async def import_models(body: CatalogImportRequest) -> dict[str, bool]:
    if store.read().pod_id:
        raise HTTPException(status_code=409, detail="Delete the active pod before importing model settings")
    try:
        registry.import_user_catalog(body.catalog, replace=body.replace)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"ok": True}


@app.put("/api/models/{model_id}", dependencies=[Depends(require_control)])
async def save_model(model_id: str, body: ModelDefinition) -> dict[str, bool]:
    state = store.read()
    if state.pod_id and state.model_id == model_id:
        raise HTTPException(status_code=409, detail="Stop and delete the active pod before editing its model")
    try:
        registry.save_model(model_id, body)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"ok": True}


@app.delete("/api/models/{model_id}", dependencies=[Depends(require_control)])
async def delete_model(model_id: str) -> dict[str, bool]:
    state = store.read()
    if state.model_id == model_id:
        raise HTTPException(status_code=409, detail="The active model cannot be deleted")
    try:
        registry.delete_user_model(model_id)
    except KeyError as error:
        raise HTTPException(status_code=409, detail="Built-in models cannot be deleted; reset an override instead") from error
    return {"ok": True}


@app.post("/api/models/{model_id}/reset", dependencies=[Depends(require_control)])
async def reset_model(model_id: str) -> dict[str, bool]:
    state = store.read()
    if state.pod_id and state.model_id == model_id:
        raise HTTPException(status_code=409, detail="Delete the active pod before resetting its model")
    try:
        registry.reset_builtin(model_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Built-in model not found") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"ok": True}


def resolved(options: LaunchOptions):
    models = registry.models()
    if options.model_id not in models:
        raise HTTPException(status_code=404, detail="Model not found")
    model = models[options.model_id]
    if model.status == "disabled":
        raise HTTPException(status_code=409, detail="This model profile is disabled")
    runtime = registry.runtimes()[model.runtime]
    try:
        return resolve_launch(options, model, runtime, settings.datacenter_ids)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/pod/plan", dependencies=[Depends(require_control)])
async def plan(options: LaunchOptions, request: Request) -> dict:
    launch = resolved(options)
    candidates = request.app.state.runpod.create_candidates(launch)
    candidates = redact_secrets(candidates)
    return {
        "billable_actions_enabled": settings.runpod_allow_billable_actions,
        "configuration_errors": settings.live_errors(launch.profile.runtime),
        "launch": launch.model_dump(),
        "candidates": candidates,
    }


@app.post("/api/runpod/preflight", dependencies=[Depends(require_control)])
async def preflight(options: LaunchOptions, request: Request) -> dict:
    launch = resolved(options)
    try:
        pods, gpus = await asyncio.gather(
            request.app.state.runpod.list_pods(),
            asyncio.gather(*(request.app.state.runpod.get_gpu(gpu) for gpu in launch.gpu_type_ids)),
        )
    except RunpodError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {
        "billable_action_performed": False,
        "pods": redact_secrets(pods),
        "gpu_catalog": redact_secrets(gpus),
    }


@app.get("/api/status", dependencies=[Depends(require_control)])
async def status(request: Request) -> dict:
    state = store.read()
    if not state.pod_id:
        return {"pod": None, "model_id": state.model_id}
    try:
        pod = await request.app.state.runpod.get_pod(state.pod_id)
    except RunpodError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {"pod": redact_secrets(pod), "model_id": state.model_id}


@app.post("/api/pod/start", dependencies=[Depends(require_control)])
async def start(options: LaunchOptions, request: Request) -> dict:
    if not settings.runpod_allow_billable_actions:
        raise HTTPException(status_code=403, detail="Billable actions are disabled")
    launch = resolved(options)
    profile_revision = registry.records()[options.model_id].revision
    errors = settings.live_errors(launch.profile.runtime)
    if errors:
        raise HTTPException(status_code=412, detail=errors)
    if operation_lock.locked():
        raise HTTPException(status_code=409, detail="Another pod operation is running")
    async with operation_lock:
        request.app.state.last_inference = time.monotonic()
        state = store.read()
        if state.pod_id and state.model_id != options.model_id:
            raise HTTPException(status_code=409, detail="Delete the current pod before switching model/runtime")
        if state.pod_id:
            if not state.profile_revision or state.profile_revision != profile_revision:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "The model profile changed after this pod was created. Review the new plan, "
                        "then delete and recreate the pod explicitly."
                    ),
                )
            immutable_changes = []
            if options.gpu_type_id and options.gpu_type_id != state.gpu_type_id:
                immutable_changes.append("GPU")
            if options.datacenter_id and options.datacenter_id != state.datacenter_id:
                immutable_changes.append("datacenter")
            if (
                options.volume_gb
                and options.volume_gb not in {state.volume_gb, launch.profile.volume_gb}
            ):
                immutable_changes.append("volume")
            if launch.profile.runtime != state.runtime_id:
                immutable_changes.append("runtime")
            if immutable_changes:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"{', '.join(immutable_changes)} cannot be changed on the existing pod. "
                        "Delete it explicitly before creating a replacement."
                    ),
                )
        try:
            if not state.pod_id:
                pod = await request.app.state.runpod.create_pod(launch)
                state = ControllerState(
                    pod_id=pod["id"],
                    model_id=options.model_id,
                    runtime_id=launch.profile.runtime,
                    profile_revision=profile_revision,
                    gpu_type_id=pod.pop("_gpuharbor_gpu_type_id"),
                    datacenter_id=pod.pop("_gpuharbor_datacenter_id"),
                    volume_gb=launch.volume_gb,
                )
                store.write(state)
            else:
                pod = await request.app.state.runpod.get_pod(state.pod_id)
                if pod_status(pod) != "RUNNING":
                    await request.app.state.runpod.configure(state.pod_id, launch)
                    await request.app.state.runpod.start_pod(state.pod_id)
            pod = await request.app.state.runpod.wait_for_status(state.pod_id, {"RUNNING"})
        except RunpodError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        return {"pod_id": state.pod_id, "model_id": state.model_id, "status": pod_status(pod)}


@app.post("/api/pod/stop", dependencies=[Depends(require_control)])
async def stop(request: Request) -> dict:
    if operation_lock.locked():
        raise HTTPException(status_code=409, detail="Another pod operation is running")
    async with operation_lock:
        state = store.read()
        if not state.pod_id:
            raise HTTPException(status_code=404, detail="No managed pod")
        try:
            await request.app.state.runpod.stop_pod(state.pod_id)
            await request.app.state.runpod.wait_for_status(state.pod_id, {"EXITED"})
        except RunpodError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        return {"pod_id": state.pod_id, "status": "EXITED"}


@app.delete("/api/pod", dependencies=[Depends(require_control)])
async def delete_pod(request: Request) -> dict:
    if operation_lock.locked():
        raise HTTPException(status_code=409, detail="Another pod operation is running")
    async with operation_lock:
        state = store.read()
        if not state.pod_id:
            raise HTTPException(status_code=404, detail="No managed pod")
        try:
            await request.app.state.runpod.delete_pod(state.pod_id)
        except RunpodError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        store.write(ControllerState())
        return {"pod_id": state.pod_id, "status": "TERMINATED"}


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request, _: None = Depends(require_model_token)) -> Response:
    if not path or "\\" in path or any(part in {"", ".", ".."} for part in path.split("/")):
        raise HTTPException(status_code=400, detail="Invalid API path")
    maximum_bytes = settings.gpuharbor_max_request_mb * 1024 * 1024
    declared_length = request.headers.get("content-length")
    if declared_length:
        try:
            if int(declared_length) > maximum_bytes:
                raise HTTPException(status_code=413, detail="Request body is too large")
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Invalid Content-Length") from error
    body = await request.body()
    if len(body) > maximum_bytes:
        raise HTTPException(status_code=413, detail="Request body is too large")
    request.app.state.last_inference = time.monotonic()
    state = store.read()
    if not state.pod_id:
        raise HTTPException(status_code=503, detail="No model pod is configured")
    query = f"?{request.url.query}" if request.url.query else ""
    upstream_request = request.app.state.proxy.build_request(
        request.method,
        f"{proxy_url(state.pod_id)}/v1/{path}{query}",
        headers={
            "Authorization": f"Bearer {settings.runtime_gateway_token.get_secret_value()}",
            "Content-Type": request.headers.get("content-type", "application/json"),
            "Accept": request.headers.get("accept", "application/json"),
            "Accept-Encoding": "identity",
        },
        content=body,
    )
    try:
        upstream = await request.app.state.proxy.send(upstream_request, stream=True)
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail=f"Model unavailable: {error}") from error
    return StreamingResponse(
        upstream.aiter_raw(),
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type"),
        background=BackgroundTask(upstream.aclose),
    )
