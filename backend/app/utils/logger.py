"""
Structured JSON logger using structlog.
All pipeline steps log through this — providing full observability.
"""
import logging
import sys
import structlog
from app.core.config import settings


def configure_logging() -> None:
    log_level = logging.DEBUG if settings.ENVIRONMENT == "local" else logging.INFO

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
            if settings.ENVIRONMENT != "local"
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "medibot"):
    return structlog.get_logger(name)


logger = get_logger()
