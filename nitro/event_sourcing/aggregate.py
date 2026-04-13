"""Aggregate base class and event handler decorator."""

from __future__ import annotations

import copy
from typing import Any, Callable

from .models import DomainEvent


_HANDLER_ATTR = "__es_event_type__"


def event_handler(event_type: str) -> Callable:
    """Decorator to register a method as handler for a specific event type.

    Usage::

        class Order(Aggregate):
            total: float = 0.0

            @event_handler("ItemAdded")
            def on_item_added(self, event: DomainEvent):
                self.total += event.data["price"]
    """

    def decorator(fn: Callable) -> Callable:
        setattr(fn, _HANDLER_ATTR, event_type)
        return fn

    return decorator


class Aggregate:
    """Base class for event-sourced aggregates.

    Subclasses define state fields as class attributes and register
    ``@event_handler`` methods to mutate state in response to events.

    State is NEVER modified directly — only through ``apply_event()``,
    which records the event and calls the matching handler.

    Attributes:
        aggregate_id: Unique identifier for this aggregate instance.
        version: Number of events applied (0 = new aggregate).
    """

    aggregate_id: str
    version: int

    def __init__(self, aggregate_id: str, **initial_state: Any) -> None:
        self.aggregate_id = aggregate_id
        self.version = 0
        self._pending_events: list[DomainEvent] = []
        self._handlers: dict[str, Callable] = {}

        # Set any initial state defaults from class annotations
        for cls in reversed(type(self).__mro__):
            for attr, _ in getattr(cls, "__annotations__", {}).items():
                if attr in ("aggregate_id", "version"):
                    continue
                if hasattr(cls, attr) and not hasattr(self, attr):
                    setattr(self, attr, getattr(cls, attr))

        # Override with explicit initial state
        for key, value in initial_state.items():
            setattr(self, key, value)

        # Collect event handlers from the class hierarchy
        for cls in reversed(type(self).__mro__):
            for name in vars(cls):
                method = getattr(cls, name)
                event_type = getattr(method, _HANDLER_ATTR, None)
                if event_type is not None:
                    self._handlers[event_type] = getattr(self, name)

    @property
    def pending_events(self) -> list[DomainEvent]:
        """Events applied since last save/load — to be persisted."""
        return list(self._pending_events)

    def clear_pending_events(self) -> None:
        """Clear pending events (called after successful save)."""
        self._pending_events.clear()

    def apply_event(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DomainEvent:
        """Create and apply a new event, advancing the version.

        This is the ONLY way to change aggregate state. The event is recorded
        in ``pending_events`` for later persistence.
        """
        self.version += 1
        event = DomainEvent(
            event_type=event_type,
            aggregate_id=self.aggregate_id,
            aggregate_type=type(self).__name__,
            version=self.version,
            data=data or {},
            metadata=metadata or {},
        )
        self._apply(event)
        self._pending_events.append(event)
        return event

    def replay(self, events: list[DomainEvent]) -> None:
        """Replay historical events to rebuild state. No pending events generated."""
        for event in events:
            self.version = event.version
            self._apply(event)

    def load_from_snapshot(self, state: dict[str, Any], version: int) -> None:
        """Restore aggregate state from a snapshot."""
        for key, value in state.items():
            setattr(self, key, copy.deepcopy(value))
        self.version = version

    def take_snapshot_state(self) -> dict[str, Any]:
        """Serialise current state for snapshotting.

        Returns all instance attributes except internals.
        """
        skip = {"aggregate_id", "version", "_pending_events", "_handlers"}
        return {
            k: v
            for k, v in self.__dict__.items()
            if k not in skip and not k.startswith("__")
        }

    def _apply(self, event: DomainEvent) -> None:
        """Dispatch event to the registered handler, if any."""
        handler = self._handlers.get(event.event_type)
        if handler is not None:
            handler(event)
