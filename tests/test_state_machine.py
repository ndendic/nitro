"""
Tests for nitro.domain.mixins.StateMachineMixin — finite state machine behavior.

Covers: state initialization, valid/invalid transitions, lifecycle hooks,
terminal states, available_transitions, in_state query, composition with
other mixins, and edge cases.
"""

import pytest
from sqlmodel import Field

from nitro.domain.entities.base_entity import Entity
from nitro.domain.mixins import (
    InvalidTransition,
    StateMachineMixin,
    TimestampMixin,
    SoftDeleteMixin,
)


# ---------------------------------------------------------------------------
# Test entities
# ---------------------------------------------------------------------------


class Order(Entity, StateMachineMixin, table=True):
    """Typical order workflow."""
    __tablename__ = "test_orders"
    __states__ = {
        "draft":     ["submitted", "cancelled"],
        "submitted": ["approved", "rejected"],
        "approved":  ["shipped"],
        "shipped":   ["delivered"],
        "delivered": [],
        "rejected":  [],
        "cancelled": [],
    }
    __initial_state__ = "draft"

    customer: str = ""


class Ticket(Entity, StateMachineMixin, table=True):
    """Support ticket with hooks."""
    __tablename__ = "test_tickets"
    __states__ = {
        "open":        ["in_progress", "closed"],
        "in_progress": ["open", "closed"],
        "closed":      ["open"],  # can reopen
    }
    __initial_state__ = "open"

    subject: str = ""
    hook_log: str = Field(default="")

    def on_exit_open(self):
        self.hook_log += "exit_open;"

    def on_enter_in_progress(self):
        self.hook_log += "enter_in_progress;"

    def on_enter_closed(self):
        self.hook_log += "enter_closed;"

    def on_exit_closed(self):
        self.hook_log += "exit_closed;"

    def on_enter_open(self):
        self.hook_log += "enter_open;"


class MinimalState(Entity, StateMachineMixin, table=True):
    """Entity with no __states__ defined — everything is open."""
    __tablename__ = "test_minimal_state"
    label: str = ""


class ComposedStateful(Entity, TimestampMixin, SoftDeleteMixin, StateMachineMixin, table=True):
    """State machine composed with other mixins."""
    __tablename__ = "test_composed_stateful"
    __states__ = {
        "pending":  ["active", "cancelled"],
        "active":   ["completed", "cancelled"],
        "completed": [],
        "cancelled": [],
    }
    __initial_state__ = "pending"

    title: str = ""


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInitialization:
    def test_initial_state_set_automatically(self):
        order = Order(id="o1", customer="Acme")
        assert order.state == "draft"

    def test_explicit_state_overrides_initial(self):
        order = Order(id="o2", customer="Acme", state="submitted")
        assert order.state == "submitted"

    def test_no_initial_state_defaults_to_empty(self):
        item = MinimalState(id="m1", label="x")
        assert item.state == ""

    def test_initial_state_persists(self, test_repository):
        test_repository.init_db()
        order = Order(id="o3", customer="Init")
        order.save()
        loaded = Order.get("o3")
        assert loaded.state == "draft"


# ---------------------------------------------------------------------------
# Valid transitions
# ---------------------------------------------------------------------------


class TestValidTransitions:
    def test_simple_transition(self):
        order = Order(id="o10", customer="A")
        order.transition_to("submitted")
        assert order.state == "submitted"

    def test_chain_of_transitions(self):
        order = Order(id="o11", customer="B")
        order.transition_to("submitted")
        order.transition_to("approved")
        order.transition_to("shipped")
        order.transition_to("delivered")
        assert order.state == "delivered"

    def test_transition_to_cancelled(self):
        order = Order(id="o12", customer="C")
        order.transition_to("cancelled")
        assert order.state == "cancelled"

    def test_reopen_ticket(self):
        ticket = Ticket(id="t10", subject="Bug")
        ticket.transition_to("closed")
        ticket.transition_to("open")  # reopen
        assert ticket.state == "open"

    def test_transition_persists(self, test_repository):
        test_repository.init_db()
        order = Order(id="o13", customer="D")
        order.transition_to("submitted")
        order.save()
        loaded = Order.get("o13")
        assert loaded.state == "submitted"


