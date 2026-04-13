"""
Abstract base interface for all Nitro cache backends.

All cache implementations must subclass ``CacheInterface`` and implement
every abstract method. This ensures backends are interchangeable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class CacheInterface(ABC):
    """Abstract base class for cache backends.

    Provides a consistent interface for key/value storage with optional
    TTL, bulk operations, and atomic integer counters.

    Subclasses must implement all abstract methods.  Optional operations
    (``get_many``, ``set_many``, ``delete_many``, ``incr``, ``decr``) have
    default implementations built on top of the primitives, but backends
    should override them with native equivalents when available.
    """

    # ------------------------------------------------------------------
    # Core primitives — must be implemented by every backend
    # ------------------------------------------------------------------

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Return the cached value for *key*, or ``None`` if missing/expired.

        Args:
            key: Cache key string.

        Returns:
            The stored value, or ``None``.
        """

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store *value* under *key* with an optional TTL.

        Args:
            key: Cache key string.
            value: Serialisable value to store.
            ttl: Expiry in seconds.  ``None`` means no expiry (or the
                backend's configured ``default_ttl``).
        """

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove *key* from the cache.

        Args:
            key: Cache key string.

        Returns:
            ``True`` if the key existed and was deleted, ``False`` otherwise.
        """

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return ``True`` if *key* is present and not expired.

        Args:
            key: Cache key string.
        """

    @abstractmethod
    def clear(self) -> None:
        """Remove **all** entries from the cache (or the backend's namespace)."""

    # ------------------------------------------------------------------
    # Bulk operations — default implementations use the primitives above;
    # backends should override with native equivalents where possible.
    # ------------------------------------------------------------------

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Fetch multiple keys in one call.

        Args:
            keys: List of cache key strings.

        Returns:
            Dict mapping each *found* key to its value.  Missing/expired
            keys are omitted from the result.
        """
        result: Dict[str, Any] = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Store multiple key/value pairs at once.

        Args:
            mapping: Dict of ``{key: value}`` pairs.
            ttl: Expiry in seconds applied to **all** keys in *mapping*.
        """
        for key, value in mapping.items():
            self.set(key, value, ttl=ttl)

    def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys.

        Args:
            keys: List of cache key strings.

        Returns:
            Number of keys that were actually present and deleted.
        """
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count

    # ------------------------------------------------------------------
    # Atomic integer counters
    # ------------------------------------------------------------------

    def incr(self, key: str, amount: int = 1) -> int:
        """Atomically increment an integer counter stored at *key*.

        If the key does not exist it is initialised to ``0`` before
        incrementing.

        Args:
            key: Cache key string.
            amount: Amount to add (default ``1``).

        Returns:
            The new integer value after incrementing.

        Raises:
            TypeError: If the existing value is not an integer.
        """
        current = self.get(key)
        if current is None:
            current = 0
        if not isinstance(current, int):
            raise TypeError(
                f"Cache value at '{key}' is not an integer: {type(current).__name__}"
            )
        new_value = current + amount
        self.set(key, new_value)
        return new_value

    def decr(self, key: str, amount: int = 1) -> int:
        """Atomically decrement an integer counter stored at *key*.

        If the key does not exist it is initialised to ``0`` before
        decrementing.

        Args:
            key: Cache key string.
            amount: Amount to subtract (default ``1``).

        Returns:
            The new integer value after decrementing.

        Raises:
            TypeError: If the existing value is not an integer.
        """
        return self.incr(key, amount=-amount)
