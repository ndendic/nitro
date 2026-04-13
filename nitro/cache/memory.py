"""
In-process dictionary-based cache with TTL and optional LRU eviction.

Suitable for single-process applications or development/testing.  For
multi-process or distributed deployments use ``RedisCache`` instead.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from .base import CacheInterface


class MemoryCache(CacheInterface):
    """Thread-safe in-memory cache with lazy TTL expiry.

    Entries are stored as ``(value, expires_at)`` tuples where
    ``expires_at`` is a monotonic timestamp (``time.monotonic()``) or
    ``None`` for entries that never expire.

    Expiry is checked lazily on ``get()`` — no background threads or
    timers are created.  Expired entries are evicted on access and during
    ``set()`` when ``max_size`` is configured.

    Args:
        default_ttl: Default TTL in seconds for entries where *ttl* is not
            specified explicitly.  ``None`` means no expiry.
        max_size: Maximum number of entries.  When exceeded the least-recently
            used entry is evicted (LRU policy).  ``None`` means unlimited.

    Example::

        cache = MemoryCache(default_ttl=300, max_size=1000)
        cache.set("user:42", {"name": "Alice"}, ttl=60)
        user = cache.get("user:42")
    """

    def __init__(
        self,
        default_ttl: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> None:
        self._default_ttl = default_ttl
        self._max_size = max_size
        # OrderedDict preserves insertion/access order for LRU eviction.
        self._store: OrderedDict[str, Tuple[Any, Optional[float]]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_expired(self, expires_at: Optional[float]) -> bool:
        """Return ``True`` if the entry has passed its expiry timestamp."""
        if expires_at is None:
            return False
        return time.monotonic() >= expires_at

    def _expires_at(self, ttl: Optional[int]) -> Optional[float]:
        """Convert a TTL in seconds to an absolute monotonic timestamp."""
        effective_ttl = ttl if ttl is not None else self._default_ttl
        if effective_ttl is None:
            return None
        return time.monotonic() + effective_ttl

    def _evict_lru(self) -> None:
        """Remove the least-recently-used entry (called when at capacity)."""
        if self._store:
            self._store.popitem(last=False)

    # ------------------------------------------------------------------
    # CacheInterface implementation
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """Return the value for *key*, or ``None`` if absent or expired.

        Expired entries are removed from the store on access (lazy eviction).
        Moves the entry to the end of the LRU order on a cache hit.

        Args:
            key: Cache key string.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expires_at = entry
            if self._is_expired(expires_at):
                del self._store[key]
                self._misses += 1
                return None
            # Move to end — marks as most-recently used
            self._store.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store *value* under *key*.

        Applies LRU eviction if ``max_size`` is configured and would be
        exceeded.  Re-setting an existing key updates its value and TTL and
        moves it to the most-recently-used position.

        Args:
            key: Cache key string.
            value: Value to store.
            ttl: Entry TTL in seconds.  Falls back to ``default_ttl`` when
                ``None``.
        """
        expires_at = self._expires_at(ttl)
        with self._lock:
            if key in self._store:
                # Update in-place and move to most-recently-used end
                self._store[key] = (value, expires_at)
                self._store.move_to_end(key)
            else:
                if self._max_size and len(self._store) >= self._max_size:
                    self._evict_lru()
                self._store[key] = (value, expires_at)

    def delete(self, key: str) -> bool:
        """Remove *key* from the cache.

        Args:
            key: Cache key string.

        Returns:
            ``True`` if the key was present (and not expired), ``False``
            otherwise.
        """
        with self._lock:
            entry = self._store.pop(key, None)
            if entry is None:
                return False
            _, expires_at = entry
            return not self._is_expired(expires_at)

    def exists(self, key: str) -> bool:
        """Return ``True`` if *key* exists and has not expired.

        Args:
            key: Cache key string.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return False
            _, expires_at = entry
            if self._is_expired(expires_at):
                del self._store[key]
                return False
            return True

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            self._store.clear()

    # ------------------------------------------------------------------
    # Bulk operations — native override for efficiency
    # ------------------------------------------------------------------

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Fetch multiple keys under a single lock acquisition.

        Args:
            keys: List of cache key strings.

        Returns:
            Dict mapping each found (non-expired) key to its value.
        """
        result: Dict[str, Any] = {}
        now = time.monotonic()
        with self._lock:
            for key in keys:
                entry = self._store.get(key)
                if entry is None:
                    self._misses += 1
                    continue
                value, expires_at = entry
                if expires_at is not None and now >= expires_at:
                    del self._store[key]
                    self._misses += 1
                    continue
                self._store.move_to_end(key)
                self._hits += 1
                result[key] = value
        return result

    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Store multiple key/value pairs under a single lock acquisition.

        Args:
            mapping: Dict of ``{key: value}`` pairs.
            ttl: TTL in seconds applied to every entry.
        """
        expires_at = self._expires_at(ttl)
        with self._lock:
            for key, value in mapping.items():
                if key in self._store:
                    self._store[key] = (value, expires_at)
                    self._store.move_to_end(key)
                else:
                    if self._max_size and len(self._store) >= self._max_size:
                        self._evict_lru()
                    self._store[key] = (value, expires_at)

    def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys under a single lock acquisition.

        Args:
            keys: List of cache key strings.

        Returns:
            Number of keys that were present and deleted.
        """
        now = time.monotonic()
        count = 0
        with self._lock:
            for key in keys:
                entry = self._store.pop(key, None)
                if entry is not None:
                    _, expires_at = entry
                    if expires_at is None or now < expires_at:
                        count += 1
        return count

    # ------------------------------------------------------------------
    # Atomic integer counters — override for lock-safety
    # ------------------------------------------------------------------

    def incr(self, key: str, amount: int = 1) -> int:
        """Atomically increment an integer counter.

        Initialises the counter to ``0`` if the key does not exist.

        Args:
            key: Cache key string.
            amount: Amount to add.

        Returns:
            New integer value.

        Raises:
            TypeError: If the stored value is not an integer.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                current = 0
                expires_at = None
            else:
                current, expires_at = entry
                if self._is_expired(expires_at):
                    current = 0
                    expires_at = None
            if not isinstance(current, int):
                raise TypeError(
                    f"Cache value at '{key}' is not an integer: {type(current).__name__}"
                )
            new_value = current + amount
            self._store[key] = (new_value, expires_at)
            self._store.move_to_end(key)
            return new_value

    def decr(self, key: str, amount: int = 1) -> int:
        """Atomically decrement an integer counter.

        Args:
            key: Cache key string.
            amount: Amount to subtract.

        Returns:
            New integer value.
        """
        return self.incr(key, amount=-amount)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics.

        Returns a dict with the following keys:

        - ``hits``: Number of successful ``get()`` calls.
        - ``misses``: Number of failed ``get()`` calls (absent or expired).
        - ``size``: Current number of entries (including not-yet-evicted
          expired entries).
        - ``max_size``: Configured ``max_size`` limit, or ``None``.
        - ``default_ttl``: Configured ``default_ttl``, or ``None``.
        """
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._store),
                "max_size": self._max_size,
                "default_ttl": self._default_ttl,
            }
