from __future__ import annotations

import secrets
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


def secure_equals(expected: str, supplied: str | None) -> bool:
    """Constant-time comparison that never raises and never accepts an empty secret.

    ``secrets.compare_digest`` raises ``TypeError`` for non-ASCII ``str`` input,
    which would turn a crafted header into a 500 instead of a 401.
    """
    if not expected or not supplied:
        return False
    return secrets.compare_digest(expected.encode("utf-8"), supplied.encode("utf-8"))


def bearer_token(authorization: str | None) -> str:
    """Return the token of an ``Authorization: Bearer`` header, or an empty string."""
    if authorization and authorization[:7].lower() == "bearer ":
        return authorization[7:].strip()
    return ""


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
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; "
            "form-action 'self'"
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


class SessionRegistry:
    """Server-side list of live sessions so logout really revokes a cookie.

    Session cookies are signed but stateless; without this a copied cookie would
    stay valid until it expires. State is in memory, so a restart signs everyone out.
    """

    def __init__(self, lifetime_seconds: int) -> None:
        self.lifetime_seconds = lifetime_seconds
        self._live: dict[str, float] = {}

    def _prune(self, now: float) -> None:
        for sid in [sid for sid, expires in self._live.items() if expires <= now]:
            del self._live[sid]

    def create(self) -> str:
        now = time.monotonic()
        self._prune(now)
        sid = secrets.token_urlsafe(24)
        self._live[sid] = now + self.lifetime_seconds
        return sid

    def valid(self, sid: object) -> bool:
        if not isinstance(sid, str):
            return False
        expires = self._live.get(sid)
        if expires is None or expires <= time.monotonic():
            self._live.pop(sid, None)
            return False
        return True

    def revoke(self, sid: object) -> None:
        if isinstance(sid, str):
            self._live.pop(sid, None)
