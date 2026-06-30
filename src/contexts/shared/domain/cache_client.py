from abc import ABC, abstractmethod


class CacheClient(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 600) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def clear(self) -> None: ...

    @abstractmethod
    async def increment(self, key: str, ttl: int) -> int:
        """Atomically increment the counter at key, returning the new value.

        The ttl is applied only when the counter is first created, so the window
        is anchored to the first increment (fixed window).
        """
        ...
