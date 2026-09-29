from __future__ import annotations

import time
from collections import deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


_SENSITIVE_PARTS = ("TOKEN", "KEY", "SECRET", "PASSWORD", "AUTHORIZATION")


def redact_secrets(value):
    """Recursively redact values whose field names indicate credentials."""
    if isinstance(value, dict):
        return {
            key: (
                "***"
                if any(part in str(key).upper() for part in _SENSITIVE_PARTS)
                else redact_secrets(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply browser hardening headers to the controller and API."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        if (
            request.url.path == "/"
            or request.url.path.startswith("/api/")
            or request.url.path.startswith("/docs")
        ):
            response.headers["Cache-Control"] = "no-store"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response


class LoginLimiter:
    """Small in-memory limiter that avoids an external dependency for one admin."""

    def __init__(self, maximum: int, window_seconds: int) -> None:
        self.maximum = maximum
        self.window_seconds = window_seconds
        self._failures: dict[str, deque[float]] = {}

    def _recent(self, key: str, now: float) -> deque[float]:
        attempts = self._failures.setdefault(key, deque())
        cutoff = now - self.window_seconds
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()
        return attempts

    def blocked(self, key: str, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        attempts = self._recent(key, current)
        blocked = len(attempts) >= self.maximum
        if not attempts:
            self._failures.pop(key, None)
        return blocked

    def failure(self, key: str, now: float | None = None) -> None:
        current = time.monotonic() if now is None else now
        self._recent(key, current).append(current)

    def success(self, key: str) -> None:
        self._failures.pop(key, None)
