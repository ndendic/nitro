"""
Entity action registration via __init_subclass__.

Scans Entity subclasses for decorated methods and registers
handlers in the routing registry for dispatch by catch-all endpoints.
"""
import inspect
from .metadata import get_action_metadata, has_action_metadata
from .decorator import _extract_params
from .registry import register_handler


class NotFoundError(Exception):
    """Raised when an entity is not found by ID."""
    pass


async def _call_method(method, is_async, *args, **kwargs):
    """Call a method handling all handler types: sync, async, generator, async generator."""
    if is_async:
        result = await method(*args, **kwargs)
    else:
        result = method(*args, **kwargs)

    # Consume generators into lists
    if inspect.isgenerator(result):
        return list(result)
    if inspect.isasyncgen(result):
        return [item async for item in result]

    return result


def _make_entity_handler(cls, method, metadata, is_instance: bool):
    """Create a routing handler that wraps an Entity method.

    Handler signature: async handler(signals, request, sender) -> Any
    Supports sync, async, generator, and async generator methods.
    """
    if is_instance:
        async def handler(signals, request, sender):
            entity_id = signals.pop("id", None)
            if not entity_id:
                raise ValueError(f"ID required for {cls.__name__}.{metadata.function_name}")
            entity = cls.get(entity_id)
            if not entity:
                raise NotFoundError(f"{cls.__name__} '{entity_id}' not found")
            params = _extract_params(metadata, signals, request=request)
            return await _call_method(method, metadata.is_async, entity, **params)
    else:
        async def handler(signals, request, sender):
            params = _extract_params(metadata, signals, request=request)
            return await _call_method(method, metadata.is_async, **params)
    return handler


def register_entity_actions(cls):
    """
    Scan an Entity subclass for decorated methods and register
    handlers in the routing registry.

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
        register_handler(event_name, handler)
