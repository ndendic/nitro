"""Aggregate repository — load and save aggregates via an event store."""

from __future__ import annotations

from typing import TypeVar

from .aggregate import Aggregate
from .models import Snapshot
from .store import EventStore

T = TypeVar("T", bound=Aggregate)


class AggregateRepository:
    """Load and save aggregates through an event store.

    Supports optional snapshotting to speed up loading of long-lived
    aggregates.

    Args:
        store: The event store backend to use.
        aggregate_class: The Aggregate subclass this repository manages.
        snapshot_interval: Take a snapshot every N events. 0 = disabled.
    """

    def __init__(
        self,
        store: EventStore,
        aggregate_class: type[T],
        *,
        snapshot_interval: int = 0,
    ) -> None:
        self._store = store
        self._aggregate_class = aggregate_class
        self._snapshot_interval = snapshot_interval

    def save(self, aggregate: T) -> None:
        """Persist pending events and optionally take a snapshot."""
        pending = aggregate.pending_events
        if not pending:
            return
        self._store.append(pending)
        aggregate.clear_pending_events()

        if (
            self._snapshot_interval > 0
            and aggregate.version % self._snapshot_interval == 0
        ):
            snapshot = Snapshot(
                aggregate_id=aggregate.aggregate_id,
                aggregate_type=type(aggregate).__name__,
                version=aggregate.version,
                state=aggregate.take_snapshot_state(),
            )
            self._store.save_snapshot(snapshot)

    def load(self, aggregate_id: str) -> T:
        """Load an aggregate by replaying events (with optional snapshot).

        Raises:
            KeyError: If no events exist for the given aggregate_id.
        """
        aggregate = self._aggregate_class(aggregate_id=aggregate_id)
        after_version = 0

        snapshot = self._store.load_snapshot(aggregate_id)
        if snapshot is not None:
            aggregate.load_from_snapshot(snapshot.state, snapshot.version)
            after_version = snapshot.version

        events = self._store.load_events(
            aggregate_id, after_version=after_version
        )

        if not events and snapshot is None:
            raise KeyError(f"Aggregate {aggregate_id!r} not found")

        aggregate.replay(events)
        return aggregate

    def exists(self, aggregate_id: str) -> bool:
        """Check whether an aggregate has any events."""
        events = self._store.load_events(aggregate_id)
        return len(events) > 0
