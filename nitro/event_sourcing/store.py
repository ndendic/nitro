"""Event store backends — abstract base, memory, and SQLite implementations."""

from __future__ import annotations

import json
import sqlite3
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Sequence

from .models import DomainEvent, Snapshot


class EventStore(ABC):
    """Abstract base class for event storage backends."""

    @abstractmethod
    def append(self, events: Sequence[DomainEvent]) -> None:
        """Persist one or more events atomically.

        Raises:
            ConcurrencyError: If expected version doesn't match stored version.
        """

    @abstractmethod
    def load_events(
        self,
        aggregate_id: str,
        *,
        after_version: int = 0,
    ) -> list[DomainEvent]:
        """Load events for an aggregate, optionally after a given version."""

    @abstractmethod
    def load_all_events(
        self,
        *,
        event_type: str | None = None,
        aggregate_type: str | None = None,
        after: datetime | None = None,
    ) -> list[DomainEvent]:
        """Load events across all aggregates with optional filters."""

    def save_snapshot(self, snapshot: Snapshot) -> None:
        """Save an aggregate snapshot. Override in backends that support it."""

    def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        """Load the latest snapshot for an aggregate. Returns None if unsupported."""
        return None


class ConcurrencyError(Exception):
    """Raised when an append conflicts with the stored version."""


# ---------------------------------------------------------------------------
# In-memory implementation
# ---------------------------------------------------------------------------


class MemoryEventStore(EventStore):
    """Thread-safe in-memory event store for development and testing."""

    def __init__(self) -> None:
        self._streams: dict[str, list[DomainEvent]] = {}
        self._snapshots: dict[str, Snapshot] = {}
        self._lock = threading.Lock()

    def append(self, events: Sequence[DomainEvent]) -> None:
        if not events:
            return
        aggregate_id = events[0].aggregate_id
        with self._lock:
            stream = self._streams.setdefault(aggregate_id, [])
            expected = events[0].version - 1
            current = stream[-1].version if stream else 0
            if current != expected:
                raise ConcurrencyError(
                    f"Expected version {expected} but stream is at {current}"
                )
            self._streams[aggregate_id] = stream + list(events)

    def load_events(
        self,
        aggregate_id: str,
        *,
        after_version: int = 0,
    ) -> list[DomainEvent]:
        with self._lock:
            stream = self._streams.get(aggregate_id, [])
            return [e for e in stream if e.version > after_version]

    def load_all_events(
        self,
        *,
        event_type: str | None = None,
        aggregate_type: str | None = None,
        after: datetime | None = None,
    ) -> list[DomainEvent]:
        with self._lock:
            result: list[DomainEvent] = []
            for stream in self._streams.values():
                for e in stream:
                    if event_type and e.event_type != event_type:
                        continue
                    if aggregate_type and e.aggregate_type != aggregate_type:
                        continue
                    if after and e.timestamp <= after:
                        continue
                    result.append(e)
            result.sort(key=lambda e: (e.timestamp, e.version))
            return result

    def save_snapshot(self, snapshot: Snapshot) -> None:
        with self._lock:
            self._snapshots[snapshot.aggregate_id] = snapshot

    def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        with self._lock:
            return self._snapshots.get(aggregate_id)


# ---------------------------------------------------------------------------
# SQLite implementation
# ---------------------------------------------------------------------------


class SQLiteEventStore(EventStore):
    """SQLite-backed event store. Production-ready, single-writer safe.

    Uses a single SQLite database with two tables: ``events`` and ``snapshots``.
    All writes are serialised through SQLite's built-in locking.
    """

    def __init__(self, db_path: str = "events.db") -> None:
        self._db_path = db_path
        self._local = threading.local()
        self._init_db()

    @property
    def _conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self._db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return conn

    def _init_db(self) -> None:
        conn = self._conn
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id       TEXT PRIMARY KEY,
                event_type     TEXT NOT NULL,
                aggregate_id   TEXT NOT NULL,
                aggregate_type TEXT NOT NULL,
                version        INTEGER NOT NULL,
                timestamp      TEXT NOT NULL,
                data           TEXT NOT NULL DEFAULT '{}',
                metadata       TEXT NOT NULL DEFAULT '{}',
                UNIQUE(aggregate_id, version)
            );
            CREATE INDEX IF NOT EXISTS idx_events_aggregate
                ON events(aggregate_id, version);
            CREATE INDEX IF NOT EXISTS idx_events_type
                ON events(event_type);

            CREATE TABLE IF NOT EXISTS snapshots (
                aggregate_id   TEXT PRIMARY KEY,
                aggregate_type TEXT NOT NULL,
                version        INTEGER NOT NULL,
                state          TEXT NOT NULL DEFAULT '{}',
                timestamp      TEXT NOT NULL
            );
            """
        )

    def append(self, events: Sequence[DomainEvent]) -> None:
        if not events:
            return
        conn = self._conn
        try:
            with conn:
                for event in events:
                    conn.execute(
                        """
                        INSERT INTO events
                            (event_id, event_type, aggregate_id, aggregate_type,
                             version, timestamp, data, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event.event_id,
                            event.event_type,
                            event.aggregate_id,
                            event.aggregate_type,
                            event.version,
                            event.timestamp.isoformat(),
                            json.dumps(event.data),
                            json.dumps(event.metadata),
                        ),
                    )
        except sqlite3.IntegrityError as exc:
            raise ConcurrencyError(str(exc)) from exc

    def load_events(
        self,
        aggregate_id: str,
        *,
        after_version: int = 0,
    ) -> list[DomainEvent]:
        rows = self._conn.execute(
            """
            SELECT * FROM events
            WHERE aggregate_id = ? AND version > ?
            ORDER BY version
            """,
            (aggregate_id, after_version),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def load_all_events(
        self,
        *,
        event_type: str | None = None,
        aggregate_type: str | None = None,
        after: datetime | None = None,
    ) -> list[DomainEvent]:
        clauses: list[str] = []
        params: list[str] = []
        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type)
        if aggregate_type:
            clauses.append("aggregate_type = ?")
            params.append(aggregate_type)
        if after:
            clauses.append("timestamp > ?")
            params.append(after.isoformat())
        where = " AND ".join(clauses) if clauses else "1=1"
        rows = self._conn.execute(
            f"SELECT * FROM events WHERE {where} ORDER BY timestamp, version",
            params,
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def save_snapshot(self, snapshot: Snapshot) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO snapshots
                    (aggregate_id, aggregate_type, version, state, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot.aggregate_id,
                    snapshot.aggregate_type,
                    snapshot.version,
                    json.dumps(snapshot.state),
                    snapshot.timestamp.isoformat(),
                ),
            )

    def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        row = self._conn.execute(
            "SELECT * FROM snapshots WHERE aggregate_id = ?",
            (aggregate_id,),
        ).fetchone()
        if row is None:
            return None
        return Snapshot(
            aggregate_id=row["aggregate_id"],
            aggregate_type=row["aggregate_type"],
            version=row["version"],
            state=json.loads(row["state"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> DomainEvent:
        return DomainEvent(
            event_id=row["event_id"],
            event_type=row["event_type"],
            aggregate_id=row["aggregate_id"],
            aggregate_type=row["aggregate_type"],
            version=row["version"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            data=json.loads(row["data"]),
            metadata=json.loads(row["metadata"]),
        )

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn:
            conn.close()
            self._local.conn = None
