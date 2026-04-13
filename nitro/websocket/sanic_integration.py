"""
Sanic framework integration for nitro.websocket.

Provides a one-call helper to mount a :class:`WSHandler` on a Sanic app.

Example::

    from sanic import Sanic
    from nitro.websocket import WSHandler, sanic_websocket

    class Chat(WSHandler):
        async def on_connect(self, client_id, ws):
            await self.rooms.join("lobby", client_id, ws)

        async def on_message(self, client_id, ws, message):
            await self.rooms.broadcast("lobby", message, exclude=client_id)

        async def on_disconnect(self, client_id, ws):
            await self.rooms.leave_all(client_id)

    app = Sanic("ChatApp")
    sanic_websocket(app, Chat(), path="/ws/chat")
"""

from __future__ import annotations

import uuid

from .handler import WSHandler

try:
    from sanic import Sanic, Request, Websocket  # type: ignore[import]

    SANIC_AVAILABLE = True
except ImportError:
    SANIC_AVAILABLE = False


def sanic_websocket(
    app: "Sanic",
    handler: WSHandler,
    path: str = "/ws",
) -> None:
    """Register a WebSocket handler on a Sanic application.

    Each incoming connection receives a unique ``ws-<hex8>`` client ID and
    is handed off to ``handler.handle()``.

    Args:
        app: The Sanic application instance.
        handler: A configured :class:`WSHandler` (or subclass) instance.
        path: URL path to mount the WebSocket route on.

    Raises:
        ImportError: If Sanic is not installed.

    Example::

        sanic_websocket(app, Chat(), path="/ws/chat")
    """
    if not SANIC_AVAILABLE:
        raise ImportError(
            "Sanic is required for sanic_websocket. "
            "Install with: pip install sanic"
        )

    @app.websocket(path)
    async def _ws_route(request: "Request", ws: "Websocket") -> None:
        client_id = f"ws-{uuid.uuid4().hex[:8]}"
        await handler.handle(client_id, ws)
