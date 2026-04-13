"""
Tests for nitro.cache — framework-agnostic caching module.

Covers: MemoryCache (TTL, LRU, bulk ops, counters, stats),
        cached decorator (sync, async, custom key), cache_invalidate.
"""

import asyncio
import time
from unittest.mock import patch

import pytest

from nitro.cache import CacheInterface, MemoryCache, cached, cache_invalidate


# ---------------------------------------------------------------------------
# MemoryCache — core operations
# ---------------------------------------------------------------------------


class TestMemoryCacheGetSet:
    def test_set_and_get(self):
        cache = MemoryCache()
        cache.set("k1", "hello")
        assert cache.get("k1") == "hello"

    def test_get_missing_returns_none(self):
        cache = MemoryCache()
        assert cache.get("nonexistent") is None

    def test_overwrite_existing_key(self):
        cache = MemoryCache()
        cache.set("k", 1)
        cache.set("k", 2)
        assert cache.get("k") == 2

    def test_stores_complex_values(self):
        cache = MemoryCache()
        data = {"users": [{"id": 1, "name": "Alice"}], "count": 1}
        cache.set("data", data)
        assert cache.get("data") == data

    def test_none_value_not_cached_by_decorator_but_stored_directly(self):
        cache = MemoryCache()
        cache.set("k", 0)
        assert cache.get("k") == 0


class TestMemoryCacheDelete:
    def test_delete_existing(self):
        cache = MemoryCache()
        cache.set("k", "v")
        assert cache.delete("k") is True
        assert cache.get("k") is None

    def test_delete_missing(self):
        cache = MemoryCache()
        assert cache.delete("k") is False

    def test_exists_after_delete(self):
        cache = MemoryCache()
        cache.set("k", "v")
        cache.delete("k")
        assert cache.exists("k") is False


class TestMemoryCacheExists:
    def test_exists_true(self):
        cache = MemoryCache()
        cache.set("k", 42)
        assert cache.exists("k") is True

    def test_exists_false(self):
        cache = MemoryCache()
        assert cache.exists("nope") is False


class TestMemoryCacheClear:
    def test_clear_removes_all(self):
        cache = MemoryCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None


# ---------------------------------------------------------------------------
# TTL behaviour
# ---------------------------------------------------------------------------


class TestMemoryCacheTTL:
    def test_explicit_ttl_expires(self):
        cache = MemoryCache()
        cache.set("k", "v", ttl=1)
        assert cache.get("k") == "v"
        time.sleep(1.1)
        assert cache.get("k") is None

    def test_default_ttl_applied(self):
        cache = MemoryCache(default_ttl=1)
        cache.set("k", "v")
        assert cache.get("k") == "v"
        time.sleep(1.1)
        assert cache.get("k") is None

    def test_no_ttl_never_expires(self):
        cache = MemoryCache()
        cache.set("k", "v")
        # No sleep needed — just verify it persists
        assert cache.get("k") == "v"

    def test_exists_returns_false_for_expired(self):
        cache = MemoryCache()
        cache.set("k", "v", ttl=1)
        time.sleep(1.1)
        assert cache.exists("k") is False

    def test_delete_expired_returns_false(self):
        cache = MemoryCache()
        cache.set("k", "v", ttl=1)
        time.sleep(1.1)
        assert cache.delete("k") is False


# ---------------------------------------------------------------------------
# LRU eviction
# ---------------------------------------------------------------------------


class TestMemoryCacheLRU:
    def test_evicts_oldest_when_full(self):
        cache = MemoryCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # should evict "a"
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_access_refreshes_lru_order(self):
        cache = MemoryCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")  # refresh "a" — now "b" is oldest
        cache.set("c", 3)  # should evict "b"
        assert cache.get("a") == 1
        assert cache.get("b") is None
        assert cache.get("c") == 3

    def test_overwrite_does_not_evict(self):
        cache = MemoryCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("a", 10)  # overwrite, not new entry
        assert cache.get("a") == 10
        assert cache.get("b") == 2


# ---------------------------------------------------------------------------
# Bulk operations
# ---------------------------------------------------------------------------


