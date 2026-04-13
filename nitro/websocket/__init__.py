"""
nitro.websocket — WebSocket abstraction layer with room/channel management.

Provides a clean, framework-agnostic API for building real-time WebSocket
features, with optional integration into the nitro.events PubSub system so
WebSocket clients and SSE clients can share the same messaging bus.

Core classes:

- :class:`WSMessage`    : JSON-serialisable message envelope
- :class:`Room`         : A named channel tracking connections + broadcasting
- :class:`RoomManager`  : Registry for multiple rooms with join/leave lifecycle
- :class:`WSHandler`    : Base class with on_connect / on_message / on_disconnect hooks
- :class:`EventBridge`  : Bidirectional bridge to nitro.events PubSub

Sanic integration:

- :func:`sanic_websocket` : One-call route registration for Sanic apps

Quick start::

    from sanic import Sanic
    from nitro.websocket import WSHandler, sanic_websocket

    class Chat(WSHandler):
        async def on_connect(self, client_id, ws):
            await self.rooms.join("lobby", client_id, ws)

        async def on_message(self, client_id, ws, message):
            # Echo to everyone else in the room
            await self.rooms.broadcast("lobby", message, exclude=client_id)

        async def on_disconnect(self, client_id, ws):
            await self.rooms.leave_all(client_id)

    app = Sanic("ChatApp")
    sanic_websocket(app, Chat(), path="/ws/chat")

Bridge to nitro.events (SSE + WebSocket share one bus)::

    from nitro.websocket import RoomManager, EventBridge

    rooms = RoomManager()
    bridge = EventBridge(rooms)
    bridge.link("chat", "chat.messages")

    # In your WS handler:
    await bridge.ws_to_events("chat", message)   # WS → SSE clients

    # In your SSE subscriber:
    await bridge.events_to_ws("chat", payload)   # Event → WS clients
"""

from .base import WSMessage, Room, RoomManager
from .handler import WSHandler
from .bridge import EventBridge
from .sanic_integration import sanic_websocket

__all__ = [
    "WSMessage",
    "Room",
    "RoomManager",
    "WSHandler",
    "EventBridge",
    "sanic_websocket",
]
