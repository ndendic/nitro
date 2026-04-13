"""
nitro.audit — Immutable audit trail for entity lifecycle events.

Provides:
- AuditEntry       : Pydantic model for a single audit record
- FieldChange      : Pydantic model for a single field-level change
- AuditStore       : Abstract base class for audit storage backends
- MemoryAuditStore : In-memory store (default, for dev/testing)
- AuditTrail       : Main service — record and query audit events
- audit_context    : Context manager to set actor/metadata for a block
- audited          : Decorator to auto-record entity method changes
- get_audit_trail  : Helper to retrieve active trail from context
- get_current_actor: Helper to retrieve active actor from context
- get_current_metadata: Helper to retrieve active metadata from context

Quick start::

    from nitro.audit import AuditTrail, audit_context

    trail = AuditTrail()

    # Record a creation
    trail.record_create(
        entity_type="Order",
        entity_id="order:1",
        snapshot={"status": "pending", "total": 0.0},
        actor="user:42",
    )

    # Record an update (auto-diffs old vs new state)
    trail.record_update(
        entity_type="Order",
        entity_id="order:1",
        old_state={"status": "pending", "total": 0.0},
        new_state={"status": "active", "total": 99.0},
        actor="user:42",
    )

    # Query history
    history = trail.get_history("Order", "order:1")

    # Context manager — set actor for a whole block
    with audit_context(trail, actor="user:7", metadata={"ip": "1.2.3.4"}):
        actor = get_current_actor()   # "user:7"

    # Decorator usage
    from nitro.audit import audited

    class Order:
        def __init__(self):
            self.id = "order:1"
            self.status = "pending"

        def model_dump(self):
            return {"id": self.id, "status": self.status}

        @audited(trail, actor_from="user_id")
        def approve(self, request):
            self.status = "approved"

    # What was the entity before the last change?
    rollback_state = trail.rollback_info("Order", "order:1")
"""

from __future__ import annotations

from .models import AuditEntry, FieldChange
from .store import AuditStore, MemoryAuditStore
from .trail import AuditTrail
from .context import (
    audit_context,
    get_audit_trail,
    get_current_actor,
    get_current_metadata,
)
from .decorators import audited

__all__ = [
    # Models
    "AuditEntry",
    "FieldChange",
    # Storage
    "AuditStore",
    "MemoryAuditStore",
    # Service
    "AuditTrail",
    # Context
    "audit_context",
    "get_audit_trail",
    "get_current_actor",
    "get_current_metadata",
    # Decorator
    "audited",
]
