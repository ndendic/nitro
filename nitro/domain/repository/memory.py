"""
StarModel Persistence Layer - Memory Backend

In-memory entity persistence implementation for development and testing.
"""

import time
from typing import Any, Dict, List, Optional, Tuple, Type, TYPE_CHECKING

from .base import EntityRepositoryInterface

if TYPE_CHECKING:
    from ..core.entity import Entity


class MemoryRepository(EntityRepositoryInterface):
    """
    In-memory entity persistence implementation (Singleton).

    Provides fast persistence for development and testing.
    Data is lost when the application restarts.
    Uses singleton pattern to ensure single shared instance.

    Storage is keyed by (class_name, entity_id) for type-safe retrieval,
    matching the SQLModelRepository API signature.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize memory persistence backend (only once)."""
        if not self._initialized:
            # Storage keyed by (class_name, entity_id)
            self._data: Dict[Tuple[str, Any], Any] = {}
            self._expiry: Dict[Tuple[str, Any], float] = {}
            MemoryRepository._initialized = True

            # Initialize parent class for cleanup functionality
            super().__init__()

            # Start automatic cleanup by default
            self.start_cleanup()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _key(self, cls_or_entity, entity_id=None) -> Tuple[str, Any]:
        """Build a composite storage key from a class (or instance) and id."""
        if entity_id is None:
            # Called with an entity instance — derive class and id from it
            return (type(cls_or_entity).__name__, cls_or_entity.id)
        return (cls_or_entity.__name__, entity_id)

    def _is_expired(self, key: Tuple[str, Any]) -> bool:
        """Return True if the key has a registered TTL that has elapsed."""
        if key in self._expiry and time.time() > self._expiry[key]:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
            return True
        return False

    # ------------------------------------------------------------------
    # Core API — matches SQLModelRepository
    # ------------------------------------------------------------------

    def save(self, entity, ttl: Optional[int] = None) -> bool:
        """Save entity to memory with optional TTL."""
        try:
            key = self._key(entity)
            self._data[key] = entity
            if ttl:
                self._expiry[key] = time.time() + ttl
            elif key in self._expiry:
                del self._expiry[key]
            return True
        except Exception as e:
            print(f"Error saving entity to memory: {e}")
            return False

    def get(self, cls: Type, entity_id: Any) -> Optional[Any]:
        """Get an entity by class and ID. Alias for find()."""
        return self.find(cls, entity_id)

    def find(self, cls: Type, entity_id: Any) -> Optional[Any]:
        """Load entity from memory by class and ID."""
        try:
            key = self._key(cls, entity_id)
            if self._is_expired(key):
                return None
            return self._data.get(key)
        except Exception as e:
            print(f"Error loading entity from memory: {e}")
            return None

    def delete(self, entity) -> bool:
        """Delete entity from memory (takes an entity instance)."""
        try:
            key = self._key(entity)
            existed = key in self._data
            self._data.pop(key, None)
            self._expiry.pop(key, None)
            return existed
        except Exception as e:
            print(f"Error deleting entity from memory: {e}")
            return False

    def all(self, cls: Type) -> List[Any]:
        """Return all stored entities of the given class."""
        class_name = cls.__name__
        result = []
        for (stored_class, stored_id), entity in list(self._data.items()):
            if stored_class == class_name:
                key = (stored_class, stored_id)
                if not self._is_expired(key):
                    result.append(entity)
        return result

    def exists(self, cls: Type, entity_id: Any) -> bool:
        """Check if entity exists in memory by class and ID."""
        key = self._key(cls, entity_id)
        if self._is_expired(key):
            return False
        return key in self._data

    # ------------------------------------------------------------------
    # Legacy / internal helpers kept for backward compatibility
    # ------------------------------------------------------------------

    def exists_sync(self, entity_id: str) -> bool:
        """
        Legacy check by bare string key (used by existing tests and internal code).

        Searches across all class namespaces for the given id.
        """
        for (stored_class, stored_id) in list(self._data.keys()):
            if stored_id == entity_id:
                key = (stored_class, stored_id)
                if self._is_expired(key):
                    continue
                return True
        return False

    def cleanup_expired_sync(self) -> int:
        """Clean up expired entity entries from memory."""
        try:
            current_time = time.time()
            expired_keys = [
                key for key, expiry_time in list(self._expiry.items())
                if current_time > expiry_time
            ]
            for key in expired_keys:
                self._data.pop(key, None)
                self._expiry.pop(key, None)
            return len(expired_keys)
        except Exception as e:
            print(f"Error cleaning up expired entities: {e}")
            return 0

    def start_cleanup(self, interval: int = 300):
        """
        Start automatic cleanup of expired entities.

        Args:
            interval: Cleanup interval in seconds (default: 300 = 5 minutes)

        Note: This is a placeholder for future async cleanup implementation.
        For now, cleanup happens automatically on access (lazy cleanup).
        """
        # Placeholder for future implementation
        # Current implementation uses lazy cleanup on access
        pass


# Convenience function to get singleton instance
def get_memory_persistence() -> MemoryRepository:
    """Get the singleton memory persistence instance."""
    return MemoryRepository()
