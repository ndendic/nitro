"""
AuditTrail — the main service class for recording and querying audit events.

AuditTrail wraps an AuditStore and provides a high-level API for recording
entity lifecycle events, computing diffs, and retrieving audit history.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import AuditEntry, FieldChange
from .store import AuditStore, MemoryAuditStore


def _compute_diff(
    old_state: Dict[str, Any], new_state: Dict[str, Any]
) -> Dict[str, FieldChange]:
    """Compute field-level diff between two entity state dicts.

    Only fields that actually changed are included.  Fields present in
    *old_state* but absent from *new_state* are treated as removed
    (new_value=None).  Fields absent from *old_state* but present in
    *new_state* are treated as added (old_value=None).

    Args:
        old_state: Entity snapshot before the change.
        new_state: Entity snapshot after the change.

    Returns:
        Dict mapping field name to a ``FieldChange`` instance for every
        field whose value differs between the two states.
    """
    changes: Dict[str, FieldChange] = {}

    all_keys = set(old_state.keys()) | set(new_state.keys())
    for key in all_keys:
        old_val = old_state.get(key)
        new_val = new_state.get(key)
        if old_val != new_val:
            changes[key] = FieldChange(
                field=key, old_value=old_val, new_value=new_val
            )

    return changes


class AuditTrail:
    """Service class for recording and querying entity audit events.

    Wraps an ``AuditStore`` and provides convenience methods for the full
    entity lifecycle: create, update, delete.

    Automatically computes field-level diffs on update, captures full
    snapshots, and delegates storage to the underlying backend.

    Args:
        store: Storage backend.  Defaults to a new ``MemoryAuditStore``
            when not provided.

    Example::

        trail = AuditTrail()

        entry = trail.record_create(
            entity_type="Order",
            entity_id="order:1",
            snapshot={"status": "pending", "total": 0.0},
            actor="user:42",
        )

        updated = trail.record_update(
            entity_type="Order",
            entity_id="order:1",
            old_state={"status": "pending", "total": 0.0},
            new_state={"status": "active", "total": 99.0},
            actor="user:42",
        )
    """

    def __init__(self, store: Optional[AuditStore] = None) -> None:
        self._store: AuditStore = store if store is not None else MemoryAuditStore()

    # ------------------------------------------------------------------
    # Record helpers
    # ------------------------------------------------------------------

    def record_create(
        self,
        entity_type: str,
        entity_id: str,
        snapshot: Dict[str, Any],
        actor: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Record an entity creation event.

        Args:
            entity_type: Entity class name.
            entity_id: Entity identifier.
            snapshot: Full entity state at creation time.
            actor: Who performed the action.
            metadata: Optional extra context (IP, request ID, etc.).

        Returns:
            The persisted ``AuditEntry``.
        """
        entry = AuditEntry(
            entity_type=entity_type,
            entity_id=entity_id,
            action="create",
            actor=actor,
            snapshot=snapshot,
            metadata=metadata or {},
        )
        self._store.append(entry)
        return entry

    def record_update(
        self,
        entity_type: str,
        entity_id: str,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        actor: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Record an entity update event with auto-computed field diff.

        Diffs *old_state* against *new_state* and stores only the changed
        fields in ``entry.changes``.  The ``snapshot`` is set to *new_state*.

        Args:
            entity_type: Entity class name.
            entity_id: Entity identifier.
            old_state: Full entity state before the update.
            new_state: Full entity state after the update.
            actor: Who performed the action.
            metadata: Optional extra context.

        Returns:
            The persisted ``AuditEntry``.
        """
        changes = _compute_diff(old_state, new_state)
        entry = AuditEntry(
            entity_type=entity_type,
            entity_id=entity_id,
            action="update",
            actor=actor,
            changes=changes,
            snapshot=new_state,
            metadata=metadata or {},
        )
        self._store.append(entry)
        return entry

    def record_delete(
        self,
        entity_type: str,
        entity_id: str,
        snapshot: Dict[str, Any],
        actor: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Record an entity deletion event.

        Args:
            entity_type: Entity class name.
            entity_id: Entity identifier.
            snapshot: Full entity state at deletion time (last known state).
            actor: Who performed the action.
            metadata: Optional extra context.

        Returns:
            The persisted ``AuditEntry``.
        """
        entry = AuditEntry(
            entity_type=entity_type,
            entity_id=entity_id,
            action="delete",
            actor=actor,
            snapshot=snapshot,
            metadata=metadata or {},
        )
        self._store.append(entry)
        return entry

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_history(
        self, entity_type: str, entity_id: str
    ) -> List[AuditEntry]:
        """Return all audit entries for an entity, oldest first.

        Args:
            entity_type: Entity class name.
            entity_id: Entity identifier.
        """
        return self._store.get_history(entity_type, entity_id)

    def get_actor_history(
        self, actor: str, limit: int = 100
    ) -> List[AuditEntry]:
        """Return recent audit entries made by a specific actor.

        Args:
            actor: Actor identifier.
            limit: Maximum number of results.
        """
        return self._store.get_by_actor(actor, limit=limit)

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
        """General-purpose filtered query delegating to the store.

        Args:
            entity_type: Filter by entity class name.
            entity_id: Filter by entity identifier.
            actor: Filter by actor.
            action: Filter by action type.
            since: Include entries at or after this UTC datetime.
            until: Include entries at or before this UTC datetime.
            limit: Maximum number of results.
        """
        return self._store.query(
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            action=action,
            since=since,
            until=until,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Analysis helpers
    # ------------------------------------------------------------------

    def diff(
        self,
        entity_type: str,
        entity_id: str,
        entry_a: int = -2,
        entry_b: int = -1,
    ) -> Dict[str, FieldChange]:
        """Compare two audit entries by index and return field-level diff.

        Indexes are applied to the entity's history list (oldest-first).
        Negative indexes work like Python list indexing: -1 is the latest
        entry, -2 is the one before it, etc.

        Args:
            entity_type: Entity class name.
            entity_id: Entity identifier.
            entry_a: Index of the "before" entry (default -2, second-to-last).
            entry_b: Index of the "after" entry (default -1, latest).

        Returns:
            Field-level diff between the snapshots of the two entries.

        Raises:
            IndexError: If the history is too short to satisfy the indexes.
        """
        history = self._store.get_history(entity_type, entity_id)
        snapshot_a = history[entry_a].snapshot
        snapshot_b = history[entry_b].snapshot
        return _compute_diff(snapshot_a, snapshot_b)

    def rollback_info(
        self,
        entity_type: str,
        entity_id: str,
        to_index: int = -2,
    ) -> Dict[str, Any]:
        """Return the snapshot from a previous audit entry.

        Useful for presenting "undo" information — the returned dict is the
        full entity state at the time of the entry at *to_index*.

        Args:
            entity_type: Entity class name.
            entity_id: Entity identifier.
            to_index: History index to read the snapshot from (default -2,
                i.e. the entry before the most recent one).

        Returns:
            A copy of the snapshot dict from the selected entry.

        Raises:
            IndexError: If the history is too short to satisfy *to_index*.
        """
        history = self._store.get_history(entity_type, entity_id)
        return dict(history[to_index].snapshot)

    # ------------------------------------------------------------------
    # Store access
    # ------------------------------------------------------------------

    @property
    def store(self) -> AuditStore:
        """The underlying AuditStore backend."""
        return self._store
