"""
Framework-agnostic catch-all dispatch logic.

Parses action strings and calls handlers from the routing registry.
Framework adapters call dispatch_action() from their catch-all route handlers.
"""
from typing import Any, Optional
from ..routing.actions import parse_action
from ..routing.registry import get_handler


async def dispatch_action(
    action_str: str,
    sender: str,
    signals: Optional[dict] = None,
    request: Any = None,
) -> Any:
    """
    Parse an action string and dispatch to the registered handler.

    Args:
        action_str: Action string like "Counter:abc123.increment"
        sender: Client identifier (from $conn signal)
        signals: Dict of signal values from the request
        request: The raw framework request object (passed through to handlers)

    Returns:
        The result from the handler, or None if no handler matched.
    """
    if signals is None:
        signals = {}

    parsed = parse_action(action_str)

    # Inject entity ID into signals if present
    if parsed.id:
        signals["id"] = parsed.id

    handler = get_handler(parsed.event_name)
    if handler is None:
        return None

    return await handler(signals, request, sender)
