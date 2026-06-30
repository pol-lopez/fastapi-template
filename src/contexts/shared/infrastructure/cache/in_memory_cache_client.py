import asyncio
from datetime import UTC, datetime, timedelta

from src.contexts.shared.domain.cache_client import CacheClient


class InMemoryCacheClient(CacheClient):
    def __init__(self) -> None:
        self._cache: dict[str, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: str, ttl: int = 600) -> None:
        async with self._lock:
            expires_at = (datetime.now(tz=UTC) + timedelta(seconds=ttl)).timestamp()
            self._cache[key] = (value, expires_at)

    async def get(self, key: str) -> str | None:
        async with self._lock:
            item = self._cache.get(key)
            if item:
                value, expires_at = item
                if expires_at > datetime.now(tz=UTC).timestamp():
                    return value
                self._cache.pop(key, None)
            return None

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()

    async def increment(self, key: str, ttl: int) -> int:
        async with self._lock:
            now = datetime.now(tz=UTC).timestamp()
            item = self._cache.get(key)
            if item and item[1] > now:
                count = int(item[0]) + 1
                expires_at = item[1]
            else:
                count = 1
                expires_at = (datetime.now(tz=UTC) + timedelta(seconds=ttl)).timestamp()
            self._cache[key] = (str(count), expires_at)
            return count
