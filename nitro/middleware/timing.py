"""
Request timing middleware.

Tracks request duration and exposes it via the ``Server-Timing`` header
and the middleware context state.
"""

from __future__ import annotations

import time
from typing import Optional

from .base import MiddlewareContext, MiddlewareInterface


class TimingMiddleware(MiddlewareInterface):
    """Track request duration and add ``Server-Timing`` header.

    The duration is stored in ``ctx.state["duration_ms"]`` for use by
    other middleware (e.g. LoggingMiddleware) and also emitted as the
    standard ``Server-Timing`` HTTP header.

    Args:
        slow_threshold: Duration in seconds above which
            ``ctx.state["is_slow"]`` is set to ``True``.  ``None``
            disables slow detection.
        header_name: The response header to set.  Defaults to
            ``"Server-Timing"`` per the W3C spec.

    Example::

        TimingMiddleware(slow_threshold=1.0)
    """

    def __init__(
        self,
        slow_threshold: Optional[float] = None,
        header_name: str = "Server-Timing",
    ) -> None:
        self.slow_threshold = slow_threshold
        self.header_name = header_name

    def before_request(self, ctx: MiddlewareContext) -> MiddlewareContext:
        ctx.state["_timing_start"] = time.monotonic()
        return ctx

    def after_response(self, ctx: MiddlewareContext) -> MiddlewareContext:
        start = ctx.state.get("_timing_start")
        if start is None:
            return ctx

        duration_s = time.monotonic() - start
        duration_ms = duration_s * 1000

        ctx.state["duration_ms"] = duration_ms
        ctx.headers[self.header_name] = f'total;dur={duration_ms:.1f};desc="Total"'

        if self.slow_threshold is not None:
            ctx.state["is_slow"] = duration_s >= self.slow_threshold

        return ctx
