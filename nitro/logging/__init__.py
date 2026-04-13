"""nitro.logging — Structured JSON logging with request correlation IDs.

Quick-start::

    from nitro.logging import configure_logging, get_logger

    configure_logging(level="DEBUG", pretty=True)
    log = get_logger("myapp")
    log.info("Server starting")
"""
from __future__ import annotations

from nitro.logging.context import (
    RequestContext,
    clear_context,
    correlation_id,
    set_correlation_id,
)
from nitro.logging.config import configure_logging, get_logger
from nitro.logging.decorators import log_action
from nitro.logging.filters import CorrelationFilter
from nitro.logging.formatters import JsonFormatter, PrettyFormatter
from nitro.logging.middleware import LoggingMiddleware, request_logging_middleware

__all__ = [
    # Core
    "configure_logging",
    "get_logger",
    # Context
    "RequestContext",
    "correlation_id",
    "set_correlation_id",
    "clear_context",
    # Formatters
    "JsonFormatter",
    "PrettyFormatter",
    # Filters
    "CorrelationFilter",
    # Middleware
    "LoggingMiddleware",
    "request_logging_middleware",
    # Decorators
    "log_action",
]
