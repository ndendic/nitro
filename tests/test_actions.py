# nitro/tests/test_actions.py
import pytest
from nitro.routing.actions import ActionRef, parse_action


class TestParseAction:
    """Tests for parsing action strings into ActionRef."""

    def test_instance_method(self):
        ref = parse_action("Counter:abc123.increment")
        assert ref.entity == "Counter"
        assert ref.id == "abc123"
        assert ref.method == "increment"
        assert ref.event_name == "Counter.increment"

    def test_instance_method_uuid_id(self):
        ref = parse_action("User:550e8400-e29b-41d4-a716-446655440000.update")
        assert ref.entity == "User"
        assert ref.id == "550e8400-e29b-41d4-a716-446655440000"
        assert ref.method == "update"

    def test_class_method_or_prefixed_standalone(self):
        ref = parse_action("Counter.load_all")
        assert ref.prefix == "Counter"
        assert ref.function == "load_all"
        assert ref.id is None
        assert ref.event_name == "Counter.load_all"

    def test_standalone_with_prefix(self):
        ref = parse_action("auth.register_user")
        assert ref.prefix == "auth"
        assert ref.function == "register_user"
        assert ref.event_name == "auth.register_user"

    def test_standalone_no_prefix(self):
        ref = parse_action("health_check")
        assert ref.prefix is None
        assert ref.function == "health_check"
        assert ref.event_name == "health_check"

    def test_instance_method_with_signal_id(self):
        """Signal IDs like $id come through as literal strings at parse time."""
        ref = parse_action("Todo:$selected_id.toggle")
        assert ref.entity == "Todo"
        assert ref.id == "$selected_id"
        assert ref.method == "toggle"


class TestActionRef:
    """Tests for ActionRef dataclass."""

    def test_entity_ref_is_instance(self):
        ref = ActionRef(entity="Counter", id="abc", method="increment")
        assert ref.is_instance_method is True

    def test_entity_ref_is_class(self):
        ref = ActionRef(entity="Counter", method="load_all")
        assert ref.is_instance_method is False

    def test_standalone_ref(self):
        ref = ActionRef(function="health_check")
        assert ref.is_instance_method is False

    def test_event_name_instance(self):
        ref = ActionRef(entity="Counter", id="abc", method="increment")
        assert ref.event_name == "Counter.increment"

    def test_event_name_class(self):
        ref = ActionRef(prefix="Counter", function="load_all")
        assert ref.event_name == "Counter.load_all"

    def test_event_name_standalone(self):
        ref = ActionRef(function="health_check")
        assert ref.event_name == "health_check"

    def test_event_name_prefixed_standalone(self):
        ref = ActionRef(prefix="auth", function="register")
        assert ref.event_name == "auth.register"
