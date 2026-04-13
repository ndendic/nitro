"""
nitro.cache — Framework-agnostic caching for the Nitro framework.

Provides:
- CacheInterface  : Abstract base for cache backends
- MemoryCache     : In-process dict-based cache with TTL and optional LRU
- cached          : Decorator for caching sync and async function results
- cache_invalidate: Helper for manual cache key invalidation

Optional backends (requires extra dependencies):
- RedisCache      : Redis-backed distributed cache (pip install redis)

Quick start::

    from nitro.cache import MemoryCache, cached

    cache = MemoryCache(default_ttl=300)

    @cached(cache, ttl=120)
    def expensive_function(x):
        ...

    # Direct cache operations
    cache.set("key", "value", ttl=60)
    value = cache.get("key")
    cache.delete("key")

    # Bulk operations
    cache.set_many({"a": 1, "b": 2}, ttl=60)
    values = cache.get_many(["a", "b"])

    # Atomic counters
    cache.set("hits", 0)
    cache.incr("hits")          # 1
    cache.incr("hits", 5)       # 6
    cache.decr("hits", 2)       # 4

Redis backend::

    from nitro.cache import RedisCache

    cache = RedisCache(
        url="redis://localhost:6379/0",
        prefix="myapp:cache",
        default_ttl=600,
    )

Manual invalidation::

    from nitro.cache import cache_invalidate

    cache_invalidate(cache, "user:42", "user_list")
"""

from .base import CacheInterface
from .memory import MemoryCache
from .decorators import cached, cache_invalidate

__all__ = [
    "CacheInterface",
    "MemoryCache",
    "cached",
    "cache_invalidate",
]

# RedisCache is imported lazily to avoid hard dependency on the redis package.
# Import it explicitly when needed:
#
#   from nitro.cache.redis_cache import RedisCache
#
# or check availability:
#
#   from nitro.cache.redis_cache import HAS_REDIS, RedisCache
