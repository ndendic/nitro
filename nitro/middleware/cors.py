"""
CORS (Cross-Origin Resource Sharing) middleware.

Adds CORS headers to responses and handles preflight OPTIONS requests.
"""

from __future__ import annotations

from typing import Sequence

from .base import MiddlewareContext, MiddlewareInterface


class CORSMiddleware(MiddlewareInterface):
    """Add CORS headers to every response.

    Handles preflight ``OPTIONS`` requests by short-circuiting with a
    204 response containing the appropriate headers.

    Args:
        allow_origins: Allowed origin patterns.  ``["*"]`` permits all.
        allow_methods: HTTP methods to advertise in preflight responses.
        allow_headers: Request headers the client may send.
        expose_headers: Response headers the client may read.
        allow_credentials: Whether to include
            ``Access-Control-Allow-Credentials: true``.
        max_age: Preflight cache duration in seconds.

    Example::

        CORSMiddleware(
            allow_origins=["https://app.example.com"],
            allow_credentials=True,
            max_age=3600,
        )
    """

    def __init__(
        self,
        allow_origins: Sequence[str] = ("*",),
        allow_methods: Sequence[str] = ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"),
        allow_headers: Sequence[str] = ("Content-Type", "Authorization", "X-Requested-With"),
        expose_headers: Sequence[str] = (),
        allow_credentials: bool = False,
        max_age: int = 86400,
    ) -> None:
        self.allow_origins = list(allow_origins)
        self.allow_methods = list(allow_methods)
        self.allow_headers = list(allow_headers)
        self.expose_headers = list(expose_headers)
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def _origin_allowed(self, origin: str) -> bool:
        """Check whether *origin* matches the allow list."""
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins

    def _get_request_origin(self, ctx: MiddlewareContext) -> str:
        """Extract the Origin header from the request."""
        request = ctx.request
        if hasattr(request, "headers") and hasattr(request.headers, "get"):
            return request.headers.get("origin", "")
        if isinstance(request, dict):
            headers = request.get("headers", {})
            if isinstance(headers, dict):
                return headers.get("origin", headers.get("Origin", ""))
        return ""

    def before_request(self, ctx: MiddlewareContext) -> MiddlewareContext:
        origin = self._get_request_origin(ctx)

        if origin and self._origin_allowed(origin):
            # Use the actual origin (not "*") when credentials are enabled
            allowed_origin = origin if self.allow_credentials else (
                origin if "*" not in self.allow_origins else "*"
            )
            ctx.headers["Access-Control-Allow-Origin"] = allowed_origin

            if self.allow_credentials:
                ctx.headers["Access-Control-Allow-Credentials"] = "true"

            if self.expose_headers:
                ctx.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)

        # Handle preflight
        if ctx.method == "OPTIONS" and origin:
            ctx.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            ctx.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            ctx.headers["Access-Control-Max-Age"] = str(self.max_age)
            ctx.should_abort = True
            ctx.abort_status = 204
            ctx.abort_body = ""

        return ctx
