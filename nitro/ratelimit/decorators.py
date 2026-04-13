"""
Decorator for applying rate limits to route handlers.

Works with any Python web framework — the key-extraction function is
pluggable so you can derive the rate-limit key from a request object,
user identity, API key, or any other attribute.
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Optional

from .base import RateLimiterInterface, RateLimitExceeded


def rate_limit(
    limiter: RateLimiterInterface,
    limit: int = 60,
    window: int = 60,
    key_func: Optional[Callable[..., str]] = None,
) -> Callable:
    """Decorator that enforces a rate limit on a function or route handler.

    When the limit is exceeded, :class:`RateLimitExceeded` is raised.
    The caller (or framework error handler) is responsible for
    converting it into an appropriate HTTP 429 response.

    Args:
        limiter: The rate-limiter backend to use.
        limit: Maximum number of calls allowed per *window* (default 60).
        window: Sliding-window size in seconds (default 60).
        key_func: Callable that receives the same arguments as the
            decorated function and returns a string key.  When ``None``,
            the first positional argument is used (commonly ``request``
            in web frameworks — its ``str()`` representation is hashed).

    Returns:
        A decorator that wraps the target function.

    Example::

        from nitro.ratelimit import MemoryRateLimiter, rate_limit

        limiter = MemoryRateLimiter()

        @rate_limit(limiter, limit=10, window=60,
                    key_func=lambda request: request.ip)
        async def create_post(request):
            ...

    Raises:
        RateLimitExceeded: When the rate limit is exceeded.
    """

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                key = _resolve_key(key_func, args, kwargs)
                result = limiter.hit(key, limit, window)
                if not result.allowed:
                    raise RateLimitExceeded(result)
                return await func(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                key = _resolve_key(key_func, args, kwargs)
                result = limiter.hit(key, limit, window)
                if not result.allowed:
                    raise RateLimitExceeded(result)
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator


def _resolve_key(
    key_func: Optional[Callable], args: tuple, kwargs: dict
) -> str:
    """Derive the rate-limit key from the call arguments."""
    if key_func is not None:
        return key_func(*args, **kwargs)
    # Default: use str() of first positional arg (usually a request object)
    if args:
        return str(args[0])
    return "global"
