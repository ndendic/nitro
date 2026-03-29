"""
Entity action registration via __init_subclass__.

Scans Entity subclasses for decorated methods and registers
Blinker event handlers for each.
"""
import inspect
from .metadata import get_action_metadata, has_action_metadata
from .decorator import _extract_params
from ..events.events import on


class NotFoundError(Exception):
    """Raised when an entity is not found by ID."""
    pass


def _make_entity_handler(cls, method, metadata, is_instance: bool):
    """Create a Blinker event handler that wraps an Entity method."""
    if is_instance:
        async def handler(sender, **kwargs):
            signals = kwargs.pop("signals", {})
            entity_id = signals.pop("id", None)
            if not entity_id:
                raise ValueError(f"ID required for {cls.__name__}.{metadata.function_name}")
            entity = cls.get(entity_id)
            if not entity:
                raise NotFoundError(f"{cls.__name__} '{entity_id}' not found")                
            params = _extract_params(metadata, signals, **kwargs)
            if metadata.is_async:
                return await method(entity, **params)
            else:
                return method(entity, **params)
    else:
        async def handler(sender, **kwargs):
            signals = kwargs.pop("signals", {})
            params = _extract_params(metadata, signals, **kwargs)
            if metadata.is_async:
                return await method(**params)
            else:
                return method(**params)
    return handler


def register_entity_actions(cls):
    """
    Scan an Entity subclass for decorated methods and register
    Blinker event handlers for each.

    Called by Entity.__init_subclass__.
    """
    entity_name = getattr(cls, "__route_name__", cls.__name__)

    for name, method in inspect.getmembers(cls, predicate=callable):
        if name.startswith("_"):
            continue
        if not has_action_metadata(method):
            continue

        metadata = get_action_metadata(method)
        metadata.entity_class_name = entity_name

        is_instance = "self" in metadata.parameters
        event_name = f"{entity_name}.{name}"
        metadata.event_name = event_name

        handler = _make_entity_handler(cls, method, metadata, is_instance)
        on(event_name)(handler)
