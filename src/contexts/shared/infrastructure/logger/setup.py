import json
import logging
import sys

from fastapi import FastAPI
from loguru import logger

from src.settings import settings

from .middleware import log_requests
from .request_context import context_patcher

_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>{name}</magenta> | "
    "<level>{message}</level> | "
    "<dim>{extra}</dim>"
)


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _json_formatter(record: dict[str, object]) -> str:
    payload: dict[str, object] = {
        "timestamp": record["time"].isoformat(),  # type: ignore[union-attr]
        "level": record["level"].name,  # type: ignore[union-attr]
        "logger": record["name"],
        "message": record["message"],
    }
    payload.update(
        {
            key: value
            for key, value in record["extra"].items()
            if not key.startswith("_")
        }  # type: ignore[union-attr]
    )
    if record["exception"] is not None:
        payload["exception"] = str(record["exception"])
    record["extra"]["_serialized"] = json.dumps(payload, default=str)  # type: ignore[index]
    return "{extra[_serialized]}\n"


def configure_loguru(
    logger_names: list[str] | None = None,
    *,
    backtrace: bool = True,
    enqueue: bool = True,
) -> None:
    diagnose = settings.is_development

    if logger_names is None:
        for logger_name in logging.root.manager.loggerDict:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers = []
            logging_logger.propagate = True
        logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)
    else:
        for logger_name in logger_names:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers = [InterceptHandler()]
            logging_logger.propagate = False

    logger.remove()
    logger.configure(patcher=context_patcher)

    if settings.log_format == "json":
        logger.add(
            sys.stdout,
            level=settings.log_level,
            format=_json_formatter,
            backtrace=backtrace,
            diagnose=diagnose,
            enqueue=enqueue,
        )
    else:
        logger.add(
            sys.stdout,
            level=settings.log_level,
            colorize=True,
            backtrace=backtrace,
            diagnose=diagnose,
            enqueue=enqueue,
            format=_CONSOLE_FORMAT,
        )


def setup_logger(app: FastAPI) -> None:
    configure_loguru()
    app.middleware("http")(log_requests)
