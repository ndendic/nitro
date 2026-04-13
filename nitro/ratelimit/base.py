"""
Abstract base interface for all Nitro rate-limiter backends.

All rate-limiter implementations must subclass ``RateLimiterInterface`` and
implement every abstract method.  This ensures backends are interchangeable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RateLimitResult:
    """Outcome of a rate-limit check.

    Attributes:
        allowed: Whether the request is permitted.
        limit: Maximum number of requests in the window.
        remaining: Requests remaining before the limit is reached.
        reset_at: Monotonic timestamp when the current window resets
            (seconds since an arbitrary epoch — compare with
            ``time.monotonic()``).  May be ``None`` for backends that
            do not track exact reset times.
        retry_after: Seconds until the client should retry.  ``0`` when
            *allowed* is ``True``.
    """

    allowed: bool
    limit: int
    remaining: int
    reset_at: Optional[float] = None
    retry_after: float = 0.0


class RateLimitExceeded(Exception):
    """Raised by the ``rate_limit`` decorator when a request exceeds the limit.

    Attributes:
        result: The :class:`RateLimitResult` that triggered the exception.
    """

    def __init__(self, result: RateLimitResult) -> None:
        self.result = result
        super().__init__(
            f"Rate limit exceeded: {result.remaining}/{result.limit} remaining, "
            f"retry after {result.retry_after:.1f}s"
        )


class RateLimiterInterface(ABC):
    """Abstract base class for rate-limiter backends.

    Provides a consistent interface for checking and recording request
    rates using a sliding-window algorithm.

    Subclasses must implement :meth:`hit` and :meth:`reset`.
    """

    @abstractmethod
    def hit(self, key: str, limit: int, window: int) -> RateLimitResult:
        """Record a request and check whether the rate limit is exceeded.

        Args:
            key: Identifier for the rate-limited resource (e.g.
                ``"ip:192.168.1.1"`` or ``"user:42"``).
            limit: Maximum number of requests allowed in *window* seconds.
            window: Sliding-window size in seconds.

        Returns:
            A :class:`RateLimitResult` describing whether the request is
            allowed, how many requests remain, and when the window resets.
        """

    @abstractmethod
    def reset(self, key: str) -> None:
        """Clear all recorded hits for *key*.

        Useful for administrative resets (e.g. after a user upgrades their
        plan).

        Args:
            key: The rate-limit key to clear.
        """

    @abstractmethod
    def peek(self, key: str, limit: int, window: int) -> RateLimitResult:
        """Check the current rate-limit state *without* recording a hit.

        Args:
            key: Identifier for the rate-limited resource.
            limit: Maximum requests allowed in *window* seconds.
            window: Sliding-window size in seconds.

        Returns:
            A :class:`RateLimitResult` with the current state.
        """
