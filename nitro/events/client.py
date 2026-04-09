"""
Nitro Events Client - SSE/WebSocket streaming support.

This module provides a backward-compatible Client that wraps nitro-events.Client
with deprecation warnings for old API patterns.

Usage:
    from nitro.events import Client
    
    async def sse_endpoint(request):
        async with Client(topics=["orders.*"]) as client:
            async for msg in client.stream():
                yield f"data: {msg.to_json()}\\n\\n"
"""
import warnings
from typing import Any

# Import from nitro-events
from nitro_events import (
    Client as BaseClient,
    TopicSubscription,
    Message,
    get_default_pubsub,
)
from nitro_events.client import SENTINEL


class Client(BaseClient):
    """Backward-compatible Client wrapper.
    
    Adds deprecation shims for:
    - stream(delay=...) → stream(timeout=...)
    - send(raw_data) → send(Message(...))
    """
    
    async def stream(self, timeout: float = 30.0, delay: float | None = None):
        """Stream messages with backward-compatible delay parameter.
        
        Args:
            timeout: Timeout between messages (new API)
            delay: Deprecated, use timeout instead
        """
        if delay is not None:
            warnings.warn(
                "Client.stream(delay=...) is deprecated, use timeout=... instead. "
                "Will be removed in v2.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            timeout = delay
        
        async for msg in super().stream(timeout=timeout):
            yield msg
    
    def send(self, item: Message | Any) -> bool:
        """Send a message to this client's queue.
        
        Args:
            item: Message object (preferred) or raw data (deprecated)
            
        Returns:
            True if sent successfully
        """
        if not isinstance(item, Message):
            warnings.warn(
                "Passing raw data to Client.send() is deprecated. "
                "Use Client.send(Message(topic='...', data=...)) instead. "
                "Will be removed in v2.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            # Create Message with default topic from subscriptions or 'direct'
            default_topic = self.topics[0] if self.topics else "direct"
            item = Message(topic=default_topic, data=item)
        
        return super().send(item)
    
    def send_data(self, topic: str, data: Any, **kwargs) -> bool:
        """Send data as a message directly to this client.
        
        This is the preferred way to send raw data (creates Message internally).
        
        Args:
            topic: Message topic
            data: Message payload
            **kwargs: Additional Message fields
            
        Returns:
            True if sent successfully
        """
        return super().send(Message(topic=topic, data=data, **kwargs))


# --- Legacy compatibility ---

def _get_active_clients():
    """Legacy accessor for active clients dict.
    
    Deprecated: Use Client.get_active_clients() instead.
    """
    warnings.warn(
        "active_clients is deprecated, use Client.get_active_clients() instead. "
        "Will be removed in v2.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    return Client.get_active_clients()


class _ActiveClientsProxy(dict):
    """Proxy for legacy active_clients access."""
    
    def __getitem__(self, key):
        return Client.get_active_clients().get(key)
    
    def __setitem__(self, key, value):
        warnings.warn("Direct active_clients modification is deprecated.", DeprecationWarning)
    
    def __contains__(self, key):
        return key in Client.get_active_clients()
    
    def __iter__(self):
        return iter(Client.get_active_clients())
    
    def __len__(self):
        return Client.client_count()
    
    def keys(self):
        return Client.get_active_clients().keys()
    
    def values(self):
        return Client.get_active_clients().values()
    
    def items(self):
        return Client.get_active_clients().items()
    
    def get(self, key, default=None):
        return Client.get_client(key) or default
    
    def pop(self, key, *args):
        client = Client.get_client(key)
        if client:
            client.disconnect()
            return client
        if args:
            return args[0]
        raise KeyError(key)


active_clients = _ActiveClientsProxy()
"""Legacy dict-like access to active clients.

Deprecated: Use Client.get_active_clients() or Client.get_client(id).
"""


# --- Exports ---

__all__ = [
    "Client",
    "TopicSubscription",
    "Message",
    "active_clients",
    "SENTINEL",
]
