import pytest

from src.contexts.shared.infrastructure.logger.request_context import (
    bind_context,
    context_patcher,
    get_context,
    init_context,
    reset_context,
)


@pytest.mark.unit
class TestRequestContext:
    def test_get_context_is_empty_without_init(self) -> None:
        assert get_context() == {}

    def test_bind_context_mutates_current_context_in_place(self) -> None:
        token = init_context(request_id="r1")
        live_reference = get_context()

        bind_context(user_id="u1")

        assert live_reference == {"request_id": "r1", "user_id": "u1"}
        reset_context(token)

    def test_reset_context_clears_context(self) -> None:
        token = init_context(request_id="r1")
        reset_context(token)

        assert get_context() == {}

    def test_bind_context_is_noop_without_init(self) -> None:
        bind_context(user_id="u1")

        assert get_context() == {}

    def test_context_patcher_merges_context_into_record_extra(self) -> None:
        token = init_context(request_id="r1")
        bind_context(user_id="u1")
        record: dict[str, object] = {"extra": {}}

        context_patcher(record)

        assert record["extra"] == {"request_id": "r1", "user_id": "u1"}
        reset_context(token)
