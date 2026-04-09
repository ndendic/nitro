# nitro/tests/test_decorator_events.py
import pytest
import asyncio
from nitro.routing.decorator import get, post, put, delete
from nitro.routing.metadata import get_action_metadata
from nitro.routing.registry import get_handler, clear_handlers


class TestDecoratorMetadata:
    """Decorators stamp ActionMetadata correctly."""

    def test_post_stamps_metadata(self):
        @post()
        def my_func(): pass
        meta = get_action_metadata(my_func)
        assert meta is not None
        assert meta.method == "POST"
        assert meta.function_name == "my_func"

    def test_get_stamps_metadata(self):
        @get()
        def my_func(): pass
        meta = get_action_metadata(my_func)
        assert meta.method == "GET"

    def test_put_stamps_metadata(self):
        @put()
        def my_func(): pass
        meta = get_action_metadata(my_func)
        assert meta.method == "PUT"

    def test_delete_stamps_metadata(self):
        @delete()
        def my_func(): pass
        meta = get_action_metadata(my_func)
        assert meta.method == "DELETE"

    def test_prefix_stored_in_metadata(self):
        @post(prefix="auth")
        def register(): pass
        meta = get_action_metadata(register)
        assert meta.prefix == "auth"
        assert meta.event_name == "auth.register"

    def test_no_prefix(self):
        @get()
        def health_check(): pass
        meta = get_action_metadata(health_check)
        assert meta.event_name == "health_check"

    def test_async_function_detected(self):
        @post()
        async def my_async(): pass
        meta = get_action_metadata(my_async)
        assert meta.is_async is True

    def test_sync_function_detected(self):
        @post()
        def my_sync(): pass
        meta = get_action_metadata(my_sync)
        assert meta.is_async is False


class TestStandaloneEventRegistration:
    """Standalone functions register handlers in the routing registry at decoration time."""

    def setup_method(self):
        clear_handlers()

    def test_standalone_registers_handler(self):
        @post(prefix="auth")
        def register_user(name: str): pass

        handler = get_handler("auth.register_user")
        assert handler is not None

    def test_standalone_no_prefix_registers_handler(self):
        @get()
        def health(): pass

        handler = get_handler("health")
        assert handler is not None

    def test_standalone_handler_calls_function(self):
        call_log = []

        @post(prefix="test")
        def do_thing(name: str = "default"):
            call_log.append(name)
            return {"ok": True}

        handler = get_handler("test.do_thing")
        asyncio.run(handler({"name": "hello"}, None, "test"))
        assert call_log == ["hello"]

    def test_standalone_async_handler(self):
        call_log = []

        @post(prefix="test")
        async def async_thing(value: int = 0):
            call_log.append(value)

        handler = get_handler("test.async_thing")
        asyncio.run(handler({"value": 42}, None, "test"))
        assert call_log == [42]

    def test_original_function_still_callable(self):
        """Decorator returns the original function, not the handler."""
        @post(prefix="test")
        def my_func(x: int = 1):
            return x * 2

        assert my_func(5) == 10


class TestEntityMethodDeferred:
    """Entity methods only get metadata — no handler registration."""

    def setup_method(self):
        clear_handlers()

    def test_method_with_self_not_registered(self):
        """Methods with 'self' param should NOT register handlers at decoration time."""
        @post()
        def increment(self, amount: int = 1):
            pass

        # Should NOT have registered a handler
        meta = get_action_metadata(increment)
        assert meta is not None
        # event_name should be empty (deferred to __init_subclass__)
        assert meta.event_name == ""
