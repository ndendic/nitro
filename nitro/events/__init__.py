"""
Nitro Events - PubSub messaging for SSE streaming and side effects.

Usage:
    from nitro.events import subscribe, publish, publish_sync, Signal, Message, Client
"""

# PubSub API
from .events import (
    subscribe,
    publish,
    publish_sync,
    Signal,
    Message,
    PubSub,
    get_default_pubsub,
    set_default_pubsub,
    match,
    filter_dict,
)

# Client
from .client import (
    Client,
    TopicSubscription,
    active_clients,
    SENTINEL,
)

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
    "active_clients",
    "SENTINEL",
]
