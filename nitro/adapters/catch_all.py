"""
Framework-agnostic catch-all dispatch logic.

Parses action strings and dispatches to the Blinker event system.
Framework adapters call dispatch_action() from their catch-all route handlers.
"""
from typing import Any, Optional
from ..routing.actions import parse_action
from ..events.events import emit_async


async def dispatch_action(
    action_str: str,
    sender: str,
    signals: Optional[dict] = None,
    request: Any = None,
) -> Any:
    """
    Parse an action string and dispatch to the Blinker event system.

    Args:
        action_str: Action string like "Counter:abc123.increment"
        sender: Client identifier (from $conn signal)
        signals: Dict of signal values from the request
        request: The raw framework request object (passed through to handlers)

    Returns:
        The result from the event handler, or None if no handler matched.
    """
    if signals is None:
        signals = {}

    parsed = parse_action(action_str)

    # Inject entity ID into signals if present
    if parsed.id:
        signals["id"] = parsed.id

    event_name = parsed.event_name

    result = await emit_async(event_name, sender, signals=signals, request=request)
    return result
