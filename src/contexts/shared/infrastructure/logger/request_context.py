from __future__ import annotations

from contextvars import ContextVar, Token

_request_context: ContextVar[dict[str, object] | None] = ContextVar(
    "request_context",
    default=None,
)


def init_context(**fields: object) -> Token[dict[str, object] | None]:
    return _request_context.set(dict(fields))


def bind_context(**fields: object) -> None:
    # Mutate in place — never reassign the ContextVar mid-request. The middleware
    # seeds the dict; downstream layers running in BaseHTTPMiddleware child tasks
    # (which get their own ContextVar copy) add to the same object, so the middleware
    # still sees their fields at emit time. Reassigning here would break that.
    context = _request_context.get()
    if context is None:
        return
    context.update(fields)


def get_context() -> dict[str, object]:
    context = _request_context.get()
    return context if context is not None else {}


def reset_context(token: Token[dict[str, object] | None]) -> None:
    _request_context.reset(token)


def context_patcher(record: dict[str, object]) -> None:
    extra = record["extra"]
    extra.update(get_context())  # type: ignore[union-attr]
