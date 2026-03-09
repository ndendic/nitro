# nitro/tests/test_action_helper.py
import pytest
from nitro.routing.decorator import get, post, delete
from nitro.routing.action_helper import action


class TestActionStandalone:
    """action() with standalone functions."""

    def test_standalone_with_prefix(self):
        @post(prefix="auth")
        def register_user(name: str, email: str): pass

        result = action(register_user)
        assert result == "@post('/post/auth.register_user/$conn')"

    def test_standalone_no_prefix(self):
        @get()
        def health_check(): pass

        result = action(health_check)
        assert result == "@get('/get/health_check/$conn')"

    def test_get_with_query_params(self):
        @get(prefix="admin")
        def dashboard(limit: int = 10): pass

        result = action(dashboard, limit=20, offset=5)
        assert "@get('/get/admin.dashboard/$conn?" in result
        assert "limit=20" in result
        assert "offset=5" in result

    def test_post_with_literal_params(self):
        @post(prefix="auth")
        def register(name: str = ""): pass

        result = action(register, name="John")
        assert "$name = 'John'" in result
        assert "@post('/post/auth.register/$conn')" in result

    def test_post_with_signal_params(self):
        @post(prefix="auth")
        def register(name: str = ""): pass

        result = action(register, name="$name")
        # Signal references don't need assignment — just fire the action
        assert "@post('/post/auth.register/$conn')" in result

    def test_not_decorated_raises(self):
        def plain_func(): pass
        with pytest.raises(ValueError, match="not a decorated action"):
            action(plain_func)


class TestActionEntityClass:
    """action() with Entity class methods (unbound)."""

    def test_class_method_with_id(self):
        @post()
        def toggle(self): pass

        # Simulate what __init_subclass__ would do
        from nitro.routing.metadata import get_action_metadata
        meta = get_action_metadata(toggle)
        meta.entity_class_name = "Todo"
        meta.event_name = "Todo.toggle"

        result = action(toggle, id="abc123")
        assert result == "@post('/post/Todo:abc123.toggle/$conn')"

    def test_class_method_with_signal_id(self):
        @post()
        def toggle(self): pass

        from nitro.routing.metadata import get_action_metadata
        meta = get_action_metadata(toggle)
        meta.entity_class_name = "Todo"
        meta.event_name = "Todo.toggle"

        result = action(toggle, id="$selected_id")
        assert result == "@post('/post/Todo:$selected_id.toggle/$conn')"

    def test_class_method_no_self_no_id(self):
        @get()
        def load_all(): pass

        from nitro.routing.metadata import get_action_metadata
        meta = get_action_metadata(load_all)
        meta.entity_class_name = "Todo"
        meta.event_name = "Todo.load_all"

        result = action(load_all)
        assert result == "@get('/get/Todo.load_all/$conn')"

    def test_delete_method(self):
        @delete()
        def remove(self): pass

        from nitro.routing.metadata import get_action_metadata
        meta = get_action_metadata(remove)
        meta.entity_class_name = "Todo"
        meta.event_name = "Todo.remove"

        result = action(remove, id="xyz")
        assert result == "@delete('/delete/Todo:xyz.remove/$conn')"


class TestActionBoundInstance:
    """action() with bound instance methods."""

    def test_bound_method_auto_injects_id(self):
        class FakeEntity:
            id = "auto-id-123"

            @post()
            def save_data(self): pass

        from nitro.routing.metadata import get_action_metadata
        meta = get_action_metadata(FakeEntity.save_data)
        meta.entity_class_name = "FakeEntity"
        meta.event_name = "FakeEntity.save_data"

        instance = FakeEntity()
        result = action(instance.save_data)
        assert result == "@post('/post/FakeEntity:auto-id-123.save_data/$conn')"

    def test_bound_method_with_params(self):
        class FakeEntity:
            id = "e1"

            @post()
            def update(self, name: str = ""): pass

        from nitro.routing.metadata import get_action_metadata
        meta = get_action_metadata(FakeEntity.update)
        meta.entity_class_name = "FakeEntity"
        meta.event_name = "FakeEntity.update"

        instance = FakeEntity()
        result = action(instance.update, name="$new_name")
        assert "@post('/post/FakeEntity:e1.update/$conn')" in result
