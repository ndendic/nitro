"""
Sanic framework integration for the middleware pipeline.

Registers the pipeline as Sanic request/response middleware so the
hooks run automatically on every request.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pipeline import Pipeline

try:
    from sanic import Sanic, Request
    from sanic.response import text as sanic_text

    SANIC_AVAILABLE = True
except ImportError:
    SANIC_AVAILABLE = False


def sanic_middleware(app: "Sanic", pipeline: "Pipeline") -> None:
    """Attach a :class:`Pipeline` to a Sanic application.

    Registers ``on_request`` and ``on_response`` listeners that run the
    pipeline's ``before`` / ``after`` hooks on every HTTP request.

    When a middleware sets ``ctx.should_abort = True`` during the
    ``before`` phase, the handler is skipped and an immediate response
    is returned with the abort status and body.

    Response headers accumulated in ``ctx.headers`` are merged into the
    Sanic response.

    Args:
        app: The Sanic application instance.
        pipeline: A :class:`Pipeline` of middleware to apply.

    Raises:
        ImportError: If Sanic is not installed.

    Example::

        from sanic import Sanic
        from nitro.middleware import Pipeline, CORSMiddleware, sanic_middleware

        app = Sanic("MyApp")
        sanic_middleware(app, Pipeline(CORSMiddleware()))
    """
    if not SANIC_AVAILABLE:
        raise ImportError("Sanic is required. Install with: pip install sanic")

    @app.on_request
    async def middleware_before(request: Request):
        method = request.method
        path = request.path
        ctx = pipeline.before(request, method=method, path=path)

        # Stash the context on the request for the response middleware
        request.ctx.middleware_ctx = ctx

        if ctx.should_abort:
            response = sanic_text(
                ctx.abort_body or "",
                status=ctx.abort_status,
            )
            # Apply headers from the pipeline to the abort response
            for key, value in ctx.headers.items():
                response.headers[key] = value
            return response

    @app.on_response
    async def middleware_after(request: Request, response):
        ctx = getattr(request.ctx, "middleware_ctx", None)
        if ctx is None:
            return response

        ctx = pipeline.after(ctx)

        # Merge pipeline headers into the response
        for key, value in ctx.headers.items():
            response.headers[key] = value

        return response
