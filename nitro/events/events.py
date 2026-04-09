"""
Nitro Events - Re-exports from nitro-events.

The event system (PubSub) is for async messaging: SSE streaming,
notifications, side effects. NOT for HTTP routing — that uses the
handler registry in nitro.routing.registry.

Usage:
    from nitro.events import subscribe, publish, publish_sync, Signal, Message
"""
import inspect
from functools import wraps

from nitro_events import (
    PubSub,
    Signal,
    Message,
    Client,
    TopicSubscription,
    get_default_pubsub,
    set_default_pubsub,
    publish,
    publish_sync,
    subscribe as _subscribe,
    match,
    filter_dict,
)


def subscribe(pattern: str, **kwargs):
    """Subscribe a handler to a PubSub topic pattern.

    Wraps nitro-events subscribe to auto-consume async generator handlers.
    This allows handlers to use `yield` for backward compatibility:

        @subscribe("page.button")
        async def get_button(msg):
            yield emit_elements(page, source=msg.source)

    The yield result is discarded — emit_elements publishes via PubSub as a side effect.
    """
    def decorator(fn):
        if inspect.isasyncgenfunction(fn):
            @wraps(fn)
            async def wrapper(msg):
                async for _ in fn(msg):
                    pass
            return _subscribe(pattern, **kwargs)(wrapper)
        if inspect.isgeneratorfunction(fn):
            @wraps(fn)
            async def wrapper(msg):
                for _ in fn(msg):
                    pass
            return _subscribe(pattern, **kwargs)(wrapper)
        return _subscribe(pattern, **kwargs)(fn)
    return decorator


__all__ = [
    "subscribe",
    "publish",
    "publish_sync",
    "Signal",
    "Message",
    "Client",
    "TopicSubscription",
    "PubSub",
    "get_default_pubsub",
    "set_default_pubsub",
    "match",
    "filter_dict",
]
