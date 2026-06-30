import time
from uuid import uuid4

import psutil
from loguru import logger
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.settings import settings

from .request_context import bind_context, get_context, init_context, reset_context

REQUEST_ID_HEADER = "X-Request-ID"


def _level_for_status(status_code: int) -> str:
    if status_code >= 500:  # noqa: PLR2004
        return "ERROR"
    if status_code >= 400:  # noqa: PLR2004
        return "WARNING"
    return "INFO"


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = headers.get(REQUEST_ID_HEADER) or str(uuid4())
        client = scope.get("client")
        token = init_context(
            request_id=request_id,
            method=scope["method"],
            path=scope["path"],
            client_ip=client[0] if client else "unknown",
            user_agent=headers.get("user-agent", ""),
        )

        process = psutil.Process() if settings.is_development else None
        start_ram = process.memory_info().rss / 1024 / 1024 if process else 0.0
        start_time = time.perf_counter()

        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = MutableHeaders(scope=message)
                response_headers[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            outcome = "ok" if status_code < 500 else "error"  # noqa: PLR2004
            bind_context(
                status_code=status_code,
                duration_ms=duration_ms,
                outcome=outcome,
            )
            route = scope.get("route")
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
            reset_context(token)
