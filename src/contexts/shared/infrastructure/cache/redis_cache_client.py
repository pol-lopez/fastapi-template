import redis.asyncio as redis
from loguru import logger
from redis.exceptions import RedisError

from src.contexts.shared.domain.cache_client import CacheClient


class RedisCacheClient(CacheClient):
    def __init__(
        self, client: redis.Redis, key_prefix: str = "fastapi-template"
    ) -> None:
        self._client = client
        self._key_prefix = key_prefix

    def _namespaced(self, key: str) -> str:
        return f"{self._key_prefix}:{key}"

    async def get(self, key: str) -> str | None:
        try:
            return await self._client.get(self._namespaced(key))
        except RedisError as exc:
            logger.warning("Redis get failed for key {}: {}", key, exc)
            return None

    async def set(self, key: str, value: str, ttl: int = 600) -> None:
        try:
            await self._client.set(self._namespaced(key), value, ex=ttl)
        except RedisError as exc:
            logger.warning("Redis set failed for key {}: {}", key, exc)

    async def delete(self, key: str) -> None:
        try:
            await self._client.delete(self._namespaced(key))
        except RedisError as exc:
            logger.warning("Redis delete failed for key {}: {}", key, exc)

    async def clear(self) -> None:
        try:
            async for redis_key in self._client.scan_iter(
                match=f"{self._key_prefix}:*"
            ):
                await self._client.delete(redis_key)
        except RedisError as exc:
            logger.warning("Redis clear failed: {}", exc)

    async def increment(self, key: str, ttl: int) -> int:
        try:
            namespaced = self._namespaced(key)
            async with self._client.pipeline(transaction=True) as pipe:
                pipe.incr(namespaced)
                pipe.expire(namespaced, ttl, nx=True)
                results = await pipe.execute()
            return int(results[0])
        except RedisError as exc:
            logger.warning("Redis increment failed for key {}: {}", key, exc)
            return 0
