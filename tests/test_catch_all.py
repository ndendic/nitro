# nitro/tests/test_catch_all.py
import pytest
import asyncio
from nitro.routing.actions import parse_action, ActionRef
from nitro.routing.registration import NotFoundError
from nitro.routing.registry import register_handler, clear_handlers
from nitro.adapters.catch_all import dispatch_action


class TestDispatchAction:
    """Test the core dispatch logic (framework-agnostic)."""

    def setup_method(self):
        clear_handlers()

    def test_dispatch_standalone(self):
        call_log = []

        async def handler(signals, request, sender):
            call_log.append(signals.get("name", "world"))
            return {"greeting": f"hello {signals.get('name', 'world')}"}

        register_handler("test.greet", handler)

        result = asyncio.run(
            dispatch_action("test.greet", "client1", signals={"name": "Nikola"})
        )
        assert call_log == ["Nikola"]

    def test_dispatch_with_entity_id(self):
        """ID from action string should be injected into signals."""
        received_signals = {}

        async def handler(signals, request, sender):
            received_signals.update(signals)

        register_handler("Counter.increment", handler)

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

        async def handler(signals, request, sender):
            called_with["signals"] = signals
            called_with["sender"] = sender
            return []

        register_handler("Todo.load_all", handler)

        asyncio.run(
            dispatch_action("Todo.load_all", "client1", signals={})
        )
        assert "signals" in called_with

    def test_dispatch_no_handler_returns_none(self):
        """If no handler is registered, dispatch returns None."""
        result = asyncio.run(
            dispatch_action("nonexistent.action", "client1", signals={})
        )
        assert result is None
