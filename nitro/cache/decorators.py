"""
Caching decorators for the Nitro framework.

Provides:
- ``cached``           : Decorator that caches sync and async function results.
- ``cache_invalidate`` : Helper for manual cache invalidation by key pattern.
"""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable, Optional

from .base import CacheInterface


def _default_key_func(func: Callable, args: tuple, kwargs: dict) -> str:
    """Generate a deterministic cache key from the function and its arguments.

    Format: ``{module}.{qualname}:{args!r}:{sorted_kwargs!r}``

    Args:
        func: The decorated callable.
        args: Positional arguments passed to *func*.
        kwargs: Keyword arguments passed to *func*.

    Returns:
        Cache key string.
    """
    sorted_kwargs = sorted(kwargs.items())
    return f"{func.__module__}.{func.__qualname__}:{args!r}:{sorted_kwargs!r}"


def cached(
    cache: CacheInterface,
    ttl: Optional[int] = None,
    key_func: Optional[Callable[[Callable, tuple, dict], str]] = None,
) -> Callable:
    """Decorator that caches function return values in a cache backend.

    Works transparently with both regular and ``async`` functions.

    On each invocation:
    1. Compute the cache key (via *key_func* or the default).
    2. Return the cached value if present.
    3. Otherwise call the original function, store the result, and return it.

    Args:
        cache: Cache backend instance (any ``CacheInterface`` implementation).
        ttl: Time-to-live in seconds.  Overrides the cache's ``default_ttl``.
            Pass ``None`` to rely on the backend default.
        key_func: Custom key generator with signature
            ``(func, args, kwargs) -> str``.  Defaults to
            ``"{module}.{qualname}:{args!r}:{sorted_kwargs!r}"``.

    Returns:
        The decorated function.

    Example::

        cache = MemoryCache(default_ttl=300)

        @cached(cache, ttl=120)
        def fetch_user(user_id: int) -> dict:
            return db.query(user_id)

        @cached(cache, ttl=60)
        async def fetch_orders(user_id: int) -> list:
            return await db.query_orders(user_id)

        # Custom key function
        @cached(cache, key_func=lambda f, a, kw: f"user:{a[0]}")
        def get_profile(user_id: int) -> dict:
            ...
    """
    _key_func = key_func or _default_key_func

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                key = _key_func(func, args, kwargs)
                cached_value = cache.get(key)
                if cached_value is not None:
                    return cached_value
                result = await func(*args, **kwargs)
                if result is not None:
                    cache.set(key, result, ttl=ttl)
                return result

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                key = _key_func(func, args, kwargs)
                cached_value = cache.get(key)
                if cached_value is not None:
                    return cached_value
                result = func(*args, **kwargs)
                if result is not None:
                    cache.set(key, result, ttl=ttl)
                return result

            return sync_wrapper

    return decorator


def cache_invalidate(cache: CacheInterface, *keys: str) -> int:
    """Manually invalidate one or more cache keys.

    Convenience wrapper around ``cache.delete_many()`` for explicit
    invalidation outside of the normal TTL lifecycle.

    Args:
        cache: Cache backend instance.
        *keys: One or more cache key strings to invalidate.

    Returns:
        Number of keys that were present and successfully deleted.

    Example::

        # Invalidate a single key
        cache_invalidate(cache, "user:42")

        # Invalidate multiple keys at once
        cache_invalidate(cache, "user:42", "user:43", "user_list")
    """
    if not keys:
        return 0
    return cache.delete_many(list(keys))
