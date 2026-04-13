"""
Core abstractions for nitro.websocket — Room and RoomManager.

Provides:
- WSMessage   : Serializable WebSocket message envelope
- Room        : A named channel that tracks connections and broadcasts messages
- RoomManager : Registry that manages multiple rooms with join/leave lifecycle
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class WSMessage:
    """WebSocket message envelope.

    Attributes:
        type:   Message purpose — "message", "join", "leave", "error", "broadcast".
        data:   Arbitrary payload (must be JSON-serialisable).
        room:   Room/channel name this message is associated with.
        sender: Client ID of the originating connection.
    """

    def __init__(
        self,
        type: str,
        data: Any = None,
        room: str | None = None,
        sender: str | None = None,
    ) -> None:
        self.type = type
        self.data = data
        self.room = room
        self.sender = sender

    def to_json(self) -> str:
        """Serialise the message to a JSON string."""
        return json.dumps(
            {
                "type": self.type,
                "data": self.data,
                "room": self.room,
                "sender": self.sender,
            }
        )

    @classmethod
    def from_json(cls, raw: str) -> WSMessage:
        """Deserialise a JSON string into a WSMessage.

        Raises:
            json.JSONDecodeError: If ``raw`` is not valid JSON.
            KeyError: If ``raw`` is missing the required ``type`` field.
        """
        d = json.loads(raw)
        return cls(
            type=d["type"],
            data=d.get("data"),
            room=d.get("room"),
            sender=d.get("sender"),
        )

    def __repr__(self) -> str:
        return (
            f"WSMessage(type={self.type!r}, room={self.room!r}, "
            f"sender={self.sender!r}, data={self.data!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WSMessage):
            return NotImplemented
        return (
            self.type == other.type
            and self.data == other.data
            and self.room == other.room
            and self.sender == other.sender
        )


class Room:
    """A named WebSocket room/channel.

    Tracks connected clients and broadcasts messages to all (or all except one).

    Args:
        name: Unique room identifier.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._connections: dict[str, Any] = {}  # client_id -> ws connection

    def add(self, client_id: str, ws: Any) -> None:
        """Add a client connection to the room.

        Args:
            client_id: Unique identifier for the connecting client.
            ws: The WebSocket connection object (framework-specific).
        """
        self._connections[client_id] = ws
        logger.debug("Room %r: client %r joined (%d total)", self.name, client_id, self.count)

    def remove(self, client_id: str) -> None:
        """Remove a client from the room.  No-op if not present.

        Args:
            client_id: The client to remove.
        """
        self._connections.pop(client_id, None)
        logger.debug("Room %r: client %r left (%d remaining)", self.name, client_id, self.count)

    async def broadcast(self, message: WSMessage, exclude: str | None = None) -> None:
        """Send a message to all connected clients.

        Args:
            message: The message to broadcast.
            exclude: Optional client_id to skip (e.g. the sender).
        """
        payload = message.to_json()
        tasks = [
            ws.send(payload)
            for cid, ws in list(self._connections.items())
            if cid != exclude
        ]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.warning("Room %r: broadcast error: %s", self.name, result)

    @property
    def count(self) -> int:
        """Number of currently connected clients."""
        return len(self._connections)

    @property
    def client_ids(self) -> list[str]:
        """Sorted list of connected client IDs."""
        return sorted(self._connections.keys())

    def __repr__(self) -> str:
        return f"Room(name={self.name!r}, count={self.count})"


class RoomManager:
    """Registry that creates and manages WebSocket rooms.

    All join/leave operations go through here so room lifecycle
    (creation, cleanup) is handled in one place.
    """

    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        # client_id -> set of room names
        self._client_rooms: dict[str, set[str]] = {}

    # ── Room access ──────────────────────────────────────────────────────

    def get_or_create(self, name: str) -> Room:
        """Return the named room, creating it if it does not exist.

        Args:
            name: Room identifier.
        """
        if name not in self._rooms:
            self._rooms[name] = Room(name)
            logger.debug("RoomManager: created room %r", name)
        return self._rooms[name]

    def get(self, name: str) -> Room | None:
        """Return the named room or ``None`` if it does not exist.

        Args:
            name: Room identifier.
        """
        return self._rooms.get(name)

    # ── Membership ────────────────────────────────────────────────────────

    async def join(self, room_name: str, client_id: str, ws: Any) -> Room:
        """Add a client to a room, creating the room if necessary.

        Args:
            room_name: Target room name.
            client_id: The joining client's ID.
            ws: The WebSocket connection object.

        Returns:
            The room the client joined.
        """
        room = self.get_or_create(room_name)
        room.add(client_id, ws)
        self._client_rooms.setdefault(client_id, set()).add(room_name)
        return room

    async def leave(self, room_name: str, client_id: str) -> None:
        """Remove a client from a specific room.

        Args:
            room_name: The room to leave.
            client_id: The leaving client's ID.
        """
        room = self._rooms.get(room_name)
        if room is not None:
            room.remove(client_id)
        rooms = self._client_rooms.get(client_id)
        if rooms is not None:
            rooms.discard(room_name)

    async def leave_all(self, client_id: str) -> None:
        """Remove a client from every room they are in.

        Typically called on disconnect.

        Args:
            client_id: The departing client's ID.
        """
        room_names = list(self._client_rooms.pop(client_id, set()))
        for room_name in room_names:
            room = self._rooms.get(room_name)
            if room is not None:
                room.remove(client_id)

    async def broadcast(
        self,
        room_name: str,
        message: WSMessage,
        exclude: str | None = None,
    ) -> None:
        """Broadcast a message to all clients in a room.

        Args:
            room_name: Target room name.  No-op if the room does not exist.
            message: Message to send.
            exclude: Optional client_id to skip.
        """
        room = self._rooms.get(room_name)
        if room is not None:
            await room.broadcast(message, exclude=exclude)

    # ── Query helpers ─────────────────────────────────────────────────────

    def rooms_for(self, client_id: str) -> list[str]:
        """Return a sorted list of room names the client is currently in.

        Args:
            client_id: The client to look up.
        """
        return sorted(self._client_rooms.get(client_id, set()))

    def cleanup_empty(self) -> int:
        """Remove all rooms with zero connected clients.

        Returns:
            Number of rooms removed.
        """
        empty = [name for name, room in self._rooms.items() if room.count == 0]
        for name in empty:
            del self._rooms[name]
            logger.debug("RoomManager: removed empty room %r", name)
        return len(empty)

    def __repr__(self) -> str:
        return f"RoomManager(rooms={list(self._rooms.keys())})"
