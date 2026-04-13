"""
Redis-backed distributed rate limiter using sorted sets.

Requires the ``redis`` package (``pip install redis``).  Import is lazy —
the module can be loaded without ``redis`` installed; an ``ImportError``
is raised only when ``RedisRateLimiter`` is instantiated.
"""

from __future__ import annotations

import time
import uuid
from typing import Optional

from .base import RateLimiterInterface, RateLimitResult

try:
    import redis as _redis_lib

    HAS_REDIS = True
except ImportError:  # pragma: no cover
    HAS_REDIS = False


class RedisRateLimiter(RateLimiterInterface):
    """Distributed rate limiter backed by Redis sorted sets.

    Each key maps to a Redis sorted set where members are unique request
    IDs and scores are Unix timestamps.  On each :meth:`hit`:

    1. Entries older than ``now - window`` are removed (``ZREMRANGEBYSCORE``).
    2. The current count is checked (``ZCARD``).
    3. If under the limit, a new entry is added (``ZADD``).
    4. The key's TTL is set to *window* seconds for automatic cleanup.

    All steps run inside a Redis pipeline for atomicity.

    Args:
        url: Redis connection URL (e.g. ``redis://localhost:6379/0``).
        prefix: Key prefix for namespacing (default ``"rl:"``).
        client: Pre-existing ``redis.Redis`` instance.  When provided,
            *url* is ignored.

    Raises:
        ImportError: If the ``redis`` package is not installed.

    Example::

        limiter = RedisRateLimiter(url="redis://localhost:6379/0")
        result = limiter.hit("ip:10.0.0.1", limit=100, window=60)
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        prefix: str = "rl:",
        client: Optional[object] = None,
    ) -> None:
        self._prefix = prefix
        if client is not None:
            self._client = client
        elif not HAS_REDIS:
            raise ImportError(
                "The 'redis' package is required for RedisRateLimiter. "
                "Install it with: pip install redis"
            )
        else:
            self._client = _redis_lib.Redis.from_url(url, decode_responses=True)

    def _full_key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def hit(self, key: str, limit: int, window: int) -> RateLimitResult:
        """Record a request using a Redis sorted-set sliding window.

        Args:
            key: Rate-limit key.
            limit: Max requests per window.
            window: Window size in seconds.

        Returns:
            :class:`RateLimitResult`.
        """
        now = time.time()
        cutoff = now - window
        fk = self._full_key(key)
        member = f"{now}:{uuid.uuid4().hex[:8]}"

        pipe = self._client.pipeline(transaction=True)
        pipe.zremrangebyscore(fk, "-inf", cutoff)
        pipe.zcard(fk)
        results = pipe.execute()
        count = results[1]

        if count < limit:
            pipe2 = self._client.pipeline(transaction=True)
            pipe2.zadd(fk, {member: now})
            pipe2.expire(fk, window)
            pipe2.zrange(fk, 0, 0, withscores=True)
            results2 = pipe2.execute()
            oldest = results2[2]
            oldest_score = oldest[0][1] if oldest else now
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit - count - 1,
                reset_at=oldest_score + window,
                retry_after=0.0,
            )
        else:
            # Denied — find oldest entry for retry_after
            oldest = self._client.zrange(fk, 0, 0, withscores=True)
            oldest_score = oldest[0][1] if oldest else now
            reset_at = oldest_score + window
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=max(0.0, reset_at - now),
            )

    def peek(self, key: str, limit: int, window: int) -> RateLimitResult:
        """Check current state without recording a hit.

        Args:
            key: Rate-limit key.
            limit: Max requests per window.
            window: Window size in seconds.

        Returns:
            :class:`RateLimitResult`.
        """
        now = time.time()
        cutoff = now - window
        fk = self._full_key(key)

        pipe = self._client.pipeline(transaction=True)
        pipe.zremrangebyscore(fk, "-inf", cutoff)
        pipe.zcard(fk)
        pipe.zrange(fk, 0, 0, withscores=True)
        results = pipe.execute()

        count = results[1]
        oldest = results[2]
        oldest_score = oldest[0][1] if oldest else now
        remaining = max(0, limit - count)
        reset_at = oldest_score + window

        if count >= limit:
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=max(0.0, reset_at - now),
            )
        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=0.0,
        )

    def reset(self, key: str) -> None:
        """Clear all recorded hits for *key*.

        Args:
            key: Rate-limit key.
        """
        self._client.delete(self._full_key(key))
