import time
from collections.abc import Callable
from dataclasses import dataclass

from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.contexts.shared.domain.cache_client import CacheClient


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    reset_at: int
    retry_after: int


class RateLimiter:
    """Fixed-window rate limiter backed by a shared CacheClient.

    The counter lives in the cache (Redis in production), so the limit is shared
    across gunicorn workers and replicas — an in-memory per-process counter would
    let each worker allow the full quota independently.
    """

    def __init__(
        self, cache: CacheClient, max_requests: int, window_seconds: int
    ) -> None:
        self._cache = cache
        self._max_requests = max_requests
        self._window_seconds = window_seconds

    async def hit(self, client_id: str) -> RateLimitDecision:
        count = await self._cache.increment(
            f"ratelimit:{client_id}", ttl=self._window_seconds
        )
        # count == 0 means the cache failed (degraded) — fail open.
        allowed = count == 0 or count <= self._max_requests
        return RateLimitDecision(
            allowed=allowed,
            remaining=max(0, self._max_requests - count),
            reset_at=int(time.time()) + self._window_seconds,
            retry_after=self._window_seconds,
        )


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        cache_provider: Callable[[], CacheClient],
        max_requests: int,
        window_seconds: int,
        exclude_paths: list[str],
    ) -> None:
        self.app = app
        self._cache_provider = cache_provider
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.exclude_paths = set(exclude_paths)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in self.exclude_paths:
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        client_id = client[0] if client else "unknown"
        limiter = RateLimiter(
            self._cache_provider(), self.max_requests, self.window_seconds
        )
        decision = await limiter.hit(client_id)

        if not decision.allowed:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"},
                headers={
                    "Retry-After": str(decision.retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(decision.reset_at),
                },
            )
            await response(scope, receive, send)
            return

        async def send_with_rate_limit_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-RateLimit-Limit"] = str(self.max_requests)
                headers["X-RateLimit-Remaining"] = str(decision.remaining)
                headers["X-RateLimit-Reset"] = str(decision.reset_at)
            await send(message)

        await self.app(scope, receive, send_with_rate_limit_headers)
