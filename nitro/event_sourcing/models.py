"""Domain event and snapshot models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Immutable record of something that happened in the domain.

    Attributes:
        event_id: Unique identifier for this event instance.
        event_type: Name of the event (e.g. "OrderPlaced", "ItemAdded").
        aggregate_id: ID of the aggregate this event belongs to.
        aggregate_type: Type name of the aggregate (e.g. "Order").
        version: Sequence number within the aggregate's event stream.
        timestamp: When the event occurred (UTC).
        data: Event payload — the facts about what happened.
        metadata: Optional context (actor, correlation_id, etc.).
    """

    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    event_type: str
    aggregate_id: str
    aggregate_type: str
    version: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


class Snapshot(BaseModel):
    """Point-in-time capture of aggregate state for fast replay.

    Instead of replaying all events from the beginning, load the latest
    snapshot and only replay events after ``version``.

    Attributes:
        aggregate_id: ID of the aggregate.
        aggregate_type: Type name of the aggregate.
        version: The aggregate version at snapshot time.
        state: Serialised aggregate state.
        timestamp: When the snapshot was taken (UTC).
    """

    aggregate_id: str
    aggregate_type: str
    version: int
    state: dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
