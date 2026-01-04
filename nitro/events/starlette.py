from typing import Any, Mapping

from rusty_tags.datastar import SSE
from .events import ANY
from datastar_py.consts import ElementPatchMode
from datastar_py.sse import _HtmlProvider
from datastar_py.starlette import datastar_response


from .events import emit

def emit_to_topic(topic: str | list[str] | Any, sender: str | Any = ANY, *args, **kwargs):
    if isinstance(topic, list):
        for t in topic:
            emit(t, sender, *args, **kwargs)
    else:
        emit(topic, sender, *args, **kwargs)

def emit_elements(
        elements: str | _HtmlProvider,
        selector: str | None = None,
        mode: ElementPatchMode = ElementPatchMode.REPLACE,
        use_view_transition: bool | None = None,
        event_id: str | None = None,
        retry_duration: int | None = None,
        topic: str | list[str] | Any = ANY,
        sender: str | Any = ANY):
    
    result = SSE.patch_elements(elements,
        selector=selector if selector else None,
        mode=mode,
        # use_view_transitions=use_view_transition, TODO there is a bug in datastar_py here
        event_id=event_id,
        retry_duration=retry_duration
        )  
    emit_to_topic(topic, sender, result=result)
    return result

def remove_elements(
        selector: str, 
        event_id: str | None = None, 
        retry_duration: int | None = None,
        topic: str | list[str] | Any = ANY,
        sender: str | Any = ANY
    ):
        result = SSE.patch_elements(
            selector=selector,
            mode=ElementPatchMode.REMOVE,
            event_id=event_id,
            retry_duration=retry_duration,
        )
        emit_to_topic(topic, sender, result=result)
        return result

def emit_signals(
        signals: dict | str,
        *,
        event_id: str | None = None,
        only_if_missing: bool | None = None,
        retry_duration: int | None = None,
        topic: str | list[str] | Any = ANY,
        sender: str | Any = ANY):
    result = SSE.patch_signals(
        signals=signals,
        event_id=event_id,
        only_if_missing=only_if_missing,
        retry_duration=retry_duration)  
    emit_to_topic(topic, sender, result=result)
    return result

def execute_script(
        script: str,
        *,
        auto_remove: bool = True,
        attributes: Mapping[str, str] | list[str] | None = None,
        event_id: str | None = None,
        retry_duration: int | None = None,
        topic: str | list[str] | Any = ANY,
        sender: str | Any = ANY):
    result = SSE.execute_script(script, 
                                auto_remove=auto_remove, 
                                attributes=attributes, 
                                event_id=event_id, 
                                retry_duration=retry_duration)
    emit_to_topic(topic, sender, result=result)
    return result

def redirect(
        location: str,
        topic: str | list[str] | Any = ANY,
        sender: str | Any = ANY):
    result = SSE.redirect(location)
    emit_to_topic(topic, sender, result=result)
    return result

__all__ = [
    'emit_elements',
    'remove_elements',
    'emit_signals',
    'execute_script',
    'redirect',
    'datastar_response',
]