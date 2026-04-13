"""
Tests for nitro.ratelimit — framework-agnostic rate limiting module.

Covers: MemoryRateLimiter (sliding window, reset, peek, prefix, thread safety),
        rate_limit decorator (sync, async, custom key, RateLimitExceeded),
        RateLimitResult dataclass, RateLimitExceeded exception.
"""

import asyncio
import threading
import time
from unittest.mock import patch

import pytest

from nitro.ratelimit import (
    MemoryRateLimiter,
    RateLimiterInterface,
    RateLimitExceeded,
    RateLimitResult,
    rate_limit,
)


# ---------------------------------------------------------------------------
# RateLimitResult
# ---------------------------------------------------------------------------


class TestRateLimitResult:
    def test_allowed_result(self):
        r = RateLimitResult(allowed=True, limit=10, remaining=9)
        assert r.allowed is True
        assert r.limit == 10
        assert r.remaining == 9
        assert r.retry_after == 0.0

    def test_denied_result(self):
        r = RateLimitResult(
            allowed=False, limit=10, remaining=0, retry_after=5.5
        )
        assert r.allowed is False
        assert r.remaining == 0
        assert r.retry_after == 5.5

    def test_frozen(self):
        r = RateLimitResult(allowed=True, limit=10, remaining=9)
        with pytest.raises(AttributeError):
            r.allowed = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RateLimitExceeded
# ---------------------------------------------------------------------------


class TestRateLimitExceeded:
    def test_exception_message(self):
        r = RateLimitResult(
            allowed=False, limit=10, remaining=0, retry_after=3.2
        )
        exc = RateLimitExceeded(r)
        assert "Rate limit exceeded" in str(exc)
        assert "3.2" in str(exc)
        assert exc.result is r

    def test_is_exception(self):
        r = RateLimitResult(allowed=False, limit=5, remaining=0)
        exc = RateLimitExceeded(r)
        assert isinstance(exc, Exception)


# ---------------------------------------------------------------------------
# RateLimiterInterface — abstract
# ---------------------------------------------------------------------------


class TestRateLimiterInterface:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            RateLimiterInterface()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# MemoryRateLimiter — basic operations
# ---------------------------------------------------------------------------


class TestMemoryRateLimiterHit:
    def test_first_hit_allowed(self):
        limiter = MemoryRateLimiter()
        r = limiter.hit("k1", limit=5, window=60)
        assert r.allowed is True
        assert r.limit == 5
        assert r.remaining == 4

    def test_hits_decrement_remaining(self):
        limiter = MemoryRateLimiter()
        for i in range(4):
            r = limiter.hit("k1", limit=5, window=60)
            assert r.allowed is True
            assert r.remaining == 5 - i - 1

    def test_limit_reached_denies(self):
        limiter = MemoryRateLimiter()
        for _ in range(5):
            limiter.hit("k1", limit=5, window=60)
        r = limiter.hit("k1", limit=5, window=60)
        assert r.allowed is False
        assert r.remaining == 0
        assert r.retry_after > 0

    def test_different_keys_independent(self):
        limiter = MemoryRateLimiter()
        for _ in range(5):
            limiter.hit("a", limit=5, window=60)
        # a is exhausted
        r_a = limiter.hit("a", limit=5, window=60)
        assert r_a.allowed is False
        # b is fresh
        r_b = limiter.hit("b", limit=5, window=60)
        assert r_b.allowed is True
        assert r_b.remaining == 4

    def test_retry_after_zero_when_allowed(self):
        limiter = MemoryRateLimiter()
        r = limiter.hit("k", limit=10, window=60)
        assert r.retry_after == 0.0

    def test_reset_at_present(self):
        limiter = MemoryRateLimiter()
        r = limiter.hit("k", limit=10, window=60)
        assert r.reset_at is not None
        assert r.reset_at > time.monotonic()


class TestMemoryRateLimiterWindow:
    def test_window_expiry_allows_again(self):
        limiter = MemoryRateLimiter()
        # Fill the bucket
        for _ in range(3):
            limiter.hit("k", limit=3, window=1)
        r = limiter.hit("k", limit=3, window=1)
        assert r.allowed is False

        # Wait for window to pass
        time.sleep(1.1)
        r = limiter.hit("k", limit=3, window=1)
        assert r.allowed is True
        assert r.remaining == 2

    def test_sliding_window_partial_expiry(self):
        """Only oldest entries expire, not all at once."""
        limiter = MemoryRateLimiter()
        limiter.hit("k", limit=3, window=1)
        time.sleep(0.6)
        limiter.hit("k", limit=3, window=1)
        limiter.hit("k", limit=3, window=1)
        # 3 hits, should be denied
        r = limiter.hit("k", limit=3, window=1)
        assert r.allowed is False

        # Wait for first entry to expire (0.6s was 0.6s ago, needs 0.4s more)
        time.sleep(0.5)
        r = limiter.hit("k", limit=3, window=1)
        assert r.allowed is True


