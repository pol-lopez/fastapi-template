from collections.abc import AsyncGenerator

import pytest
import redis.asyncio as redis

from src.contexts.shared.infrastructure.cache import RedisCacheClient
from src.settings import settings

TEST_KEY_PREFIX = "test-fastapi-template"


@pytest.fixture
async def redis_client() -> AsyncGenerator[redis.Redis]:
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        async for key in client.scan_iter(match=f"{TEST_KEY_PREFIX}:*"):
            await client.delete(key)
        await client.aclose()


@pytest.fixture
def redis_cache_client(redis_client: redis.Redis) -> RedisCacheClient:
    return RedisCacheClient(client=redis_client, key_prefix=TEST_KEY_PREFIX)