# ---------------------------------------------------------------------------
# Invalid transitions
# ---------------------------------------------------------------------------


class TestInvalidTransitions:
    def test_disallowed_transition_raises(self):
        order = Order(id="o20", customer="X")
        with pytest.raises(InvalidTransition) as exc_info:
            order.transition_to("delivered")
        assert exc_info.value.current_state == "draft"
        assert exc_info.value.target_state == "delivered"
        assert "submitted" in exc_info.value.allowed_states

    def test_transition_from_terminal_raises(self):
        order = Order(id="o21", customer="Y")
        order.transition_to("submitted")
        order.transition_to("rejected")
        with pytest.raises(InvalidTransition):
            order.transition_to("draft")

    def test_unknown_state_raises_value_error(self):
        order = Order(id="o22", customer="Z")
        with pytest.raises(ValueError, match="not a valid state"):
            order.transition_to("nonexistent")

    def test_self_transition_not_allowed_unless_explicit(self):
        order = Order(id="o23", customer="W")
        # draft -> draft not in __states__
        with pytest.raises(InvalidTransition):
            order.transition_to("draft")

    def test_error_message_is_descriptive(self):
        order = Order(id="o24", customer="V")
        with pytest.raises(InvalidTransition) as exc_info:
            order.transition_to("shipped")
        msg = str(exc_info.value)
        assert "Order" in msg
        assert "draft" in msg
        assert "shipped" in msg


# ---------------------------------------------------------------------------
# can_transition_to
# ---------------------------------------------------------------------------


class TestCanTransitionTo:
    def test_allowed(self):
        order = Order(id="o30", customer="A")
        assert order.can_transition_to("submitted") is True
        assert order.can_transition_to("cancelled") is True

    def test_not_allowed(self):
        order = Order(id="o31", customer="B")
        assert order.can_transition_to("delivered") is False
        assert order.can_transition_to("approved") is False

    def test_unknown_state_returns_false(self):
        order = Order(id="o32", customer="C")
        assert order.can_transition_to("nonexistent") is False


# ---------------------------------------------------------------------------
# available_transitions
# ---------------------------------------------------------------------------


class TestAvailableTransitions:
    def test_from_initial_state(self):
        order = Order(id="o40", customer="A")
        assert set(order.available_transitions) == {"submitted", "cancelled"}

    def test_from_terminal_state(self):
        order = Order(id="o41", customer="B")
        order.transition_to("submitted")
        order.transition_to("rejected")
        assert order.available_transitions == []

    def test_updates_after_transition(self):
        order = Order(id="o42", customer="C")
        order.transition_to("submitted")
        assert set(order.available_transitions) == {"approved", "rejected"}


# ---------------------------------------------------------------------------
# is_terminal
# ---------------------------------------------------------------------------


class TestIsTerminal:
    def test_initial_state_not_terminal(self):
        order = Order(id="o50", customer="A")
        assert order.is_terminal is False

    def test_delivered_is_terminal(self):
        order = Order(id="o51", customer="B")
        order.transition_to("submitted")
        order.transition_to("approved")
        order.transition_to("shipped")
        order.transition_to("delivered")
        assert order.is_terminal is True

    def test_rejected_is_terminal(self):
        order = Order(id="o52", customer="C")
        order.transition_to("submitted")
        order.transition_to("rejected")
        assert order.is_terminal is True

    def test_closed_ticket_not_terminal(self):
        ticket = Ticket(id="t50", subject="Reopen test")
        ticket.transition_to("closed")
        assert ticket.is_terminal is False  # closed -> open is allowed


# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------


