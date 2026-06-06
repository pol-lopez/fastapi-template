import time

import redis.asyncio as redis

from src.contexts.shared.domain.health_checker import HealthChecker


class RedisHealthChecker(HealthChecker):
    def __init__(self, client: redis.Redis) -> None:
        self.client = client

    async def check(self) -> dict[str, object]:
        try:
            start = time.perf_counter()
            await self.client.ping()
            latency = (time.perf_counter() - start) * 1000
            return {"status": "healthy", "latency_ms": round(latency, 2)}
        except Exception:
            return {"status": "unhealthy", "latency_ms": 0}
