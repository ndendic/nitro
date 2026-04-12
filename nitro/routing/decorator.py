"""
Action decorators for the routing system.

Standalone functions: decorator stamps metadata AND registers in the handler registry.
Entity methods (have 'self' or 'cls'): decorator only stamps metadata.
Entity method registration happens in Entity.__init_subclass__.
"""
import inspect
from typing import Optional, Any

from .metadata import ActionMetadata, extract_parameters, set_action_metadata
from .registry import register_handler


def _extract_params(metadata: ActionMetadata, signals: dict, **kwargs) -> dict:
    """Extract method parameters from signals dict, matching the function signature."""
    params = {}
    for name, info in metadata.parameters.items():
        if name in ("self", "cls"):
            continue
        if name in signals:
            value = signals[name]
            # Type coercion
            annotation = info.get("annotation")
            if annotation and value is not None:
                try:
                    if annotation is int:
                        value = int(value)
                    elif annotation is float:
                        value = float(value)
                    elif annotation is bool:
                        if isinstance(value, str):
                            value = value.lower() in ("true", "1", "yes")
                except (ValueError, TypeError):
                    pass
            params[name] = value
        elif name in kwargs:
            params[name] = kwargs[name]
        elif info.get("default") is not None:
            params[name] = info["default"]
        else:
            raise TypeError(f"Missing required parameter: {name}")
    return params


def _has_self_or_cls(func) -> bool:
    """Check if function has 'self' or 'cls' as first parameter."""
    params = extract_parameters(func)
    first_param = next(iter(params), None)
    return first_param in ("self", "cls")


def _register_standalone_handler(func, metadata: ActionMetadata):
    """Register a handler for a standalone function in the routing registry."""
    from .registration import _call_method

    event_name = metadata.event_name

    async def handler(signals, request, sender):
        params = _extract_params(metadata, signals, request=request)
        return await _call_method(func, metadata.is_async, **params)

    register_handler(event_name, handler)


def action(
    method: str = "POST",
    prefix: str = "",
    path: Optional[str] = None,
    status_code: int = 200,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[list] = None,
    response_model: Optional[Any] = None,
    **kwargs,
):
    """
    Core decorator for registering an action.

    For standalone functions: stamps metadata and registers in the handler registry.
    For Entity methods (with self/cls): stamps metadata only. Registration
    happens in Entity.__init_subclass__.
    """
    def decorator(func):
        # Unwrap classmethod/staticmethod for inspection
        raw_func = func.__func__ if isinstance(func, (classmethod, staticmethod)) else func
        is_async = inspect.iscoroutinefunction(raw_func)
        parameters = extract_parameters(raw_func)
        is_entity_method = _has_self_or_cls(raw_func)

        # Build event name only for standalone functions
        if is_entity_method:
            event_name = ""  # Filled in by __init_subclass__
        else:
            event_name = f"{prefix}.{func.__name__}" if prefix else func.__name__

        metadata = ActionMetadata(
            method=method.upper(),
            prefix=prefix,
            path=path,
            status_code=status_code,
            summary=summary,
            description=description,
            tags=tags or [],
            response_model=response_model,
            function_name=raw_func.__name__,
            entity_class_name="",
            event_name=event_name,
            is_async=is_async,
            parameters=parameters,
        )

        set_action_metadata(raw_func, metadata)
        # Also stamp on wrapper (classmethod/staticmethod) so registration can find it
        if func is not raw_func:
            set_action_metadata(func, metadata)

        # Register handler for standalone functions immediately
        if not is_entity_method:
            _register_standalone_handler(raw_func, metadata)

        return func

    return decorator


def get(prefix: str = "", **kwargs):
    """GET action decorator."""
    return action(method="GET", prefix=prefix, **kwargs)


def post(prefix: str = "", status_code: int = 200, **kwargs):
    """POST action decorator."""
    return action(method="POST", prefix=prefix, status_code=status_code, **kwargs)


def put(prefix: str = "", **kwargs):
    """PUT action decorator."""
    return action(method="PUT", prefix=prefix, **kwargs)


def delete(prefix: str = "", status_code: int = 204, **kwargs):
    """DELETE action decorator."""
    return action(method="DELETE", prefix=prefix, status_code=status_code, **kwargs)


def patch(prefix: str = "", **kwargs):
    """PATCH action decorator."""
    return action(method="PATCH", prefix=prefix, **kwargs)
