import asyncio

import pytest

from src.contexts.shared.infrastructure.cache import InMemoryCacheClient
from src.contexts.shared.infrastructure.http.rate_limit_middleware import RateLimiter


@pytest.mark.unit
class TestRateLimiter:
    async def test_allows_requests_under_limit(self) -> None:
        limiter = RateLimiter(InMemoryCacheClient(), max_requests=5, window_seconds=60)

        for _ in range(5):
            assert (await limiter.hit("192.168.1.1")).allowed is True

    async def test_blocks_requests_over_limit(self) -> None:
        limiter = RateLimiter(InMemoryCacheClient(), max_requests=3, window_seconds=60)

        for _ in range(3):
            await limiter.hit("10.0.0.1")

        assert (await limiter.hit("10.0.0.1")).allowed is False

    async def test_separate_limits_per_client(self) -> None:
        limiter = RateLimiter(InMemoryCacheClient(), max_requests=2, window_seconds=60)

        await limiter.hit("1.1.1.1")
        await limiter.hit("1.1.1.1")
        assert (await limiter.hit("1.1.1.1")).allowed is False

        assert (await limiter.hit("2.2.2.2")).allowed is True

    async def test_remaining_decrements(self) -> None:
        limiter = RateLimiter(InMemoryCacheClient(), max_requests=5, window_seconds=60)

        assert (await limiter.hit("10.0.0.1")).remaining == 4
        assert (await limiter.hit("10.0.0.1")).remaining == 3

    async def test_window_resets_after_expiry(self) -> None:
        limiter = RateLimiter(InMemoryCacheClient(), max_requests=1, window_seconds=1)

        assert (await limiter.hit("172.16.0.1")).allowed is True
        assert (await limiter.hit("172.16.0.1")).allowed is False

        await asyncio.sleep(1.1)

        assert (await limiter.hit("172.16.0.1")).allowed is True

    async def test_fails_open_when_cache_degraded(self) -> None:
        class DegradedCache(InMemoryCacheClient):
            async def increment(self, key: str, ttl: int) -> int:  # noqa: ARG002
                return 0  # mimic Redis being down (RedisCacheClient returns 0)

        limiter = RateLimiter(DegradedCache(), max_requests=1, window_seconds=60)

        assert (await limiter.hit("x")).allowed is True
        assert (await limiter.hit("x")).allowed is True