class TestMemoryRateLimiterReset:
    def test_reset_clears_key(self):
        limiter = MemoryRateLimiter()
        for _ in range(5):
            limiter.hit("k", limit=5, window=60)
        r = limiter.hit("k", limit=5, window=60)
        assert r.allowed is False

        limiter.reset("k")
        r = limiter.hit("k", limit=5, window=60)
        assert r.allowed is True
        assert r.remaining == 4

    def test_reset_nonexistent_key_noop(self):
        limiter = MemoryRateLimiter()
        limiter.reset("nonexistent")  # should not raise


class TestMemoryRateLimiterPeek:
    def test_peek_does_not_count(self):
        limiter = MemoryRateLimiter()
        limiter.hit("k", limit=5, window=60)

        p = limiter.peek("k", limit=5, window=60)
        assert p.allowed is True
        assert p.remaining == 4

        # peek again — remaining still 4
        p2 = limiter.peek("k", limit=5, window=60)
        assert p2.remaining == 4

    def test_peek_empty_key(self):
        limiter = MemoryRateLimiter()
        p = limiter.peek("fresh", limit=10, window=60)
        assert p.allowed is True
        assert p.remaining == 10

    def test_peek_at_limit(self):
        limiter = MemoryRateLimiter()
        for _ in range(5):
            limiter.hit("k", limit=5, window=60)
        p = limiter.peek("k", limit=5, window=60)
        assert p.allowed is False
        assert p.remaining == 0
        assert p.retry_after > 0


class TestMemoryRateLimiterPrefix:
    def test_prefix_isolates_keys(self):
        l1 = MemoryRateLimiter(prefix="api:")
        l2 = MemoryRateLimiter(prefix="web:")

        for _ in range(3):
            l1.hit("user:1", limit=3, window=60)
        r1 = l1.hit("user:1", limit=3, window=60)
        assert r1.allowed is False

        # Same key name but different prefix — still allowed
        r2 = l2.hit("user:1", limit=3, window=60)
        assert r2.allowed is True

    def test_no_prefix(self):
        limiter = MemoryRateLimiter()
        r = limiter.hit("bare", limit=5, window=60)
        assert r.allowed is True


