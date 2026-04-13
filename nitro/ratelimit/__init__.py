"""
nitro.ratelimit — Framework-agnostic rate limiting for the Nitro framework.

Provides:
- RateLimiterInterface : Abstract base for rate-limiter backends
- MemoryRateLimiter    : In-process sliding-window rate limiter
- RateLimitResult      : Dataclass with allowed/remaining/reset info
- RateLimitExceeded    : Exception raised when limit is exceeded
- rate_limit           : Decorator for applying rate limits to handlers

Optional backends (requires extra dependencies):
- RedisRateLimiter     : Redis-backed distributed rate limiter (pip install redis)

Quick start::

    from nitro.ratelimit import MemoryRateLimiter, rate_limit

    limiter = MemoryRateLimiter()

    @rate_limit(limiter, limit=100, window=60)
    async def api_handler(request):
        ...

Direct usage::

    limiter = MemoryRateLimiter()

    result = limiter.hit("ip:10.0.0.1", limit=100, window=60)
    if not result.allowed:
        print(f"Retry after {result.retry_after:.1f}s")

    # Check without recording
    state = limiter.peek("ip:10.0.0.1", limit=100, window=60)

    # Administrative reset
    limiter.reset("ip:10.0.0.1")

Redis backend::

    from nitro.ratelimit.redis_limiter import RedisRateLimiter

    limiter = RedisRateLimiter(
        url="redis://localhost:6379/0",
        prefix="myapp:rl:",
    )
"""

from .base import RateLimiterInterface, RateLimitExceeded, RateLimitResult
from .memory import MemoryRateLimiter
from .decorators import rate_limit

__all__ = [
    "RateLimiterInterface",
    "RateLimitResult",
    "RateLimitExceeded",
    "MemoryRateLimiter",
    "rate_limit",
]

# RedisRateLimiter is imported lazily to avoid hard dependency on the redis package.
# Import it explicitly when needed:
#
#   from nitro.ratelimit.redis_limiter import RedisRateLimiter
#
# or check availability:
#
#   from nitro.ratelimit.redis_limiter import HAS_REDIS, RedisRateLimiter
