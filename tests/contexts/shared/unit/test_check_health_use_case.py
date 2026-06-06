import pytest

from src.contexts.shared.application.use_cases.check_health import (
    CheckHealthUseCase,
)
from src.contexts.shared.domain.health_checker import HealthChecker


class FakeHealthyChecker(HealthChecker):
    async def check(self) -> dict[str, object]:
        return {"status": "healthy", "latency_ms": 1.5}


class FakeUnhealthyChecker(HealthChecker):
    async def check(self) -> dict[str, object]:
        return {"status": "unhealthy", "latency_ms": 0}


@pytest.mark.unit
class TestCheckHealthUseCase:
    async def test_returns_healthy_when_all_components_respond(self) -> None:
        use_case = CheckHealthUseCase(
            database_checker=FakeHealthyChecker(),
            cache_checker=FakeHealthyChecker(),
        )

        result = await use_case.execute()

        assert result.status == "healthy"
        assert result.components["database"]["status"] == "healthy"
        assert result.components["cache"]["status"] == "healthy"

    async def test_returns_unhealthy_when_db_fails(self) -> None:
        use_case = CheckHealthUseCase(
            database_checker=FakeUnhealthyChecker(),
            cache_checker=FakeHealthyChecker(),
        )

        result = await use_case.execute()

        assert result.status == "unhealthy"
        assert result.components["database"]["status"] == "unhealthy"

    async def test_stays_healthy_when_only_cache_fails(self) -> None:
        use_case = CheckHealthUseCase(
            database_checker=FakeHealthyChecker(),
            cache_checker=FakeUnhealthyChecker(),
        )

        result = await use_case.execute()

        assert result.status == "healthy"
        assert result.components["cache"]["status"] == "unhealthy"