class TestLifecycleHooks:
    def test_on_enter_called(self):
        ticket = Ticket(id="t20", subject="Hook test")
        ticket.transition_to("in_progress")
        assert "enter_in_progress" in ticket.hook_log

    def test_on_exit_called(self):
        ticket = Ticket(id="t21", subject="Exit test")
        ticket.transition_to("in_progress")
        assert "exit_open" in ticket.hook_log

    def test_hooks_called_in_order(self):
        ticket = Ticket(id="t22", subject="Order test")
        ticket.transition_to("in_progress")
        # exit_open should come before enter_in_progress
        assert ticket.hook_log == "exit_open;enter_in_progress;"

    def test_chain_hooks_accumulate(self):
        ticket = Ticket(id="t23", subject="Chain")
        ticket.transition_to("in_progress")
        ticket.transition_to("closed")
        ticket.transition_to("open")
        assert "exit_open;" in ticket.hook_log
        assert "enter_in_progress;" in ticket.hook_log
        assert "enter_closed;" in ticket.hook_log
        assert "exit_closed;" in ticket.hook_log
        assert "enter_open;" in ticket.hook_log

    def test_no_hooks_if_not_defined(self):
        order = Order(id="o60", customer="No hooks")
        order.transition_to("submitted")
        # Should not raise — hooks simply don't exist
        assert order.state == "submitted"

    def test_hooks_not_called_on_truly_invalid_transition(self):
        ticket = Ticket(id="t25", subject="Nope")
        ticket.transition_to("in_progress")
        ticket.hook_log = ""  # reset
        with pytest.raises(ValueError):
            ticket.transition_to("nonexistent")
        assert ticket.hook_log == ""  # no hooks fired
        assert ticket.state == "in_progress"  # state unchanged


# ---------------------------------------------------------------------------
# in_state query
# ---------------------------------------------------------------------------


class TestInStateQuery:
    def test_find_by_state(self, test_repository):
        test_repository.init_db()
        o1 = Order(id="q1", customer="A")
        o1.save()
        o2 = Order(id="q2", customer="B")
        o2.transition_to("submitted")
        o2.save()
        o3 = Order(id="q3", customer="C")
        o3.save()

        drafts = Order.in_state("draft")
        draft_ids = [o.id for o in drafts]
        assert "q1" in draft_ids
        assert "q3" in draft_ids
        assert "q2" not in draft_ids

    def test_in_state_empty_result(self, test_repository):
        test_repository.init_db()
        o1 = Order(id="q4", customer="D")
        o1.save()
        shipped = Order.in_state("shipped")
        assert len(shipped) == 0


# ---------------------------------------------------------------------------
# Composition with other mixins
# ---------------------------------------------------------------------------


class TestMixinComposition:
    def test_state_machine_with_timestamps(self, test_repository):
        test_repository.init_db()
        item = ComposedStateful(id="cs1", title="Composed")
        assert item.state == "pending"
        assert item.created_at is not None
        item.transition_to("active")
        item.save()
        loaded = ComposedStateful.get("cs1")
        assert loaded.state == "active"
        assert loaded.is_deleted is False

    def test_soft_delete_and_state(self, test_repository):
        test_repository.init_db()
        item = ComposedStateful(id="cs2", title="Delete me")
        item.transition_to("active")
        item.soft_delete()
        item.save()
        loaded = ComposedStateful.get("cs2")
        assert loaded.state == "active"
        assert loaded.is_deleted is True

    def test_in_state_with_soft_delete(self, test_repository):
        test_repository.init_db()
        alive = ComposedStateful(id="cs3", title="Alive")
        alive.save()
        dead = ComposedStateful(id="cs4", title="Dead")
        dead.soft_delete()
        dead.save()
        pending = ComposedStateful.in_state("pending")
        ids = [p.id for p in pending]
        # Both should appear — in_state doesn't filter soft-deleted
        assert "cs3" in ids
        assert "cs4" in ids


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_entity_with_no_states_defined(self):
        item = MinimalState(id="e1", label="bare")
        assert item.state == ""
        assert item.available_transitions == []
        assert item.is_terminal is True

    def test_all_states_classmethod(self):
        all_states = Order._all_states()
        expected = {"draft", "submitted", "approved", "shipped", "delivered", "rejected", "cancelled"}
        assert all_states == expected

    def test_invalid_transition_exception_fields(self):
        exc = InvalidTransition("Order", "draft", "shipped", ["submitted", "cancelled"])
        assert exc.entity_type == "Order"
        assert exc.current_state == "draft"
        assert exc.target_state == "shipped"
        assert exc.allowed_states == ["submitted", "cancelled"]