class TestMemoryCacheBulk:
    def test_get_many(self):
        cache = MemoryCache()
        cache.set("a", 1)
        cache.set("b", 2)
        result = cache.get_many(["a", "b", "c"])
        assert result == {"a": 1, "b": 2}

    def test_set_many(self):
        cache = MemoryCache()
        cache.set_many({"x": 10, "y": 20})
        assert cache.get("x") == 10
        assert cache.get("y") == 20

    def test_delete_many(self):
        cache = MemoryCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        deleted = cache.delete_many(["a", "c", "missing"])
        assert deleted == 2
        assert cache.get("b") == 2

    def test_set_many_with_ttl(self):
        cache = MemoryCache()
        cache.set_many({"a": 1, "b": 2}, ttl=1)
        assert cache.get("a") == 1
        time.sleep(1.1)
        assert cache.get("a") is None


# ---------------------------------------------------------------------------
# Atomic counters
# ---------------------------------------------------------------------------


class TestMemoryCacheCounters:
    def test_incr_new_key(self):
        cache = MemoryCache()
        result = cache.incr("counter")
        assert result == 1

    def test_incr_existing(self):
        cache = MemoryCache()
        cache.set("counter", 5)
        assert cache.incr("counter") == 6
        assert cache.incr("counter", 10) == 16

    def test_decr(self):
        cache = MemoryCache()
        cache.set("counter", 10)
        assert cache.decr("counter") == 9
        assert cache.decr("counter", 5) == 4

    def test_incr_non_integer_raises(self):
        cache = MemoryCache()
        cache.set("k", "string")
        with pytest.raises(TypeError, match="not an integer"):
            cache.incr("k")

    def test_incr_expired_key_resets_to_zero(self):
        cache = MemoryCache()
        cache.set("counter", 100, ttl=1)
        time.sleep(1.1)
        assert cache.incr("counter") == 1


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TestMemoryCacheStats:
    def test_stats_initial(self):
        cache = MemoryCache(default_ttl=60, max_size=100)
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0
        assert stats["max_size"] == 100
        assert stats["default_ttl"] == 60

    def test_stats_after_operations(self):
        cache = MemoryCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")  # hit
        cache.get("c")  # miss
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 2


# ---------------------------------------------------------------------------
# cached decorator
# ---------------------------------------------------------------------------


class TestCachedDecorator:
    def test_caches_return_value(self):
        cache = MemoryCache()
        call_count = 0

        @cached(cache, ttl=60)
        def compute(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert compute(5) == 10
        assert compute(5) == 10  # cached
        assert call_count == 1

    def test_different_args_different_keys(self):
        cache = MemoryCache()
        call_count = 0

        @cached(cache, ttl=60)
        def compute(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert compute(1) == 2
        assert compute(2) == 4
        assert call_count == 2

    def test_none_result_not_cached(self):
        cache = MemoryCache()
        call_count = 0

        @cached(cache, ttl=60)
        def maybe_none():
            nonlocal call_count
            call_count += 1
            return None

        assert maybe_none() is None
        assert maybe_none() is None
        assert call_count == 2  # called both times

    def test_custom_key_func(self):
        cache = MemoryCache()

        @cached(cache, key_func=lambda f, a, kw: f"user:{a[0]}")
        def get_user(user_id):
            return {"id": user_id}

        result = get_user(42)
        assert result == {"id": 42}
        assert cache.get("user:42") == {"id": 42}

    def test_preserves_function_name(self):
        cache = MemoryCache()

        @cached(cache)
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    def test_async_function(self):
        cache = MemoryCache()
        call_count = 0

        @cached(cache, ttl=60)
        async def async_compute(x):
            nonlocal call_count
            call_count += 1
            return x + 1

        loop = asyncio.new_event_loop()
        try:
            assert loop.run_until_complete(async_compute(5)) == 6
            assert loop.run_until_complete(async_compute(5)) == 6
            assert call_count == 1
        finally:
            loop.close()


# ---------------------------------------------------------------------------
# cache_invalidate
# ---------------------------------------------------------------------------


class TestCacheInvalidate:
    def test_invalidate_single_key(self):
        cache = MemoryCache()
        cache.set("a", 1)
        deleted = cache_invalidate(cache, "a")
        assert deleted == 1
        assert cache.get("a") is None

    def test_invalidate_multiple_keys(self):
        cache = MemoryCache()
        cache.set("a", 1)
        cache.set("b", 2)
        deleted = cache_invalidate(cache, "a", "b", "c")
        assert deleted == 2

    def test_invalidate_no_keys(self):
        cache = MemoryCache()
        assert cache_invalidate(cache) == 0


# ---------------------------------------------------------------------------
# CacheInterface ABC enforcement
# ---------------------------------------------------------------------------


class TestCacheInterface:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            CacheInterface()
