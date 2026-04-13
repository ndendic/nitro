"""
WebSocket handler base class for nitro.websocket.

Provides a lifecycle-hook pattern (on_connect / on_message / on_disconnect)
so you can build custom WebSocket endpoints by subclassing WSHandler.

Example::

    from nitro.websocket import WSHandler, RoomManager, WSMessage

    class ChatHandler(WSHandler):
        async def on_connect(self, client_id: str, ws) -> None:
            await self.rooms.join("lobby", client_id, ws)

        async def on_message(self, client_id: str, ws, message: WSMessage) -> None:
            await self.rooms.broadcast("lobby", message, exclude=client_id)

        async def on_disconnect(self, client_id: str, ws) -> None:
            await self.rooms.leave_all(client_id)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .base import RoomManager, WSMessage

logger = logging.getLogger(__name__)


class WSHandler:
    """Base WebSocket handler with lifecycle hooks.

    Subclass and override ``on_connect``, ``on_message``, and
    ``on_disconnect`` to build custom WebSocket endpoints.  The
    ``handle()`` method drives the main receive loop and calls each hook
    at the right time.

    Args:
        rooms: Optional shared :class:`RoomManager`.  A new one is created
               per handler instance if not provided.
    """

    def __init__(self, rooms: RoomManager | None = None) -> None:
        self.rooms: RoomManager = rooms or RoomManager()

    # ── Lifecycle hooks ───────────────────────────────────────────────────

    async def on_connect(self, client_id: str, ws: Any) -> None:
        """Called when a new client connects.

        Override to join rooms, authenticate, or send a welcome message.

        Args:
            client_id: Unique identifier for this connection.
            ws: The WebSocket connection object.
        """

    async def on_message(self, client_id: str, ws: Any, message: WSMessage) -> None:
        """Called for each valid message received from the client.

        Args:
            client_id: The sending client's ID.
            ws: The WebSocket connection object.
            message: Parsed :class:`WSMessage` (sender field is already set).
        """

    async def on_disconnect(self, client_id: str, ws: Any) -> None:
        """Called when the client disconnects (or on any fatal error).

        Override to clean up room membership, release resources, etc.

        Args:
            client_id: The disconnecting client's ID.
            ws: The WebSocket connection object.
        """

    # ── Main loop ─────────────────────────────────────────────────────────

    async def handle(self, client_id: str, ws: Any) -> None:
        """Drive the WebSocket lifecycle for one connection.

        Sequence:
        1. Call ``on_connect``.
        2. Iterate incoming frames; parse each as :class:`WSMessage` and
           call ``on_message``.  Invalid JSON sends an error frame back.
        3. Call ``on_disconnect`` in a ``finally`` block so it always runs.

        Args:
            client_id: Unique identifier for this connection.
            ws: The WebSocket connection object.  Must support ``async for``
                iteration and a coroutine ``send(str)`` method.
        """
        try:
            try:
                await self.on_connect(client_id, ws)
            except Exception as exc:
                logger.error("WebSocket on_connect error for client %r: %s", client_id, exc)
                return

            try:
                async for raw in ws:
                    try:
                        message = WSMessage.from_json(raw)
                        message.sender = client_id
                        await self.on_message(client_id, ws, message)
                    except (json.JSONDecodeError, KeyError):
                        error = WSMessage(type="error", data="Invalid JSON", sender=None)
                        try:
                            await ws.send(error.to_json())
                        except Exception:
                            pass  # connection may already be closing
            except Exception as exc:
                logger.error("WebSocket error for client %r: %s", client_id, exc)
        finally:
            await self.on_disconnect(client_id, ws)