class TestMemoryRateLimiterThreadSafety:
    def test_concurrent_hits_respect_limit(self):
        limiter = MemoryRateLimiter()
        limit = 50
        results = []
        barrier = threading.Barrier(60)

        def worker():
            barrier.wait()
            r = limiter.hit("concurrent", limit=limit, window=60)
            results.append(r.allowed)

        threads = [threading.Thread(target=worker) for _ in range(60)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        allowed_count = sum(1 for r in results if r)
        denied_count = sum(1 for r in results if not r)
        assert allowed_count == limit
        assert denied_count == 10


# ---------------------------------------------------------------------------
# rate_limit decorator
# ---------------------------------------------------------------------------


class TestRateLimitDecorator:
    def test_sync_function_allowed(self):
        limiter = MemoryRateLimiter()

        @rate_limit(limiter, limit=5, window=60)
        def handler(request):
            return "ok"

        assert handler("req1") == "ok"

    def test_sync_function_denied(self):
        limiter = MemoryRateLimiter()

        @rate_limit(limiter, limit=2, window=60)
        def handler(request):
            return "ok"

        handler("req1")
        handler("req1")
        with pytest.raises(RateLimitExceeded):
            handler("req1")

    def test_async_function_allowed(self):
        limiter = MemoryRateLimiter()

        @rate_limit(limiter, limit=5, window=60)
        async def handler(request):
            return "ok"

        result = asyncio.run(handler("req1"))
        assert result == "ok"

    def test_async_function_denied(self):
        limiter = MemoryRateLimiter()

        @rate_limit(limiter, limit=2, window=60)
        async def handler(request):
            return "ok"

        asyncio.run(handler("req1"))
        asyncio.run(handler("req1"))
        with pytest.raises(RateLimitExceeded):
            asyncio.run(handler("req1"))

    def test_custom_key_func(self):
        limiter = MemoryRateLimiter()

        @rate_limit(
            limiter,
            limit=2,
            window=60,
            key_func=lambda req: req.get("ip", "unknown"),
        )
        def handler(req):
            return "ok"

        handler({"ip": "1.1.1.1"})
        handler({"ip": "1.1.1.1"})
        with pytest.raises(RateLimitExceeded):
            handler({"ip": "1.1.1.1"})

        # Different key is allowed
        assert handler({"ip": "2.2.2.2"}) == "ok"

    def test_default_key_uses_first_arg(self):
        limiter = MemoryRateLimiter()

        @rate_limit(limiter, limit=1, window=60)
        def handler(request):
            return "ok"

        handler("same-key")
        with pytest.raises(RateLimitExceeded):
            handler("same-key")

        # Different first arg = different key
        assert handler("other-key") == "ok"

    def test_no_args_uses_global_key(self):
        limiter = MemoryRateLimiter()

        @rate_limit(limiter, limit=1, window=60)
        def handler():
            return "ok"

        handler()
        with pytest.raises(RateLimitExceeded):
            handler()

    def test_preserves_function_name(self):
        limiter = MemoryRateLimiter()

        @rate_limit(limiter, limit=5, window=60)
        def my_handler(request):
            return "ok"

        assert my_handler.__name__ == "my_handler"

    def test_preserves_async_function_name(self):
        limiter = MemoryRateLimiter()

        @rate_limit(limiter, limit=5, window=60)
        async def my_async_handler(request):
            return "ok"

        assert my_async_handler.__name__ == "my_async_handler"

    def test_exception_contains_result(self):
        limiter = MemoryRateLimiter()

        @rate_limit(limiter, limit=1, window=60)
        def handler(req):
            return "ok"

        handler("k")
        with pytest.raises(RateLimitExceeded) as exc_info:
            handler("k")

        assert exc_info.value.result.allowed is False
        assert exc_info.value.result.limit == 1
        assert exc_info.value.result.remaining == 0


# ---------------------------------------------------------------------------
# RedisRateLimiter — mock-based (no Redis server needed)
# ---------------------------------------------------------------------------


class TestRedisRateLimiter:
    """Tests using a mock Redis client — no real Redis required."""

    def _make_limiter(self, mock_client):
        from nitro.ratelimit.redis_limiter import RedisRateLimiter

        return RedisRateLimiter(client=mock_client)

    def test_hit_allowed(self):
        from unittest.mock import MagicMock

        mock = MagicMock()
        pipe = MagicMock()
        mock.pipeline.return_value = pipe

        # First pipeline: zremrangebyscore + zcard
        pipe.execute.side_effect = [
            [0, 0],  # 0 removed, 0 entries
            [1, None, [(b"entry", 1000.0)]],  # zadd, expire, zrange
        ]

        limiter = self._make_limiter(mock)
        with patch("time.time", return_value=1000.0):
            r = limiter.hit("k", limit=5, window=60)

        assert r.allowed is True
        assert r.remaining == 4

    def test_hit_denied(self):
        from unittest.mock import MagicMock

        mock = MagicMock()
        pipe = MagicMock()
        mock.pipeline.return_value = pipe
        pipe.execute.return_value = [0, 5]  # 5 entries = at limit
        mock.zrange.return_value = [(b"oldest", 990.0)]

        limiter = self._make_limiter(mock)
        with patch("time.time", return_value=1000.0):
            r = limiter.hit("k", limit=5, window=60)

        assert r.allowed is False
        assert r.remaining == 0
        assert r.retry_after == pytest.approx(50.0, abs=1.0)

    def test_peek(self):
        from unittest.mock import MagicMock

        mock = MagicMock()
        pipe = MagicMock()
        mock.pipeline.return_value = pipe
        pipe.execute.return_value = [0, 3, [(b"oldest", 995.0)]]

        limiter = self._make_limiter(mock)
        with patch("time.time", return_value=1000.0):
            r = limiter.peek("k", limit=5, window=60)

        assert r.allowed is True
        assert r.remaining == 2

    def test_reset_calls_delete(self):
        from unittest.mock import MagicMock

        mock = MagicMock()
        limiter = self._make_limiter(mock)
        limiter.reset("k")
        mock.delete.assert_called_once_with("rl:k")

    def test_custom_prefix(self):
        from unittest.mock import MagicMock

        mock = MagicMock()
        from nitro.ratelimit.redis_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(prefix="app:", client=mock)
        limiter.reset("user:1")
        mock.delete.assert_called_once_with("app:user:1")

    def test_import_error_without_redis(self):
        """Verify meaningful error when redis package missing."""
        from nitro.ratelimit.redis_limiter import RedisRateLimiter, HAS_REDIS

        if HAS_REDIS:
            pytest.skip("redis is installed")
        with pytest.raises(ImportError, match="redis"):
            RedisRateLimiter()
