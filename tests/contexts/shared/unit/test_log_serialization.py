import json

import pytest
from loguru import logger

from src.contexts.shared.infrastructure.logger.middleware import _level_for_status
from src.contexts.shared.infrastructure.logger.setup import _json_formatter


@pytest.mark.unit
class TestJsonFormatter:
    def test_emits_flat_json_with_core_fields_and_extra(self) -> None:
        captured: list[str] = []
        sink_id = logger.add(captured.append, level="INFO", format=_json_formatter)
        try:
            logger.bind(request_id="r1", user_id="u1").info("hello")
        finally:
            logger.remove(sink_id)

        payload = json.loads(captured[0])
        assert payload["message"] == "hello"
        assert payload["level"] == "INFO"
        assert payload["request_id"] == "r1"
        assert payload["user_id"] == "u1"
        assert "timestamp" in payload
        assert "logger" in payload


@pytest.mark.unit
class TestLevelForStatus:
    def test_5xx_maps_to_error(self) -> None:
        assert _level_for_status(500) == "ERROR"
        assert _level_for_status(503) == "ERROR"

    def test_4xx_maps_to_warning(self) -> None:
        assert _level_for_status(400) == "WARNING"
        assert _level_for_status(404) == "WARNING"

    def test_2xx_3xx_maps_to_info(self) -> None:
        assert _level_for_status(200) == "INFO"
        assert _level_for_status(302) == "INFO"
