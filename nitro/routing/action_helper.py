"""
The action() helper — generates Datastar action strings from Python function references.

Usage:
    action(counter.increment, amount=5)
    -> "@post('/post/Counter:abc123.increment')"
"""
import inspect
from .metadata import get_action_metadata


def _js_value(value) -> str:
    """Convert a Python value to a JavaScript literal string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        if value.startswith("$"):
            return value  # Signal reference, pass through
        return f"'{value}'"
    elif value is None:
        return "null"
    else:
        return f"'{value}'"


def _is_signal_ref(value) -> bool:
    """Check if a value is a Datastar signal reference like $name."""
    return isinstance(value, str) and value.startswith("$")


def action(method_or_func, **params) -> str:
    """
    Generate a Datastar action string from a decorated function reference.

    Args:
        method_or_func: A decorated function or bound method.
        **params: Parameters to include in the action.

    Returns:
        A Datastar action string like "@post('/post/Counter:abc123.increment')"
    """
    metadata = get_action_metadata(method_or_func)
    if metadata is None:
        raise ValueError(f"{method_or_func} is not a decorated action")

    http_method = metadata.method.lower()

    # Auto-inject entity id from bound instance method (not classmethods)
    if inspect.ismethod(method_or_func) and hasattr(method_or_func, "__self__"):
        instance = method_or_func.__self__
        if not isinstance(instance, type) and hasattr(instance, "id"):
            params.setdefault("id", instance.id)

    # Build the action path
    entity_id = params.pop("id", None)
    if entity_id and metadata.entity_class_name:
        action_path = f"{metadata.entity_class_name}:{entity_id}.{metadata.function_name}"
    elif metadata.event_name:
        action_path = metadata.event_name
    else:
        action_path = metadata.function_name

    url = f"/{http_method}/{action_path}"

    # Handle remaining params based on HTTP method
    if http_method == "get" and params:
        # GET: query string
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"@{http_method}('{url}?{query}')"
    elif params:
        # POST/PUT/etc: set non-signal params as signal assignments
        non_signal_params = {k: v for k, v in params.items() if not _is_signal_ref(v)}
        if non_signal_params:
            assignments = "; ".join(
                f"${k} = {_js_value(v)}" for k, v in non_signal_params.items()
            )
            return f"{assignments}; @{http_method}('{url}')"
        else:
            return f"@{http_method}('{url}')"
    else:
        return f"@{http_method}('{url}')"
