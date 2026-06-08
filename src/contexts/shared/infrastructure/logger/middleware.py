import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import psutil
from fastapi import Request, Response
from loguru import logger

from src.settings import settings

from .request_context import bind_context, get_context, init_context, reset_context

REQUEST_ID_HEADER = "X-Request-ID"


def _level_for_status(status_code: int) -> str:
    if status_code >= 500:  # noqa: PLR2004
        return "ERROR"
    if status_code >= 400:  # noqa: PLR2004
        return "WARNING"
    return "INFO"


async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
    token = init_context(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )

    process = psutil.Process() if settings.is_development else None
    start_ram = process.memory_info().rss / 1024 / 1024 if process else 0.0
    start_time = time.perf_counter()

    status_code = 500
    response: Response | None = None
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        outcome = "ok" if status_code < 500 else "error"  # noqa: PLR2004
        bind_context(
            status_code=status_code,
            duration_ms=duration_ms,
            outcome=outcome,
        )
        route = request.scope.get("route")
        route_path = getattr(route, "path", None)
        if route_path:
            bind_context(route=route_path)
        if process is not None:
            end_ram = process.memory_info().rss / 1024 / 1024
            bind_context(
                ram_start_mb=round(start_ram, 2),
                ram_end_mb=round(end_ram, 2),
                ram_delta_mb=round(end_ram - start_ram, 2),
            )
        context = get_context()
        logger.log(
            _level_for_status(status_code),
            "{method} {path} -> {status_code} ({duration_ms}ms)",
            method=context["method"],
            path=context["path"],
            status_code=status_code,
            duration_ms=duration_ms,
        )
        if response is not None:
            response.headers[REQUEST_ID_HEADER] = request_id
        reset_context(token)
