"""
Handler registry for action routing.

Simple dict-based lookup: topic → handler function.
This is the routing backbone — HTTP requests get dispatched here.
PubSub (nitro-events) is a separate concern used for SSE streaming.
"""
from typing import Callable, Optional

_handlers: dict[str, Callable] = {}


def register_handler(topic: str, handler: Callable) -> None:
    """Register a handler for an action topic (e.g. 'Counter.increment')."""
    _handlers[topic] = handler


def get_handler(topic: str) -> Optional[Callable]:
    """Get the handler for an action topic."""
    return _handlers.get(topic)


def clear_handlers() -> None:
    """Clear all registered handlers. Used in tests."""
    _handlers.clear()


def list_handlers() -> dict[str, Callable]:
    """List all registered handlers. Used for debugging."""
    return dict(_handlers)
