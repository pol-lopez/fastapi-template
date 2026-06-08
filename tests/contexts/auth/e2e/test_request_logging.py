import pytest
from httpx import AsyncClient
from loguru import logger

from tests.support.factories import PersistentUserFactory


def _canonical_events(records: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        r["extra"]
        for r in records
        if isinstance(r["extra"], dict) and "request_id" in r["extra"]
    ]


@pytest.mark.e2e
class TestRequestLogging:
    async def test_health_emits_canonical_wide_event(self, client: AsyncClient) -> None:
        records: list[dict[str, object]] = []
        sink_id = logger.add(lambda m: records.append(m.record), level="INFO")
        try:
            response = await client.get("/health")
        finally:
            logger.remove(sink_id)

        assert response.status_code == 200
        assert response.headers["X-Request-ID"]

        events = [e for e in _canonical_events(records) if e.get("path") == "/health"]
        assert events, "no canonical wide event emitted for /health"
        event = events[-1]
        assert event["method"] == "GET"
        assert event["status_code"] == 200
        assert event["request_id"]
        assert "duration_ms" in event
        assert event["outcome"] == "ok"

    async def test_echoes_inbound_request_id(self, client: AsyncClient) -> None:
        response = await client.get("/health", headers={"X-Request-ID": "trace-123"})

        assert response.headers["X-Request-ID"] == "trace-123"

    async def test_authenticated_request_logs_identity_not_raw_key(
        self,
        client: AsyncClient,
        user_factory: PersistentUserFactory,
    ) -> None:
        user, plain_key = await user_factory.create_with_api_key()
        records: list[dict[str, object]] = []
        sink_id = logger.add(lambda m: records.append(m.record), level="INFO")
        try:
            response = await client.get(
                "/api/v1/auth/users",
                headers={"X-API-Key": plain_key},
            )
        finally:
            logger.remove(sink_id)

        assert response.status_code == 200

        with_identity = [e for e in _canonical_events(records) if e.get("user_id")]
        assert with_identity, "identity not present in any canonical event"
        assert with_identity[-1]["user_id"] == str(user.user_id)
        assert with_identity[-1]["api_key_id"]

        assert all(plain_key not in str(r["extra"]) for r in records), (
            "raw API key leaked into a log record"
        )
