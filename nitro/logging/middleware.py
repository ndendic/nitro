from __future__ import annotations

import logging as _logging
import time
import uuid
from typing import Any

from nitro.logging.context import set_correlation_id, correlation_id, clear_context

_logger = _logging.getLogger("nitro.middleware")


class LoggingMiddleware:
    """Sanic middleware that instruments every HTTP request/response.

    - Extracts or generates a correlation ID from the ``X-Request-ID`` header.
    - Logs request arrival and response completion with duration.
    - Propagates ``X-Request-ID`` back to the client in the response headers.
    """

    def __init__(self, logger: _logging.Logger | None = None) -> None:
        self._logger = logger or _logger

    # ------------------------------------------------------------------
    # Internal handlers (called by Sanic middleware hooks)
    # ------------------------------------------------------------------

    async def on_request(self, request: Any) -> None:
        """Called before the route handler."""
        clear_context()

        # Prefer an existing ID sent by the caller
        cid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        set_correlation_id(cid)

        # Store start time on the request object for duration calculation
        request.ctx.nitro_start = time.time()
        request.ctx.nitro_correlation_id = cid

        self._logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.path,
                "correlation_id": cid,
            },
        )

    async def on_response(self, request: Any, response: Any) -> Any:
        """Called after the route handler returns a response."""
        cid = getattr(getattr(request, "ctx", None), "nitro_correlation_id", correlation_id())
        start = getattr(getattr(request, "ctx", None), "nitro_start", time.time())
        duration_ms = round((time.time() - start) * 1000, 2)

        response.headers["X-Request-ID"] = cid

        self._logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status,
                "duration_ms": duration_ms,
                "correlation_id": cid,
            },
        )
        return response

    async def on_error(self, request: Any, exception: Exception) -> None:
        """Log an unhandled error."""
        cid = getattr(getattr(request, "ctx", None), "nitro_correlation_id", correlation_id())
        self._logger.error(
            "Request failed",
            extra={
                "method": getattr(request, "method", "UNKNOWN"),
                "path": getattr(request, "path", "/"),
                "correlation_id": cid,
            },
            exc_info=exception,
        )


def request_logging_middleware(app: Any, logger: _logging.Logger | None = None) -> LoggingMiddleware:
    """Attach LoggingMiddleware to a Sanic app.

    Usage::

        from sanic import Sanic
        from nitro.logging.middleware import request_logging_middleware

        app = Sanic("MyApp")
        request_logging_middleware(app)
    """
    mw = LoggingMiddleware(logger=logger)

    @app.middleware("request")
    async def _on_request(request: Any) -> None:
        await mw.on_request(request)

    @app.middleware("response")
    async def _on_response(request: Any, response: Any) -> Any:
        return await mw.on_response(request, response)

    return mw
