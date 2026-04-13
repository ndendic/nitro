"""
Composable middleware pipeline.

Chains multiple :class:`MiddlewareInterface` implementations and runs
their hooks in order around a request/response cycle.
"""

from __future__ import annotations

from typing import Any

from .base import MiddlewareContext, MiddlewareInterface


class Pipeline:
    """Ordered chain of middleware components.

    Middleware is executed in insertion order for ``before_request`` and
    in **reverse** order for ``after_response`` (onion model).

    Usage::

        pipeline = Pipeline(
            CORSMiddleware(allow_origins=["*"]),
            SecurityMiddleware(),
            TimingMiddleware(slow_threshold=1.0),
        )

        # Framework integration calls these automatically:
        ctx = pipeline.before(request)
        # ... handler ...
        ctx = pipeline.after(ctx)

    Args:
        *middleware: Middleware instances to include in the chain.
    """

    def __init__(self, *middleware: MiddlewareInterface) -> None:
        self._middleware: list[MiddlewareInterface] = list(middleware)

    def add(self, mw: MiddlewareInterface) -> "Pipeline":
        """Append a middleware to the chain. Returns self for chaining."""
        self._middleware.append(mw)
        return self

    def before(self, request: Any, method: str = "", path: str = "") -> MiddlewareContext:
        """Run all ``before_request`` hooks in order.

        Args:
            request: The raw framework request object.
            method: HTTP method (uppercase). Extracted from request if empty
                and request has a ``method`` attribute.
            path: Request path. Extracted from request if empty and request
                has a ``path`` attribute.

        Returns:
            A :class:`MiddlewareContext` populated by the middleware chain.
        """
        if not method and hasattr(request, "method"):
            method = str(request.method).upper()
        if not path and hasattr(request, "path"):
            path = str(request.path)

        ctx = MiddlewareContext(request=request, method=method, path=path)

        for mw in self._middleware:
            ctx = mw.before_request(ctx)
            if ctx.should_abort:
                break

        return ctx

    def after(self, ctx: MiddlewareContext) -> MiddlewareContext:
        """Run all ``after_response`` hooks in reverse order (onion model).

        Args:
            ctx: The context returned by :meth:`before`.

        Returns:
            The (possibly modified) context.
        """
        for mw in reversed(self._middleware):
            ctx = mw.after_response(ctx)

        return ctx

    def __len__(self) -> int:
        return len(self._middleware)

    def __repr__(self) -> str:
        names = [type(mw).__name__ for mw in self._middleware]
        return f"Pipeline({', '.join(names)})"
