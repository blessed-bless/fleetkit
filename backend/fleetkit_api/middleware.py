from __future__ import annotations

import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fleetkit_api.services.rate_limit import rate_limiter


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.1f}"
        return response


class AgentRateLimitMiddleware(BaseHTTPMiddleware):
    """Throttle agent endpoints per API key (best-effort, in-memory)."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not request.url.path.startswith("/api/v1/agent/"):
            return await call_next(request)
        key = request.headers.get("X-FleetKit-Key") or request.client.host if request.client else "anon"
        # 120 claim/log/metric calls per minute per key is plenty for solo fleets
        if not rate_limiter.allow(f"agent:{key}", limit=120, window_seconds=60):
            return Response(
                content='{"detail":"rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(
            rate_limiter.remaining(f"agent:{key}", limit=120, window_seconds=60)
        )
        return response
