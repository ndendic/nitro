"""Tests for the nitro.audit module.

Covers: AuditEntry, FieldChange, MemoryAuditStore, AuditTrail,
        audit_context, @audited decorator, diff/rollback helpers,
        query filtering, edge cases, and timestamp ordering.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

import pytest

from nitro.audit import (
    AuditEntry,
    AuditStore,
    AuditTrail,
    FieldChange,
    MemoryAuditStore,
    audit_context,
    audited,
    get_audit_trail,
    get_current_actor,
    get_current_metadata,
)
from nitro.audit.trail import _compute_diff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_trail() -> AuditTrail:
    """Return a fresh AuditTrail with an empty MemoryAuditStore."""
    return AuditTrail()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# FieldChange model
# ---------------------------------------------------------------------------

class TestFieldChange:
    def test_basic_creation(self):
        fc = FieldChange(field="status", old_value="pending", new_value="active")
        assert fc.field == "status"
        assert fc.old_value == "pending"
        assert fc.new_value == "active"

    def test_defaults_are_none(self):
        fc = FieldChange(field="name")
        assert fc.old_value is None
        assert fc.new_value is None

    def test_accepts_any_types(self):
        fc = FieldChange(field="data", old_value={"x": 1}, new_value=[1, 2, 3])
        assert fc.old_value == {"x": 1}
        assert fc.new_value == [1, 2, 3]

    def test_serialization(self):
        fc = FieldChange(field="count", old_value=0, new_value=5)
        d = fc.model_dump()
        assert d == {"field": "count", "old_value": 0, "new_value": 5}

    def test_field_name_preserved(self):
        fc = FieldChange(field="my_complex_field_name")
        assert fc.field == "my_complex_field_name"

    def test_none_values_explicit(self):
        fc = FieldChange(field="optional_field", old_value=None, new_value=None)
        assert fc.old_value is None
        assert fc.new_value is None


# ---------------------------------------------------------------------------
# AuditEntry model
# ---------------------------------------------------------------------------

class TestAuditEntry:
    def test_basic_creation(self):
        entry = AuditEntry(
            entity_type="User",
            entity_id="user:1",
            action="create",
        )
        assert entry.entity_type == "User"
        assert entry.entity_id == "user:1"
        assert entry.action == "create"

    def test_auto_generates_uuid(self):
        e1 = AuditEntry(entity_type="X", entity_id="1", action="create")
        e2 = AuditEntry(entity_type="X", entity_id="1", action="create")
        assert e1.id != e2.id
        assert len(e1.id) == 36  # UUID format

    def test_default_actor_is_system(self):
        entry = AuditEntry(entity_type="X", entity_id="1", action="create")
        assert entry.actor == "system"

    def test_timestamp_auto_set(self):
        before = utcnow()
        entry = AuditEntry(entity_type="X", entity_id="1", action="create")
        after = utcnow()
        assert before <= entry.timestamp <= after

    def test_timestamp_is_utc_aware(self):
        entry = AuditEntry(entity_type="X", entity_id="1", action="create")
        assert entry.timestamp.tzinfo is not None

    def test_default_empty_collections(self):
        entry = AuditEntry(entity_type="X", entity_id="1", action="create")
        assert entry.changes == {}
        assert entry.snapshot == {}
        assert entry.metadata == {}

    def test_create_action(self):
        entry = AuditEntry(entity_type="X", entity_id="1", action="create")
        assert entry.action == "create"

    def test_update_action(self):
        entry = AuditEntry(entity_type="X", entity_id="1", action="update")
        assert entry.action == "update"

    def test_delete_action(self):
        entry = AuditEntry(entity_type="X", entity_id="1", action="delete")
        assert entry.action == "delete"

    def test_custom_actor(self):
        entry = AuditEntry(
            entity_type="X", entity_id="1", action="create", actor="user:42"
        )
        assert entry.actor == "user:42"

    def test_snapshot_stored(self):
        snap = {"status": "active", "total": 99.0}
        entry = AuditEntry(
            entity_type="Order", entity_id="o:1", action="create", snapshot=snap
        )
        assert entry.snapshot == snap

    def test_metadata_stored(self):
        meta = {"ip": "127.0.0.1", "request_id": "req:abc"}
        entry = AuditEntry(
            entity_type="X", entity_id="1", action="create", metadata=meta
        )
        assert entry.metadata == meta

    def test_changes_stored(self):
        changes = {
            "status": FieldChange(field="status", old_value="pending", new_value="active")
        }
        entry = AuditEntry(
            entity_type="X", entity_id="1", action="update", changes=changes
        )
        assert "status" in entry.changes
        assert entry.changes["status"].new_value == "active"

    def test_serialization_roundtrip(self):
        entry = AuditEntry(
            entity_type="Order",
            entity_id="o:1",
            action="create",
            actor="user:5",
            snapshot={"status": "pending"},
            metadata={"ip": "1.2.3.4"},
        )
        d = entry.model_dump()
        assert d["entity_type"] == "Order"
        assert d["entity_id"] == "o:1"
        assert d["action"] == "create"
        assert d["actor"] == "user:5"


# ---------------------------------------------------------------------------
# _compute_diff (internal helper)
# ---------------------------------------------------------------------------

class TestComputeDiff:
    def test_changed_field(self):
        diff = _compute_diff({"status": "a"}, {"status": "b"})
        assert "status" in diff
        assert diff["status"].old_value == "a"
        assert diff["status"].new_value == "b"

    def test_unchanged_field_excluded(self):
        diff = _compute_diff({"status": "a", "name": "X"}, {"status": "a", "name": "X"})
        assert diff == {}

    def test_added_field(self):
        diff = _compute_diff({}, {"new_field": 42})
        assert "new_field" in diff
        assert diff["new_field"].old_value is None
        assert diff["new_field"].new_value == 42

    def test_removed_field(self):
        diff = _compute_diff({"old_field": "val"}, {})
        assert "old_field" in diff
        assert diff["old_field"].old_value == "val"
        assert diff["old_field"].new_value is None

    def test_mixed_changes(self):
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 1, "b": 99, "d": 4}
        diff = _compute_diff(old, new)
        assert "a" not in diff        # unchanged
        assert "b" in diff            # changed
        assert "c" in diff            # removed
        assert "d" in diff            # added
        assert diff["b"].old_value == 2
        assert diff["b"].new_value == 99

    def test_type_change(self):
        diff = _compute_diff({"count": "5"}, {"count": 5})
        assert "count" in diff

    def test_none_to_value(self):
        diff = _compute_diff({"x": None}, {"x": 10})
        assert "x" in diff
        assert diff["x"].old_value is None
        assert diff["x"].new_value == 10

    def test_value_to_none(self):
        diff = _compute_diff({"x": 10}, {"x": None})
        assert "x" in diff

    def test_empty_both(self):
        diff = _compute_diff({}, {})
        assert diff == {}


# ---------------------------------------------------------------------------
# MemoryAuditStore
# ---------------------------------------------------------------------------

class TestMemoryAuditStore:
    def _entry(self, entity_type="Order", entity_id="o:1", action="create", actor="system"):
        return AuditEntry(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
        )

    def test_append_and_all(self):
        store = MemoryAuditStore()
        e = self._entry()
        store.append(e)
        assert len(store.all()) == 1
        assert store.all()[0] is e

    def test_get_history_returns_correct_entity(self):
        store = MemoryAuditStore()
        e1 = self._entry("Order", "o:1")
        e2 = self._entry("Order", "o:2")
        store.append(e1)
        store.append(e2)
        history = store.get_history("Order", "o:1")
        assert len(history) == 1
        assert history[0] is e1

    def test_get_history_ordering_oldest_first(self):
        store = MemoryAuditStore()
        for i in range(3):
            store.append(self._entry("Order", "o:1", action="update"))
        history = store.get_history("Order", "o:1")
        assert len(history) == 3
        # timestamps should be non-decreasing
        for i in range(len(history) - 1):
            assert history[i].timestamp <= history[i + 1].timestamp

    def test_get_history_empty(self):
        store = MemoryAuditStore()
        assert store.get_history("Order", "nonexistent") == []

    def test_get_by_actor(self):
        store = MemoryAuditStore()
        store.append(self._entry(actor="user:1"))
        store.append(self._entry(actor="user:2"))
        store.append(self._entry(actor="user:1"))
        results = store.get_by_actor("user:1")
        assert len(results) == 2
        assert all(e.actor == "user:1" for e in results)

    def test_get_by_actor_limit(self):
        store = MemoryAuditStore()
        for _ in range(10):
            store.append(self._entry(actor="user:1"))
        assert len(store.get_by_actor("user:1", limit=3)) == 3

    def test_get_by_action(self):
        store = MemoryAuditStore()
        store.append(self._entry(action="create"))
        store.append(self._entry(action="update"))
        store.append(self._entry(action="delete"))
        store.append(self._entry(action="create"))
        creates = store.get_by_action("create")
        assert len(creates) == 2

    def test_get_by_action_limit(self):
        store = MemoryAuditStore()
        for _ in range(10):
            store.append(self._entry(action="update"))
        assert len(store.get_by_action("update", limit=5)) == 5

    def test_count_all(self):
        store = MemoryAuditStore()
        assert store.count() == 0
        store.append(self._entry("Order", "o:1"))
        store.append(self._entry("User", "u:1"))
        assert store.count() == 2

    def test_count_by_entity_type(self):
        store = MemoryAuditStore()
        store.append(self._entry("Order", "o:1"))
        store.append(self._entry("Order", "o:2"))
        store.append(self._entry("User", "u:1"))
        assert store.count("Order") == 2
        assert store.count("User") == 1
        assert store.count("Unknown") == 0

    def test_query_by_entity_type(self):
        store = MemoryAuditStore()
        store.append(self._entry("Order", "o:1"))
        store.append(self._entry("User", "u:1"))
        results = store.query(entity_type="Order")
        assert len(results) == 1
        assert results[0].entity_type == "Order"

    def test_query_by_entity_id(self):
        store = MemoryAuditStore()
        store.append(self._entry("Order", "o:1"))
        store.append(self._entry("Order", "o:2"))
        results = store.query(entity_id="o:1")
        assert len(results) == 1

    def test_query_by_actor(self):
        store = MemoryAuditStore()
        store.append(self._entry(actor="user:1"))
        store.append(self._entry(actor="user:2"))
        results = store.query(actor="user:1")
        assert len(results) == 1

    def test_query_by_action(self):
        store = MemoryAuditStore()
        store.append(self._entry(action="create"))
        store.append(self._entry(action="update"))
        results = store.query(action="update")
        assert len(results) == 1
        assert results[0].action == "update"

    def test_query_since(self):
        store = MemoryAuditStore()
        past = utcnow() - timedelta(hours=2)
        future = utcnow() + timedelta(hours=2)
        old_entry = AuditEntry(
            entity_type="X", entity_id="1", action="create",
            timestamp=past
        )
        new_entry = AuditEntry(
            entity_type="X", entity_id="1", action="update",
            timestamp=future
        )
        store.append(old_entry)
        store.append(new_entry)
        threshold = utcnow()
        results = store.query(since=threshold)
        assert len(results) == 1
        assert results[0].action == "update"

    def test_query_until(self):
        store = MemoryAuditStore()
        past = utcnow() - timedelta(hours=2)
        future = utcnow() + timedelta(hours=2)
        old_entry = AuditEntry(
            entity_type="X", entity_id="1", action="create",
            timestamp=past
        )
        new_entry = AuditEntry(
            entity_type="X", entity_id="1", action="update",
            timestamp=future
        )
        store.append(old_entry)
        store.append(new_entry)
        threshold = utcnow()
        results = store.query(until=threshold)
        assert len(results) == 1
        assert results[0].action == "create"

    def test_query_combined_filters(self):
        store = MemoryAuditStore()
        store.append(self._entry("Order", "o:1", action="create", actor="user:1"))
        store.append(self._entry("Order", "o:1", action="update", actor="user:1"))
        store.append(self._entry("Order", "o:2", action="create", actor="user:2"))
        results = store.query(entity_type="Order", entity_id="o:1", actor="user:1")
        assert len(results) == 2

    def test_query_limit(self):
        store = MemoryAuditStore()
        for _ in range(20):
            store.append(self._entry())
        assert len(store.query(limit=5)) == 5

    def test_query_no_filters_returns_all(self):
        store = MemoryAuditStore()
        for _ in range(3):
            store.append(self._entry())
        assert len(store.query(limit=100)) == 3

    def test_clear(self):
        store = MemoryAuditStore()
        store.append(self._entry())
        store.append(self._entry())
        store.clear()
        assert store.count() == 0

    def test_is_abstract_store_subclass(self):
        store = MemoryAuditStore()
        assert isinstance(store, AuditStore)


# ---------------------------------------------------------------------------
# AuditTrail — record_create
# ---------------------------------------------------------------------------

class TestAuditTrailRecordCreate:
    def test_returns_entry(self):
        trail = make_trail()
        entry = trail.record_create("Order", "o:1", snapshot={"status": "pending"})
        assert isinstance(entry, AuditEntry)

    def test_action_is_create(self):
        trail = make_trail()
        entry = trail.record_create("Order", "o:1", snapshot={})
        assert entry.action == "create"

    def test_entity_type_and_id(self):
        trail = make_trail()
        entry = trail.record_create("User", "u:99", snapshot={})
        assert entry.entity_type == "User"
        assert entry.entity_id == "u:99"

    def test_snapshot_captured(self):
        trail = make_trail()
        snap = {"name": "Alice", "email": "a@example.com"}
        entry = trail.record_create("User", "u:1", snapshot=snap)
        assert entry.snapshot == snap

    def test_default_actor_is_system(self):
        trail = make_trail()
        entry = trail.record_create("X", "1", snapshot={})
        assert entry.actor == "system"

    def test_custom_actor(self):
        trail = make_trail()
        entry = trail.record_create("X", "1", snapshot={}, actor="user:5")
        assert entry.actor == "user:5"

    def test_metadata_stored(self):
        trail = make_trail()
        meta = {"ip": "10.0.0.1"}
        entry = trail.record_create("X", "1", snapshot={}, metadata=meta)
        assert entry.metadata == meta

    def test_no_changes_on_create(self):
        trail = make_trail()
        entry = trail.record_create("X", "1", snapshot={"a": 1})
        assert entry.changes == {}

    def test_entry_persisted_in_store(self):
        trail = make_trail()
        trail.record_create("Order", "o:1", snapshot={})
        assert trail.store.count() == 1


# ---------------------------------------------------------------------------
# AuditTrail — record_update
# ---------------------------------------------------------------------------

class TestAuditTrailRecordUpdate:
    def test_action_is_update(self):
        trail = make_trail()
        entry = trail.record_update("X", "1", old_state={}, new_state={})
        assert entry.action == "update"

    def test_changes_computed(self):
        trail = make_trail()
        old = {"status": "pending", "total": 0.0}
        new = {"status": "active", "total": 99.0}
        entry = trail.record_update("Order", "o:1", old_state=old, new_state=new)
        assert "status" in entry.changes
        assert "total" in entry.changes
        assert entry.changes["status"].old_value == "pending"
        assert entry.changes["status"].new_value == "active"

    def test_unchanged_fields_excluded_from_changes(self):
        trail = make_trail()
        old = {"a": 1, "b": 2}
        new = {"a": 1, "b": 99}
        entry = trail.record_update("X", "1", old_state=old, new_state=new)
        assert "a" not in entry.changes
        assert "b" in entry.changes

    def test_snapshot_is_new_state(self):
        trail = make_trail()
        new = {"status": "active"}
        entry = trail.record_update("X", "1", old_state={}, new_state=new)
        assert entry.snapshot == new

    def test_no_changes_when_states_identical(self):
        trail = make_trail()
        state = {"x": 1, "y": 2}
        entry = trail.record_update("X", "1", old_state=state, new_state=dict(state))
        assert entry.changes == {}

    def test_actor_propagated(self):
        trail = make_trail()
        entry = trail.record_update("X", "1", old_state={}, new_state={}, actor="admin")
        assert entry.actor == "admin"


# ---------------------------------------------------------------------------
# AuditTrail — record_delete
# ---------------------------------------------------------------------------

class TestAuditTrailRecordDelete:
    def test_action_is_delete(self):
        trail = make_trail()
        entry = trail.record_delete("X", "1", snapshot={})
        assert entry.action == "delete"

    def test_snapshot_is_last_known_state(self):
        trail = make_trail()
        snap = {"status": "active", "total": 50.0}
        entry = trail.record_delete("Order", "o:1", snapshot=snap)
        assert entry.snapshot == snap

    def test_no_changes_on_delete(self):
        trail = make_trail()
        entry = trail.record_delete("X", "1", snapshot={})
        assert entry.changes == {}

    def test_actor_propagated(self):
        trail = make_trail()
        entry = trail.record_delete("X", "1", snapshot={}, actor="user:7")
        assert entry.actor == "user:7"


# ---------------------------------------------------------------------------
# AuditTrail — get_history and get_actor_history
# ---------------------------------------------------------------------------

class TestAuditTrailHistory:
    def test_get_history_all_entries_for_entity(self):
        trail = make_trail()
        trail.record_create("Order", "o:1", snapshot={"s": "a"})
        trail.record_update("Order", "o:1", old_state={"s": "a"}, new_state={"s": "b"})
        trail.record_delete("Order", "o:1", snapshot={"s": "b"})
        history = trail.get_history("Order", "o:1")
        assert len(history) == 3

    def test_get_history_excludes_other_entities(self):
        trail = make_trail()
        trail.record_create("Order", "o:1", snapshot={})
        trail.record_create("Order", "o:2", snapshot={})
        trail.record_create("User", "u:1", snapshot={})
        history = trail.get_history("Order", "o:1")
        assert len(history) == 1

    def test_get_history_empty(self):
        trail = make_trail()
        assert trail.get_history("Order", "missing") == []

    def test_get_actor_history(self):
        trail = make_trail()
        trail.record_create("X", "1", snapshot={}, actor="user:1")
        trail.record_create("X", "2", snapshot={}, actor="user:2")
        trail.record_create("X", "3", snapshot={}, actor="user:1")
        results = trail.get_actor_history("user:1")
        assert len(results) == 2
        assert all(e.actor == "user:1" for e in results)

    def test_get_actor_history_limit(self):
        trail = make_trail()
        for i in range(20):
            trail.record_create("X", f"{i}", snapshot={}, actor="user:1")
        assert len(trail.get_actor_history("user:1", limit=5)) == 5


# ---------------------------------------------------------------------------
# AuditTrail — query
# ---------------------------------------------------------------------------

class TestAuditTrailQuery:
    def test_query_no_filter(self):
        trail = make_trail()
        for i in range(5):
            trail.record_create("X", f"{i}", snapshot={})
        assert len(trail.query()) == 5

    def test_query_by_entity_type(self):
        trail = make_trail()
        trail.record_create("Order", "o:1", snapshot={})
        trail.record_create("User", "u:1", snapshot={})
        results = trail.query(entity_type="Order")
        assert len(results) == 1

    def test_query_by_action(self):
        trail = make_trail()
        trail.record_create("X", "1", snapshot={})
        trail.record_update("X", "1", old_state={}, new_state={"x": 1})
        results = trail.query(action="create")
        assert len(results) == 1

    def test_query_since_filters_old(self):
        trail = make_trail()
        past_entry = AuditEntry(
            entity_type="X", entity_id="1", action="create",
            timestamp=utcnow() - timedelta(hours=3)
        )
        trail.store.append(past_entry)
        trail.record_create("X", "2", snapshot={})  # recent
        results = trail.query(since=utcnow() - timedelta(hours=1))
        assert len(results) == 1
        assert results[0].entity_id == "2"

    def test_query_limit(self):
        trail = make_trail()
        for i in range(10):
            trail.record_create("X", f"{i}", snapshot={})
        assert len(trail.query(limit=4)) == 4


# ---------------------------------------------------------------------------
# AuditTrail — diff
# ---------------------------------------------------------------------------

class TestAuditTrailDiff:
    def test_diff_last_two(self):
        trail = make_trail()
        trail.record_create("Order", "o:1", snapshot={"status": "pending", "total": 0.0})
        trail.record_update(
            "Order", "o:1",
            old_state={"status": "pending", "total": 0.0},
            new_state={"status": "active", "total": 99.0},
        )
        diff = trail.diff("Order", "o:1")
        assert "status" in diff
        assert "total" in diff

    def test_diff_no_changes(self):
        trail = make_trail()
        state = {"x": 1}
        trail.record_create("X", "1", snapshot=state)
        trail.record_update("X", "1", old_state=state, new_state=dict(state))
        diff = trail.diff("X", "1")
        assert diff == {}

    def test_diff_by_explicit_indexes(self):
        trail = make_trail()
        trail.record_create("X", "1", snapshot={"a": 1})
        trail.record_update("X", "1", old_state={"a": 1}, new_state={"a": 2})
        trail.record_update("X", "1", old_state={"a": 2}, new_state={"a": 3})
        # diff entries 0 and 2 (first vs last)
        diff = trail.diff("X", "1", entry_a=0, entry_b=2)
        assert "a" in diff
        assert diff["a"].old_value == 1
        assert diff["a"].new_value == 3

    def test_diff_raises_on_missing_history(self):
        trail = make_trail()
        with pytest.raises(IndexError):
            trail.diff("X", "nonexistent")


# ---------------------------------------------------------------------------
# AuditTrail — rollback_info
# ---------------------------------------------------------------------------

class TestAuditTrailRollbackInfo:
    def test_rollback_returns_previous_snapshot(self):
        trail = make_trail()
        trail.record_create("Order", "o:1", snapshot={"status": "pending"})
        trail.record_update(
            "Order", "o:1",
            old_state={"status": "pending"},
            new_state={"status": "active"},
        )
        rollback = trail.rollback_info("Order", "o:1")
        assert rollback == {"status": "pending"}

    def test_rollback_returns_copy(self):
        trail = make_trail()
        trail.record_create("Order", "o:1", snapshot={"x": 1})
        trail.record_update("Order", "o:1", old_state={"x": 1}, new_state={"x": 2})
        rollback = trail.rollback_info("Order", "o:1")
        rollback["x"] = 999  # mutate the result
        # original history unchanged
        assert trail.get_history("Order", "o:1")[0].snapshot["x"] == 1

    def test_rollback_to_specific_index(self):
        trail = make_trail()
        trail.record_create("X", "1", snapshot={"v": 1})
        trail.record_update("X", "1", old_state={"v": 1}, new_state={"v": 2})
        trail.record_update("X", "1", old_state={"v": 2}, new_state={"v": 3})
        # to_index=0 → first ever snapshot
        rollback = trail.rollback_info("X", "1", to_index=0)
        assert rollback["v"] == 1

    def test_rollback_raises_on_empty_history(self):
        trail = make_trail()
        with pytest.raises(IndexError):
            trail.rollback_info("X", "missing")


# ---------------------------------------------------------------------------
# audit_context context manager
# ---------------------------------------------------------------------------

class TestAuditContext:
    def test_sets_active_trail(self):
        trail = make_trail()
        assert get_audit_trail() is None
        with audit_context(trail):
            assert get_audit_trail() is trail

    def test_clears_trail_after_exit(self):
        trail = make_trail()
        with audit_context(trail):
            pass
        assert get_audit_trail() is None

    def test_sets_actor(self):
        trail = make_trail()
        with audit_context(trail, actor="user:42"):
            assert get_current_actor() == "user:42"

    def test_clears_actor_after_exit(self):
        trail = make_trail()
        with audit_context(trail, actor="user:42"):
            pass
        assert get_current_actor() is None

    def test_sets_metadata(self):
        trail = make_trail()
        meta = {"ip": "1.2.3.4"}
        with audit_context(trail, metadata=meta):
            assert get_current_metadata() == meta

    def test_clears_metadata_after_exit(self):
        trail = make_trail()
        with audit_context(trail, metadata={"x": 1}):
            pass
        assert get_current_metadata() is None

    def test_nested_contexts(self):
        trail1 = make_trail()
        trail2 = make_trail()
        with audit_context(trail1, actor="outer"):
            assert get_current_actor() == "outer"
            with audit_context(trail2, actor="inner"):
                assert get_current_actor() == "inner"
                assert get_audit_trail() is trail2
            # outer context restored
            assert get_current_actor() == "outer"
            assert get_audit_trail() is trail1

    def test_yields_trail(self):
        trail = make_trail()
        with audit_context(trail) as t:
            assert t is trail

    def test_default_actor_is_system(self):
        trail = make_trail()
        with audit_context(trail):
            assert get_current_actor() == "system"

    def test_default_metadata_is_empty_dict(self):
        trail = make_trail()
        with audit_context(trail):
            assert get_current_metadata() == {}

    def test_context_restored_after_exception(self):
        trail = make_trail()
        try:
            with audit_context(trail, actor="user:1"):
                raise ValueError("test error")
        except ValueError:
            pass
        assert get_audit_trail() is None
        assert get_current_actor() is None


# ---------------------------------------------------------------------------
# @audited decorator — sync
# ---------------------------------------------------------------------------

class SimpleEntity:
    """Minimal entity-like class for decorator tests."""

    def __init__(self, id: str, status: str = "pending"):
        self.id = id
        self.status = status

    def model_dump(self) -> Dict[str, Any]:
        return {"id": self.id, "status": self.status}


class TestAuditedDecoratorSync:
    def test_records_update(self):
        trail = make_trail()

        class Order(SimpleEntity):
            @audited(trail)
            def activate(self):
                self.status = "active"

        o = Order("o:1")
        o.activate()
        history = trail.get_history("Order", "o:1")
        assert len(history) == 1
        assert history[0].action == "update"

    def test_captures_before_and_after(self):
        trail = make_trail()

        class Order(SimpleEntity):
            @audited(trail)
            def activate(self):
                self.status = "active"

        o = Order("o:1", status="pending")
        o.activate()
        entry = trail.get_history("Order", "o:1")[0]
        assert "status" in entry.changes
        assert entry.changes["status"].old_value == "pending"
        assert entry.changes["status"].new_value == "active"

    def test_actor_extracted_from_request(self):
        trail = make_trail()

        class FakeRequest:
            user_id = "user:99"

        class Order(SimpleEntity):
            @audited(trail, actor_from="user_id")
            def activate(self, request):
                self.status = "active"

        o = Order("o:1")
        o.activate(FakeRequest())
        entry = trail.get_history("Order", "o:1")[0]
        assert entry.actor == "user:99"

    def test_actor_defaults_to_system_when_no_request(self):
        trail = make_trail()

        class Order(SimpleEntity):
            @audited(trail)
            def activate(self):
                self.status = "active"

        o = Order("o:1")
        o.activate()
        entry = trail.get_history("Order", "o:1")[0]
        assert entry.actor == "system"

    def test_actor_fallback_on_missing_attribute(self):
        trail = make_trail()

        class FakeRequest:
            pass  # no user_id attribute

        class Order(SimpleEntity):
            @audited(trail, actor_from="user_id")
            def activate(self, request):
                self.status = "active"

        o = Order("o:1")
        o.activate(FakeRequest())
        entry = trail.get_history("Order", "o:1")[0]
        assert entry.actor == "system"

    def test_return_value_preserved(self):
        trail = make_trail()

        class Order(SimpleEntity):
            @audited(trail)
            def get_id(self):
                return self.id

        o = Order("o:5")
        result = o.get_id()
        assert result == "o:5"

    def test_create_action_override(self):
        trail = make_trail()

        class Order(SimpleEntity):
            @audited(trail, action="create")
            def initialize(self):
                pass

        o = Order("o:1")
        o.initialize()
        entry = trail.get_history("Order", "o:1")[0]
        assert entry.action == "create"

    def test_delete_action_override(self):
        trail = make_trail()

        class Order(SimpleEntity):
            @audited(trail, action="delete")
            def remove(self):
                pass

        o = Order("o:1")
        o.remove()
        entry = trail.get_history("Order", "o:1")[0]
        assert entry.action == "delete"


# ---------------------------------------------------------------------------
# @audited decorator — async
# ---------------------------------------------------------------------------

class TestAuditedDecoratorAsync:
    def test_async_method_recorded(self):
        trail = make_trail()

        class Order(SimpleEntity):
            @audited(trail)
            async def async_activate(self):
                self.status = "active"

        async def run():
            o = Order("o:1", status="pending")
            await o.async_activate()
            return trail.get_history("Order", "o:1")

        history = asyncio.run(run())
        assert len(history) == 1
        assert history[0].action == "update"

    def test_async_changes_captured(self):
        trail = make_trail()

        class Order(SimpleEntity):
            @audited(trail)
            async def update_status(self):
                self.status = "shipped"

        async def run():
            o = Order("o:1", status="pending")
            await o.update_status()
            return trail.get_history("Order", "o:1")

        history = asyncio.run(run())
        entry = history[0]
        assert entry.changes["status"].old_value == "pending"
        assert entry.changes["status"].new_value == "shipped"

    def test_async_return_value_preserved(self):
        trail = make_trail()

        class Order(SimpleEntity):
            @audited(trail)
            async def get_status(self):
                return self.status

        async def run():
            o = Order("o:1", status="active")
            return await o.get_status()

        result = asyncio.run(run())
        assert result == "active"

    def test_async_actor_from_request(self):
        trail = make_trail()

        class FakeRequest:
            user_id = "user:77"

        class Order(SimpleEntity):
            @audited(trail, actor_from="user_id")
            async def async_activate(self, request):
                self.status = "active"

        async def run():
            o = Order("o:1")
            await o.async_activate(FakeRequest())
            return trail.get_history("Order", "o:1")

        history = asyncio.run(run())
        assert history[0].actor == "user:77"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_history_diff_raises(self):
        trail = make_trail()
        with pytest.raises(IndexError):
            trail.diff("X", "nonexistent")

    def test_single_entry_diff_raises_index_error(self):
        trail = make_trail()
        trail.record_create("X", "1", snapshot={"a": 1})
        # Only one entry, -2 index out of range
        with pytest.raises(IndexError):
            trail.diff("X", "1")

    def test_no_changes_update_produces_empty_changes(self):
        trail = make_trail()
        state = {"x": 1, "y": "hello"}
        entry = trail.record_update("X", "1", old_state=state, new_state=dict(state))
        assert entry.changes == {}

    def test_multiple_entities_interleaved(self):
        trail = make_trail()
        trail.record_create("Order", "o:1", snapshot={"status": "a"})
        trail.record_create("User", "u:1", snapshot={"name": "Alice"})
        trail.record_update("Order", "o:1", old_state={"status": "a"}, new_state={"status": "b"})
        trail.record_update("User", "u:1", old_state={"name": "Alice"}, new_state={"name": "Bob"})

        order_history = trail.get_history("Order", "o:1")
        user_history = trail.get_history("User", "u:1")
        assert len(order_history) == 2
        assert len(user_history) == 2
        assert order_history[0].entity_type == "Order"
        assert user_history[0].entity_type == "User"

    def test_timestamps_ordered(self):
        trail = make_trail()
        for _ in range(5):
            trail.record_create("X", "1", snapshot={})
        history = trail.get_history("X", "1")
        for i in range(len(history) - 1):
            assert history[i].timestamp <= history[i + 1].timestamp

    def test_metadata_none_defaults_to_empty(self):
        trail = make_trail()
        entry = trail.record_create("X", "1", snapshot={}, metadata=None)
        assert entry.metadata == {}

    def test_store_accessible_via_property(self):
        store = MemoryAuditStore()
        trail = AuditTrail(store=store)
        assert trail.store is store

    def test_default_store_is_memory_store(self):
        trail = AuditTrail()
        assert isinstance(trail.store, MemoryAuditStore)

    def test_custom_store_used(self):
        store = MemoryAuditStore()
        trail = AuditTrail(store=store)
        trail.record_create("X", "1", snapshot={})
        assert store.count() == 1
