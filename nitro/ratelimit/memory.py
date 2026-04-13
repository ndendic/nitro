"""
In-process sliding-window rate limiter.

Suitable for single-process applications or development/testing.  For
multi-process or distributed deployments use ``RedisRateLimiter`` instead.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Dict, List

from .base import RateLimiterInterface, RateLimitResult


class MemoryRateLimiter(RateLimiterInterface):
    """Thread-safe in-memory rate limiter using a sliding-window log.

    Each key stores a list of monotonic timestamps representing request
    times.  On every :meth:`hit` call, timestamps older than the window
    are pruned, and the request is allowed only if the remaining count
    is below the limit.

    Args:
        prefix: Optional prefix prepended to all keys (useful for
            namespacing multiple limiters in the same process).

    Example::

        limiter = MemoryRateLimiter()
        result = limiter.hit("ip:10.0.0.1", limit=100, window=60)
        if not result.allowed:
            raise RateLimitExceeded(result)
    """

    def __init__(self, prefix: str = "") -> None:
        self._prefix = prefix
        self._store: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _full_key(self, key: str) -> str:
        return f"{self._prefix}{key}" if self._prefix else key

    def _prune(self, entries: List[float], cutoff: float) -> List[float]:
        """Remove timestamps older than *cutoff* (in-place for efficiency)."""
        # entries are appended in monotonic order, so we can bisect
        idx = 0
        for i, ts in enumerate(entries):
            if ts > cutoff:
                idx = i
                break
        else:
            # all entries are expired
            idx = len(entries)
        if idx:
            del entries[:idx]
        return entries

    def hit(self, key: str, limit: int, window: int) -> RateLimitResult:
        """Record a request and return the rate-limit state.

        Uses a sliding-window log: timestamps older than ``now - window``
        are pruned, and the request is counted only if the limit has not
        been reached.

        Args:
            key: Rate-limit key.
            limit: Max requests per window.
            window: Window size in seconds.

        Returns:
            :class:`RateLimitResult`.
        """
        now = time.monotonic()
        cutoff = now - window
        fk = self._full_key(key)

        with self._lock:
            entries = self._prune(self._store[fk], cutoff)
            count = len(entries)

            if count < limit:
                entries.append(now)
                self._store[fk] = entries
                return RateLimitResult(
                    allowed=True,
                    limit=limit,
                    remaining=limit - count - 1,
                    reset_at=entries[0] + window if entries else now + window,
                    retry_after=0.0,
                )
            else:
                # Denied — calculate retry_after from oldest entry in window
                reset_at = entries[0] + window
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
        now = time.monotonic()
        cutoff = now - window
        fk = self._full_key(key)

        with self._lock:
            entries = self._prune(self._store.get(fk, []), cutoff)
            if fk in self._store:
                self._store[fk] = entries
            count = len(entries)
            remaining = max(0, limit - count)
            reset_at = entries[0] + window if entries else now + window

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
        fk = self._full_key(key)
        with self._lock:
            self._store.pop(fk, None)
