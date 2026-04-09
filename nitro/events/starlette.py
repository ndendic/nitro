"""
SSE helpers for Datastar integration.

These functions publish SSE-formatted messages to topics that Clients can subscribe to.
"""
import warnings
from typing import Any, Mapping

from rusty_tags.datastar import SSE
from datastar_py.consts import ElementPatchMode
from datastar_py.sse import _HtmlProvider

from .events import publish_sync


def _resolve_source(source: str | None, sender: Any) -> str | None:
    """Resolve source from new 'source' or legacy 'sender' param."""
    if sender is not None:
        warnings.warn(
            "The 'sender' parameter is deprecated, use 'source' instead. "
            "Will be removed in v2.0.",
            DeprecationWarning,
            stacklevel=3,
        )
        return str(sender) if sender != "*" else None
    return source


def publish_to_topic(
    topic: str | list[str], 
    data: Any, 
    source: str | None = None,
    sender: Any = None,  # Deprecated
):
    """Publish data to one or more topics."""
    resolved_source = _resolve_source(source, sender)
    if isinstance(topic, list):
        for t in topic:
            publish_sync(t, data=data, source=resolved_source)
    else:
        publish_sync(topic, data=data, source=resolved_source)


def emit_elements(
        elements: str | _HtmlProvider,
        selector: str | None = None,
        mode: ElementPatchMode = ElementPatchMode.REPLACE,
        use_view_transition: bool | None = None,
        event_id: str | None = None,
        retry_duration: int | None = None,
        topic: str | list[str] = "sse",
        source: str | None = None,
        sender: Any = None):  # Deprecated
    """Emit SSE element patch to topic(s)."""
    result = SSE.patch_elements(
        elements,
        selector=selector if selector else None,
        mode=mode,
        event_id=event_id,
        retry_duration=retry_duration
    )
    publish_to_topic(topic, data=result, source=source, sender=sender)
    return result


def remove_elements(
        selector: str, 
        event_id: str | None = None, 
        retry_duration: int | None = None,
        topic: str | list[str] = "sse",
        source: str | None = None,
        sender: Any = None):  # Deprecated
    """Emit SSE element removal to topic(s)."""
    result = SSE.patch_elements(
        selector=selector,
        mode=ElementPatchMode.REMOVE,
        event_id=event_id,
        retry_duration=retry_duration,
    )
    publish_to_topic(topic, data=result, source=source, sender=sender)
    return result


def emit_signals(
        signals: dict | str,
        *,
        event_id: str | None = None,
        only_if_missing: bool | None = None,
        retry_duration: int | None = None,
        topic: str | list[str] = "sse",
        source: str | None = None,
        sender: Any = None):  # Deprecated
    """Emit SSE signal patch to topic(s)."""
    result = SSE.patch_signals(
        signals=signals,
        event_id=event_id,
        only_if_missing=only_if_missing,
        retry_duration=retry_duration
    )
    publish_to_topic(topic, data=result, source=source, sender=sender)
    return result


def execute_script(
        script: str,
        *,
        auto_remove: bool = True,
        attributes: Mapping[str, str] | list[str] | None = None,
        event_id: str | None = None,
        retry_duration: int | None = None,
        topic: str | list[str] = "sse",
        source: str | None = None,
        sender: Any = None):  # Deprecated
    """Emit SSE script execution to topic(s)."""
    result = SSE.execute_script(
        script, 
        auto_remove=auto_remove, 
        attributes=attributes, 
        event_id=event_id, 
        retry_duration=retry_duration
    )
    publish_to_topic(topic, data=result, source=source, sender=sender)
    return result


def redirect(
        location: str,
        topic: str | list[str] = "sse",
        source: str | None = None,
        sender: Any = None):  # Deprecated
    """Emit SSE redirect to topic(s)."""
    result = SSE.redirect(location)
    publish_to_topic(topic, data=result, source=source, sender=sender)
    return result


# Legacy alias
emit_to_topic = publish_to_topic


__all__ = [
    'publish_to_topic',
    'emit_to_topic',  # Legacy alias
    'emit_elements',
    'remove_elements',
    'emit_signals',
    'execute_script',
    'redirect',
]
