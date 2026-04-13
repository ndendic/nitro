"""
EventBridge — bidirectional bridge between nitro.websocket rooms and nitro.events PubSub.

Allows WebSocket clients and SSE clients to share a common messaging bus.
Messages from WebSocket rooms can be forwarded to the event system, and
event system messages can be broadcast to WebSocket rooms.

Example::

    from nitro.websocket import RoomManager, EventBridge

    rooms = RoomManager()
    bridge = EventBridge(rooms)

    # Link the "chat" room to the "chat.*" PubSub topic
    bridge.link("chat", "chat.*")

    # Forward a WS message to the event system
    await bridge.ws_to_events("chat", message)

    # Forward an event system payload to the "chat" room
    await bridge.events_to_ws("chat", event_data)
"""

from __future__ import annotations

import logging
from typing import Any

from .base import RoomManager, WSMessage

logger = logging.getLogger(__name__)


class EventBridge:
    """Bridge between WebSocket rooms and the nitro.events PubSub system.

    Each link pairs a room name with a PubSub topic pattern.  Once linked:

    - Calling :meth:`ws_to_events` publishes a :class:`~nitro.events.Message`
      to the topic so SSE clients (and other PubSub subscribers) receive it.
    - Calling :meth:`events_to_ws` broadcasts a payload to the matching
      WebSocket room.

    Args:
        rooms: The :class:`RoomManager` that manages WebSocket connections.
    """

    def __init__(self, rooms: RoomManager) -> None:
        self.rooms = rooms
        self._links: dict[str, str] = {}  # room_name -> topic

    # ── Link management ───────────────────────────────────────────────────

    def link(self, room_name: str, topic: str) -> None:
        """Associate a WebSocket room with a PubSub topic.

        Args:
            room_name: The WebSocket room to link.
            topic: The PubSub topic (or pattern) to bind to.
        """
        self._links[room_name] = topic
        logger.debug("EventBridge: linked room %r <-> topic %r", room_name, topic)

    def unlink(self, room_name: str) -> None:
        """Remove the link for a room.

        Args:
            room_name: The room to unlink.
        """
        self._links.pop(room_name, None)

    def topic_for(self, room_name: str) -> str | None:
        """Return the PubSub topic linked to a room, or ``None``.

        Args:
            room_name: The room to look up.
        """
        return self._links.get(room_name)

    def linked_rooms(self) -> list[str]:
        """Return a sorted list of all room names that have active links."""
        return sorted(self._links.keys())

    # ── Direction: WS → Events ────────────────────────────────────────────

    async def ws_to_events(self, room_name: str, message: WSMessage) -> None:
        """Forward a WebSocket message to the nitro.events PubSub system.

        Publishes a :class:`~nitro_events.Message` to the topic linked to
        ``room_name``.  Does nothing if no link exists for the room.

        Args:
            room_name: The originating room name.
            message: The :class:`WSMessage` to forward.
        """
        topic = self._links.get(room_name)
        if topic is None:
            logger.debug("EventBridge.ws_to_events: room %r has no link, skipping", room_name)
            return

        try:
            from nitro_events import publish, Message as EventMessage

            event_msg = EventMessage(
                topic=topic,
                data={
                    "type": message.type,
                    "data": message.data,
                    "room": message.room,
                    "sender": message.sender,
                },
            )
            await publish(topic, event_msg)
            logger.debug(
                "EventBridge: forwarded WS message from room %r to topic %r",
                room_name,
                topic,
            )
        except Exception as exc:
            logger.error("EventBridge.ws_to_events error for room %r: %s", room_name, exc)

    # ── Direction: Events → WS ────────────────────────────────────────────

    async def events_to_ws(self, room_name: str, event_data: Any) -> None:
        """Broadcast an event system payload to a WebSocket room.

        Creates a broadcast :class:`WSMessage` and sends it to all clients
        in the named room.  Does nothing if the room does not exist.

        Args:
            room_name: The target WebSocket room.
            event_data: Arbitrary payload to broadcast (must be JSON-serialisable).
        """
        room = self.rooms.get(room_name)
        if room is None:
            logger.debug(
                "EventBridge.events_to_ws: room %r does not exist, skipping", room_name
            )
            return

        message = WSMessage(type="broadcast", data=event_data, room=room_name)
        await room.broadcast(message)
        logger.debug(
            "EventBridge: forwarded event data to room %r (%d clients)",
            room_name,
            room.count,
        )
