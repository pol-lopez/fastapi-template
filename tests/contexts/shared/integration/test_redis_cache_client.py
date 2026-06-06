import asyncio

import pytest
import redis.asyncio as redis

from src.contexts.shared.infrastructure.cache import RedisCacheClient


@pytest.mark.integration
class TestRedisCacheClient:
    async def test_set_then_get_returns_value(
        self, redis_cache_client: RedisCacheClient
    ) -> None:
        await redis_cache_client.set("greeting", "hello")

        assert await redis_cache_client.get("greeting") == "hello"

    async def test_get_missing_key_returns_none(
        self, redis_cache_client: RedisCacheClient
    ) -> None:
        assert await redis_cache_client.get("does-not-exist") is None

    async def test_delete_removes_key(
        self, redis_cache_client: RedisCacheClient
    ) -> None:
        await redis_cache_client.set("temp", "value")

        await redis_cache_client.delete("temp")

        assert await redis_cache_client.get("temp") is None

    @pytest.mark.slow
    async def test_set_with_ttl_expires(
        self, redis_cache_client: RedisCacheClient
    ) -> None:
        await redis_cache_client.set("ephemeral", "value", ttl=1)
        assert await redis_cache_client.get("ephemeral") == "value"

        await asyncio.sleep(1.1)

        assert await redis_cache_client.get("ephemeral") is None

    async def test_clear_removes_namespaced_keys(
        self, redis_cache_client: RedisCacheClient
    ) -> None:
        await redis_cache_client.set("a", "1")
        await redis_cache_client.set("b", "2")

        await redis_cache_client.clear()

        assert await redis_cache_client.get("a") is None
        assert await redis_cache_client.get("b") is None

    async def test_get_degrades_gracefully_when_redis_unavailable(self) -> None:
        dead = redis.from_url(
            "redis://localhost:6390/0",
            socket_connect_timeout=0.1,
            decode_responses=True,
        )
        client = RedisCacheClient(client=dead, key_prefix="test-dead")

        assert await client.get("any") is None
        await client.set("any", "value")  # must not raise

        await dead.aclose()
