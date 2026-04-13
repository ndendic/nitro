"""
Abstract base interface for all Nitro middleware components.

All middleware implementations must subclass ``MiddlewareInterface`` and
implement ``before_request`` and/or ``after_response``.  The pipeline
calls these hooks in order around handler execution.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MiddlewareContext:
    """Mutable context object passed through the middleware chain.

    Middleware can read/write attributes to communicate with later
    middleware or with the handler itself.

    Attributes:
        request: The raw request object (framework-specific).
        method: HTTP method (uppercase).
        path: Request path.
        headers: Mutable dict of response headers to set.
        state: Arbitrary key-value store for inter-middleware data.
        should_abort: When ``True``, the pipeline short-circuits and
            returns ``abort_status`` / ``abort_body`` without calling
            the handler.
        abort_status: HTTP status code for aborted requests.
        abort_body: Response body for aborted requests.
    """

    request: Any
    method: str = ""
    path: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
    should_abort: bool = False
    abort_status: int = 403
    abort_body: Optional[str] = None


class MiddlewareInterface(ABC):
    """Abstract base class for middleware components.

    Subclasses override ``before_request`` and/or ``after_response``.
    Both methods receive a :class:`MiddlewareContext` and may mutate it.

    Default implementations are no-ops so you only override what you need.
    """

    def before_request(self, ctx: MiddlewareContext) -> MiddlewareContext:
        """Called before the handler executes.

        May inspect/modify the context, set response headers, or abort
        the request by setting ``ctx.should_abort = True``.

        Args:
            ctx: The middleware context for this request.

        Returns:
            The (possibly modified) context.
        """
        return ctx

    def after_response(self, ctx: MiddlewareContext) -> MiddlewareContext:
        """Called after the handler executes.

        May inspect the response, add headers, log metrics, etc.

        Args:
            ctx: The middleware context for this request.

        Returns:
            The (possibly modified) context.
        """
        return ctx
