# nitro/tests/test_catch_all.py
import pytest
import asyncio
from nitro.routing.actions import parse_action, ActionRef
from nitro.routing.registration import NotFoundError
from nitro.adapters.catch_all import dispatch_action
from nitro.events.events import event, on, default_namespace


class TestDispatchAction:
    """Test the core dispatch logic (framework-agnostic)."""

    def setup_method(self):
        default_namespace.clear()

    def test_dispatch_standalone(self):
        call_log = []

        @on("test.greet")
        async def handler(sender, **kwargs):
            signals = kwargs.get("signals", {})
            call_log.append(signals.get("name", "world"))
            return {"greeting": f"hello {signals.get('name', 'world')}"}

        result = asyncio.run(
            dispatch_action("test.greet", "client1", signals={"name": "Nikola"})
        )
        assert call_log == ["Nikola"]

    def test_dispatch_with_entity_id(self):
        """ID from action string should be injected into signals."""
        received_signals = {}

        @on("Counter.increment")
        async def handler(sender, **kwargs):
            received_signals.update(kwargs.get("signals", {}))

        asyncio.run(
            dispatch_action(
                "Counter:abc123.increment", "client1",
                signals={"amount": 5}
            )
        )
        assert received_signals["id"] == "abc123"
        assert received_signals["amount"] == 5

    def test_dispatch_class_method(self):
        """Class methods have no ID in the action string."""
        called_with = {}

        @on("Todo.load_all")
        async def handler(sender, **kwargs):
            called_with.update(kwargs)
            return []

        asyncio.run(
            dispatch_action("Todo.load_all", "client1", signals={})
        )
        assert "signals" in called_with

    def test_dispatch_no_handler_returns_none(self):
        """If no handler is registered, emit returns nothing."""
        result = asyncio.run(
            dispatch_action("nonexistent.action", "client1", signals={})
        )
        # No handler = no result (Blinker returns empty)
        assert result is None or result == []
