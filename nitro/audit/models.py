"""
Pydantic models for the nitro.audit module.

Defines AuditEntry and FieldChange — the core data structures for the
immutable audit trail.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field


class FieldChange(BaseModel):
    """Tracks a single field-level change within an audit record.

    Args:
        field: Name of the field that changed.
        old_value: Value before the change (None if field was added).
        new_value: Value after the change (None if field was removed).

    Example::

        change = FieldChange(field="status", old_value="pending", new_value="active")
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    field: str
    old_value: Any = None
    new_value: Any = None


class AuditEntry(BaseModel):
    """A single immutable audit record.

    Created automatically by ``AuditTrail`` when entities are created,
    updated, or deleted.  Should not be constructed directly in application
    code — use ``AuditTrail.record_create``, ``record_update``, or
    ``record_delete`` instead.

    Args:
        id: UUID string — auto-generated.
        entity_type: Name of the entity class (e.g. "User", "Order").
        entity_id: Identifier of the specific entity instance.
        action: One of "create", "update", or "delete".
        actor: Who made the change — user ID, "system", etc.
        timestamp: UTC datetime of the change — auto-set to utcnow.
        changes: Field-level diff (populated on "update" actions).
        snapshot: Full entity state at time of the action.
        metadata: Extra context (IP address, request ID, etc.).

    Example::

        entry = AuditEntry(
            entity_type="Order",
            entity_id="order:42",
            action="create",
            actor="user:7",
            snapshot={"status": "pending", "total": 99.0},
        )
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str
    entity_id: str
    action: Literal["create", "update", "delete"]
    actor: str = "system"
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    changes: Dict[str, FieldChange] = Field(default_factory=dict)
    snapshot: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
