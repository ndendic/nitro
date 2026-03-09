# nitro/tests/test_decorator_events.py
import pytest
import asyncio
from nitro.routing.decorator import get, post, put, delete
from nitro.routing.metadata import get_action_metadata
from nitro.events.events import event, default_namespace


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
    """Standalone functions register Blinker events at decoration time."""

    def setup_method(self):
        # Clear default namespace between tests
        default_namespace.clear()

    def test_standalone_registers_event(self):
        @post(prefix="auth")
        def register_user(name: str): pass

        evt = event("auth.register_user")
        assert len(list(evt.receivers_for(None))) > 0

    def test_standalone_no_prefix_registers_event(self):
        @get()
        def health(): pass

        evt = event("health")
        assert len(list(evt.receivers_for(None))) > 0

    def test_standalone_handler_calls_function(self):
        call_log = []

        @post(prefix="test")
        def do_thing(name: str = "default"):
            call_log.append(name)
            return {"ok": True}

        evt = event("test.do_thing")
        asyncio.get_event_loop().run_until_complete(
            evt.emit_async(None, signals={"name": "hello"})
        )
        assert call_log == ["hello"]

    def test_standalone_async_handler(self):
        call_log = []

        @post(prefix="test")
        async def async_thing(value: int = 0):
            call_log.append(value)

        evt = event("test.async_thing")
        asyncio.get_event_loop().run_until_complete(
            evt.emit_async(None, signals={"value": 42})
        )
        assert call_log == [42]

    def test_original_function_still_callable(self):
        """Decorator returns the original function, not the handler."""
        @post(prefix="test")
        def my_func(x: int = 1):
            return x * 2

        assert my_func(5) == 10


class TestEntityMethodDeferred:
    """Entity methods only get metadata — no event registration."""

    def setup_method(self):
        default_namespace.clear()

    def test_method_with_self_not_registered(self):
        """Methods with 'self' param should NOT register events at decoration time."""
        @post()
        def increment(self, amount: int = 1):
            pass

        # Should NOT have created an event
        meta = get_action_metadata(increment)
        assert meta is not None
        # event_name should be empty (deferred to __init_subclass__)
        assert meta.event_name == ""
