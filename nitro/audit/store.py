"""
AuditStore ABC and MemoryAuditStore implementation.

``AuditStore`` defines the interface all storage backends must implement.
``MemoryAuditStore`` is the default in-memory implementation suitable for
development and testing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from .models import AuditEntry


class AuditStore(ABC):
    """Abstract base class for audit storage backends.

    All backends must implement every abstract method.  The ``query``
    method is the general-purpose filter, while the convenience helpers
    (``get_history``, ``get_by_actor``, ``get_by_action``) delegate to it
    with pre-filled parameters.

    Backends can override the convenience helpers with optimised
    implementations (e.g. indexed lookups) while keeping ``query`` as the
    fallback.
    """

    @abstractmethod
    def append(self, entry: AuditEntry) -> None:
        """Persist a new audit entry.

        Args:
            entry: The ``AuditEntry`` to store.  Implementations must
                treat entries as immutable once appended.
        """

    @abstractmethod
    def get_history(
        self, entity_type: str, entity_id: str
    ) -> List[AuditEntry]:
        """Return all audit entries for a specific entity, oldest first.

        Args:
            entity_type: Entity class name (e.g. "User").
            entity_id: Specific entity identifier.

        Returns:
            List of matching entries ordered by timestamp ascending.
        """

    @abstractmethod
    def get_by_actor(self, actor: str, limit: int = 100) -> List[AuditEntry]:
        """Return recent audit entries made by a specific actor.

        Args:
            actor: Actor identifier string.
            limit: Maximum number of entries to return.

        Returns:
            List of matching entries, most-recent first.
        """

    @abstractmethod
    def get_by_action(
        self, action: str, limit: int = 100
    ) -> List[AuditEntry]:
        """Return recent audit entries with a specific action type.

        Args:
            action: One of "create", "update", "delete".
            limit: Maximum number of entries to return.

        Returns:
            List of matching entries, most-recent first.
        """

    @abstractmethod
    def query(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """General-purpose filtered query.

        All parameters are optional — providing none returns up to *limit*
        most-recent entries.  Multiple filters are ANDed together.

        Args:
            entity_type: Filter by entity class name.
            entity_id: Filter by entity identifier.
            actor: Filter by actor.
            action: Filter by action type.
            since: Include only entries at or after this datetime (UTC).
            until: Include only entries at or before this datetime (UTC).
            limit: Maximum number of results.

        Returns:
            Matching entries, most-recent first.
        """

    @abstractmethod
    def count(self, entity_type: Optional[str] = None) -> int:
        """Return the total number of stored entries.

        Args:
            entity_type: If given, count only entries for this entity type.

        Returns:
            Integer count.
        """


class MemoryAuditStore(AuditStore):
    """In-memory list-based audit store.

    Thread-safety: this implementation is *not* thread-safe.  For
    production use-cases with concurrency, replace with a persistent
    backend (SQL, Elasticsearch, etc.).

    All entries are kept in a single list in insertion order.  Queries
    scan the full list — appropriate for development, testing, and
    low-volume scenarios.

    Example::

        store = MemoryAuditStore()
        store.append(entry)
        history = store.get_history("Order", "order:42")
    """

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    # ------------------------------------------------------------------
    # AuditStore interface
    # ------------------------------------------------------------------

    def append(self, entry: AuditEntry) -> None:
        """Append *entry* to the in-memory list.

        Args:
            entry: AuditEntry to store.
        """
        self._entries.append(entry)

    def get_history(
        self, entity_type: str, entity_id: str
    ) -> List[AuditEntry]:
        """Return all entries for an entity, oldest first.

        Args:
            entity_type: Entity class name.
            entity_id: Entity identifier.
        """
        return [
            e
            for e in self._entries
            if e.entity_type == entity_type and e.entity_id == entity_id
        ]

    def get_by_actor(self, actor: str, limit: int = 100) -> List[AuditEntry]:
        """Return entries by actor, most-recent first.

        Args:
            actor: Actor identifier.
            limit: Max results.
        """
        matches = [e for e in reversed(self._entries) if e.actor == actor]
        return matches[:limit]

    def get_by_action(
        self, action: str, limit: int = 100
    ) -> List[AuditEntry]:
        """Return entries by action type, most-recent first.

        Args:
            action: "create", "update", or "delete".
            limit: Max results.
        """
        matches = [e for e in reversed(self._entries) if e.action == action]
        return matches[:limit]

    def query(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """General-purpose filtered query, most-recent first.

        Args:
            entity_type: Filter by entity class name.
            entity_id: Filter by entity identifier.
            actor: Filter by actor.
            action: Filter by action type.
            since: Include entries at or after this UTC datetime.
            until: Include entries at or before this UTC datetime.
            limit: Maximum number of results.
        """
        results = []
        for entry in reversed(self._entries):
            if entity_type is not None and entry.entity_type != entity_type:
                continue
            if entity_id is not None and entry.entity_id != entity_id:
                continue
            if actor is not None and entry.actor != actor:
                continue
            if action is not None and entry.action != action:
                continue
            # Normalise to UTC-aware for comparison
            ts = entry.timestamp
            if ts.tzinfo is None:
                from datetime import timezone
                ts = ts.replace(tzinfo=timezone.utc)
            if since is not None:
                _since = since
                if _since.tzinfo is None:
                    from datetime import timezone
                    _since = _since.replace(tzinfo=timezone.utc)
                if ts < _since:
                    continue
            if until is not None:
                _until = until
                if _until.tzinfo is None:
                    from datetime import timezone
                    _until = _until.replace(tzinfo=timezone.utc)
                if ts > _until:
                    continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results

    def count(self, entity_type: Optional[str] = None) -> int:
        """Return the count of stored entries.

        Args:
            entity_type: If given, count only entries of this type.
        """
        if entity_type is None:
            return len(self._entries)
        return sum(1 for e in self._entries if e.entity_type == entity_type)

    # ------------------------------------------------------------------
    # Dev convenience
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all entries (useful in tests)."""
        self._entries.clear()

    def all(self) -> List[AuditEntry]:
        """Return all entries in insertion order."""
        return list(self._entries)
