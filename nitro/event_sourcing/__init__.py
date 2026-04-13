"""
nitro.event_sourcing — Event sourcing for Nitro entities.

Provides an event sourcing pattern separate from nitro.events (PubSub/SSE).
Event sourcing stores all state changes as immutable events and can rebuild
aggregate state by replaying the event history.

Provides:
- DomainEvent       : Immutable event record (Pydantic model)
- Snapshot          : Aggregate state snapshot for fast replay
- EventStore        : Abstract base class for event storage backends
- MemoryEventStore  : In-memory store (dev/testing)
- SQLiteEventStore  : SQLite-backed store (production-ready)
- Aggregate         : Base class for event-sourced aggregates
- event_handler     : Decorator to register event handlers on aggregates
- AggregateRepository : Load/save aggregates via event store

Quick start::

    from nitro.event_sourcing import Aggregate, event_handler, MemoryEventStore, AggregateRepository

    class BankAccount(Aggregate):
        balance: float = 0.0
        owner: str = ""

        @event_handler("AccountOpened")
        def on_opened(self, event):
            self.owner = event.data["owner"]

        @event_handler("MoneyDeposited")
        def on_deposited(self, event):
            self.balance += event.data["amount"]

        @event_handler("MoneyWithdrawn")
        def on_withdrawn(self, event):
            self.balance -= event.data["amount"]

        def open(self, owner: str):
            self.apply_event("AccountOpened", {"owner": owner})

        def deposit(self, amount: float):
            if amount <= 0:
                raise ValueError("Deposit amount must be positive")
            self.apply_event("MoneyDeposited", {"amount": amount})

        def withdraw(self, amount: float):
            if amount > self.balance:
                raise ValueError("Insufficient funds")
            self.apply_event("MoneyWithdrawn", {"amount": amount})

    store = MemoryEventStore()
    repo = AggregateRepository(store, BankAccount)

    account = BankAccount(aggregate_id="acc-1")
    account.open("Alice")
    account.deposit(100.0)
    account.withdraw(30.0)
    repo.save(account)

    # Reload from events
    loaded = repo.load("acc-1")
    assert loaded.balance == 70.0
    assert loaded.version == 3
"""

from .models import DomainEvent, Snapshot
from .store import EventStore, MemoryEventStore, SQLiteEventStore
from .aggregate import Aggregate, event_handler
from .repository import AggregateRepository

__all__ = [
    "DomainEvent",
    "Snapshot",
    "EventStore",
    "MemoryEventStore",
    "SQLiteEventStore",
    "Aggregate",
    "event_handler",
    "AggregateRepository",
]
