"""
Decorators for automatic metric collection.

Provides ``@timed`` for measuring function/method duration and
``@counted`` for tracking invocations.
"""

from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Callable, Optional, TypeVar

from .base import Counter, Histogram

F = TypeVar("F", bound=Callable[..., Any])


def timed(
    histogram: Histogram,
    **static_labels: str,
) -> Callable[[F], F]:
    """Decorator that records function execution time in a histogram.

    Example::

        from nitro.metrics import Histogram, timed

        duration = Histogram("handler_duration_seconds", "Handler duration")

        @timed(duration, handler="index")
        async def index(request):
            ...
    """

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.monotonic()
                try:
                    return await func(*args, **kwargs)
                finally:
                    elapsed = time.monotonic() - start
                    histogram.observe(elapsed, **static_labels)

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.monotonic()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = time.monotonic() - start
                    histogram.observe(elapsed, **static_labels)

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def counted(
    counter: Counter,
    **static_labels: str,
) -> Callable[[F], F]:
    """Decorator that increments a counter on each invocation.

    Example::

        from nitro.metrics import Counter, counted

        calls = Counter("handler_calls_total", "Handler call count")

        @counted(calls, handler="index")
        def index(request):
            ...
    """

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                counter.inc(**static_labels)
                return await func(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                counter.inc(**static_labels)
                return func(*args, **kwargs)

            return sync_wrapper  # type: ignore[return-value]

    return decorator
