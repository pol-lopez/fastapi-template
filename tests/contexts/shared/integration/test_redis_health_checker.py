import pytest
import redis.asyncio as redis

from src.contexts.shared.infrastructure.cache.redis_health_checker import (
    RedisHealthChecker,
)
from src.settings import settings


@pytest.mark.integration
class TestRedisHealthChecker:
    async def test_reports_healthy_when_redis_responds(self) -> None:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        checker = RedisHealthChecker(client=client)

        result = await checker.check()
        await client.aclose()

        assert result["status"] == "healthy"

    async def test_reports_unhealthy_when_redis_unavailable(self) -> None:
        client = redis.from_url(
            "redis://localhost:6390/0",
            socket_connect_timeout=0.1,
            decode_responses=True,
        )
        checker = RedisHealthChecker(client=client)

        result = await checker.check()
        await client.aclose()

        assert result["status"] == "unhealthy"
