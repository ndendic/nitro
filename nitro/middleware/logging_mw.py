"""
Request logging middleware.

Logs request method, path, and response timing using the standard
``logging`` module.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from .base import MiddlewareContext, MiddlewareInterface


class LoggingMiddleware(MiddlewareInterface):
    """Log every request with method, path, and duration.

    Uses Python's standard ``logging`` module.  The logger name defaults
    to ``"nitro.middleware.request"`` but is configurable.

    Args:
        logger_name: Name of the logger to use.
        level: Logging level for normal requests (default ``INFO``).
        slow_level: Logging level for slow requests (default ``WARNING``).
        slow_threshold: Seconds above which a request is logged at
            *slow_level*.  ``None`` disables slow-request detection.
        log_headers: Whether to include request headers in log output.

    Example::

        LoggingMiddleware(slow_threshold=2.0, log_headers=True)
    """

    def __init__(
        self,
        logger_name: str = "nitro.middleware.request",
        level: int = logging.INFO,
        slow_level: int = logging.WARNING,
        slow_threshold: Optional[float] = None,
        log_headers: bool = False,
    ) -> None:
        self.logger = logging.getLogger(logger_name)
        self.level = level
        self.slow_level = slow_level
        self.slow_threshold = slow_threshold
        self.log_headers = log_headers

    def before_request(self, ctx: MiddlewareContext) -> MiddlewareContext:
        ctx.state["_logging_start"] = time.monotonic()
        return ctx

    def after_response(self, ctx: MiddlewareContext) -> MiddlewareContext:
        start = ctx.state.get("_logging_start")
        duration_ms = (time.monotonic() - start) * 1000 if start else 0

        msg = f"{ctx.method} {ctx.path} — {duration_ms:.1f}ms"

        if self.log_headers and hasattr(ctx.request, "headers"):
            msg += f" headers={dict(ctx.request.headers)}"

        # Pick log level based on duration
        level = self.level
        if self.slow_threshold is not None and start:
            duration_s = duration_ms / 1000
            if duration_s >= self.slow_threshold:
                level = self.slow_level
                msg += " [SLOW]"

        self.logger.log(level, msg)
        return ctx
