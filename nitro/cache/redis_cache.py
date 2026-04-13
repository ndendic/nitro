"""
Redis-backed distributed cache for the Nitro framework.

Requires the ``redis`` package::

    pip install redis

Values are serialised to JSON, so any JSON-serialisable Python object can
be stored.  Integer counters use Redis's native INCRBY/DECRBY commands for
true atomicity across processes.

Usage::

    from nitro.cache import RedisCache

    cache = RedisCache(url="redis://localhost:6379/0", default_ttl=300)
    cache.set("user:42", {"name": "Alice"}, ttl=60)
    user = cache.get("user:42")
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .base import CacheInterface

try:
    import redis as _redis_module
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class RedisCache(CacheInterface):
    """Redis-backed cache with JSON serialisation and optional namespace prefix.

    All keys are stored under ``{prefix}:{key}`` to avoid collisions with
    other Redis data in the same database.

    ``clear()`` uses ``SCAN`` + ``DEL`` rather than ``KEYS`` to avoid
    blocking the Redis server in production.

    ``get_many`` uses ``MGET`` and ``set_many`` uses a pipeline for
    efficient batching.

    ``incr``/``decr`` delegate to Redis's native ``INCRBY``/``DECRBY``,
    which are atomic across multiple processes and connections.

    Args:
        url: Redis connection URL, e.g. ``redis://localhost:6379/0`` or
            ``rediss://...`` for TLS.
        prefix: Namespace prefix prepended to every key (default
            ``"nitro:cache"``).
        default_ttl: Default TTL in seconds.  ``None`` means no expiry
            unless overridden per-call.

    Raises:
        ImportError: If the ``redis`` package is not installed.

    Example::

        cache = RedisCache(
            url="redis://localhost:6379/0",
            prefix="myapp:cache",
            default_ttl=600,
        )
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        prefix: str = "nitro:cache",
        default_ttl: Optional[int] = None,
    ) -> None:
        if not HAS_REDIS:
            raise ImportError(
                "redis package is required for RedisCache: pip install redis"
            )
        self._url = url
        self._prefix = prefix
        self._default_ttl = default_ttl
        self._client = _redis_module.from_url(url, decode_responses=True)

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------

    def _k(self, key: str) -> str:
        """Return the namespaced Redis key for *key*."""
        return f"{self._prefix}:{key}"

    def _strip_prefix(self, redis_key: str) -> str:
        """Strip the namespace prefix from a Redis key."""
        prefix_with_colon = f"{self._prefix}:"
        if redis_key.startswith(prefix_with_colon):
            return redis_key[len(prefix_with_colon):]
        return redis_key

    def _effective_ttl(self, ttl: Optional[int]) -> Optional[int]:
        """Return *ttl* if given, else ``default_ttl``, else ``None``."""
        return ttl if ttl is not None else self._default_ttl

    # ------------------------------------------------------------------
    # CacheInterface implementation
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """Return the value for *key*, or ``None`` if absent or expired.

        Args:
            key: Cache key string.
        """
        raw = self._client.get(self._k(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return raw

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store *value* under *key* with an optional TTL.

        Args:
            key: Cache key string.
            value: JSON-serialisable value.
            ttl: Expiry in seconds.  Falls back to ``default_ttl``.
        """
        effective_ttl = self._effective_ttl(ttl)
        serialised = json.dumps(value)
        if effective_ttl is not None:
            self._client.setex(self._k(key), effective_ttl, serialised)
        else:
            self._client.set(self._k(key), serialised)

    def delete(self, key: str) -> bool:
        """Remove *key* from the cache.

        Args:
            key: Cache key string.

        Returns:
            ``True`` if the key existed and was deleted.
        """
        return self._client.delete(self._k(key)) > 0

    def exists(self, key: str) -> bool:
        """Return ``True`` if *key* exists and has not expired.

        Args:
            key: Cache key string.
        """
        return self._client.exists(self._k(key)) > 0

    def clear(self) -> None:
        """Remove all entries under this cache's namespace prefix.

        Uses ``SCAN`` + ``DEL`` in batches to avoid blocking Redis.
        """
        pattern = f"{self._prefix}:*"
        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor, match=pattern, count=200)
            if keys:
                self._client.delete(*keys)
            if cursor == 0:
                break

    # ------------------------------------------------------------------
    # Bulk operations — native Redis equivalents
    # ------------------------------------------------------------------

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Fetch multiple keys using ``MGET``.

        Args:
            keys: List of cache key strings.

        Returns:
            Dict mapping found keys to their deserialized values.
        """
        if not keys:
            return {}
        redis_keys = [self._k(k) for k in keys]
        values = self._client.mget(redis_keys)
        result: Dict[str, Any] = {}
        for key, raw in zip(keys, values):
            if raw is not None:
                try:
                    result[key] = json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    result[key] = raw
        return result

    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Store multiple key/value pairs using a Redis pipeline.

        Args:
            mapping: Dict of ``{key: value}`` pairs.
            ttl: TTL in seconds applied to every key.
        """
        if not mapping:
            return
        effective_ttl = self._effective_ttl(ttl)
        pipe = self._client.pipeline(transaction=False)
        for key, value in mapping.items():
            serialised = json.dumps(value)
            if effective_ttl is not None:
                pipe.setex(self._k(key), effective_ttl, serialised)
            else:
                pipe.set(self._k(key), serialised)
        pipe.execute()

    def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys with a single ``DEL`` command.

        Args:
            keys: List of cache key strings.

        Returns:
            Number of keys that were present and deleted.
        """
        if not keys:
            return 0
        redis_keys = [self._k(k) for k in keys]
        return self._client.delete(*redis_keys)

    # ------------------------------------------------------------------
    # Atomic integer counters — native Redis INCRBY/DECRBY
    # ------------------------------------------------------------------

    def incr(self, key: str, amount: int = 1) -> int:
        """Atomically increment an integer counter using Redis INCRBY.

        Creates the key with value ``0`` if it does not exist, then applies
        the increment.  The TTL of an existing key is preserved.

        Args:
            key: Cache key string.
            amount: Amount to add (default ``1``).

        Returns:
            New integer value.

        Raises:
            redis.ResponseError: If the stored value is not an integer.
        """
        return self._client.incrby(self._k(key), amount)

    def decr(self, key: str, amount: int = 1) -> int:
        """Atomically decrement an integer counter using Redis DECRBY.

        Args:
            key: Cache key string.
            amount: Amount to subtract (default ``1``).

        Returns:
            New integer value.
        """
        return self._client.decrby(self._k(key), amount)
