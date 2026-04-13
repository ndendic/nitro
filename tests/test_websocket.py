"""
Tests for nitro.websocket — rooms, handlers, and event bridge.

Covers:
- WSMessage serialisation / deserialisation
- Room membership, broadcasting, and exclusion
- RoomManager join/leave/leave_all/rooms_for/cleanup_empty
- WSHandler lifecycle (on_connect / on_message / on_disconnect)
- EventBridge link, ws_to_events, and events_to_ws
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from nitro.websocket.base import Room, RoomManager, WSMessage
from nitro.websocket.handler import WSHandler
from nitro.websocket.bridge import EventBridge


# ── Helpers ───────────────────────────────────────────────────────────────────


class MockWS:
    """Minimal mock WebSocket that records sent messages."""

    def __init__(self, messages: list[str] | None = None) -> None:
        self._messages = iter(messages or [])
        self.sent: list[str] = []
        self.send = AsyncMock(side_effect=self._record_send)

    async def _record_send(self, data: str) -> None:
        self.sent.append(data)

    def __aiter__(self) -> AsyncIterator[str]:
        return self

    async def __anext__(self) -> str:
        try:
            return next(self._messages)
        except StopIteration:
            raise StopAsyncIteration


def make_ws(*messages: str) -> MockWS:
    """Create a MockWS that yields the provided string frames."""
    return MockWS(list(messages))


# ── WSMessage ─────────────────────────────────────────────────────────────────


class TestWSMessage:
    def test_ws_message_serialization(self) -> None:
        msg = WSMessage(type="message", data={"text": "hello"}, room="lobby", sender="ws-abc")
        raw = msg.to_json()
        parsed = json.loads(raw)
        assert parsed["type"] == "message"
        assert parsed["data"] == {"text": "hello"}
        assert parsed["room"] == "lobby"
        assert parsed["sender"] == "ws-abc"

    def test_ws_message_round_trip(self) -> None:
        original = WSMessage(type="join", data=42, room="general", sender="ws-001")
        recovered = WSMessage.from_json(original.to_json())
        assert recovered == original

    def test_ws_message_defaults(self) -> None:
        msg = WSMessage(type="ping")
        assert msg.data is None
        assert msg.room is None
        assert msg.sender is None

    def test_ws_message_from_json(self) -> None:
        raw = json.dumps({"type": "leave", "data": None, "room": "lobby", "sender": "ws-x"})
        msg = WSMessage.from_json(raw)
        assert msg.type == "leave"
        assert msg.room == "lobby"

    def test_ws_message_from_json_invalid(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            WSMessage.from_json("not json at all")

    def test_ws_message_from_json_missing_type(self) -> None:
        raw = json.dumps({"data": "hello"})
        with pytest.raises(KeyError):
            WSMessage.from_json(raw)

    def test_ws_message_equality(self) -> None:
        a = WSMessage(type="message", data="hi", room="r", sender="s")
        b = WSMessage(type="message", data="hi", room="r", sender="s")
        assert a == b

    def test_ws_message_inequality(self) -> None:
        a = WSMessage(type="message", data="hi")
        b = WSMessage(type="error", data="hi")
        assert a != b


# ── Room ──────────────────────────────────────────────────────────────────────


class TestRoom:
    def test_room_add_remove(self) -> None:
        room = Room("lobby")
        ws = make_ws()
        room.add("c1", ws)
        assert "c1" in room.client_ids
        room.remove("c1")
        assert "c1" not in room.client_ids

    def test_room_remove_nonexistent(self) -> None:
        room = Room("lobby")
        room.remove("ghost")  # should not raise

    def test_room_count(self) -> None:
        room = Room("test")
        assert room.count == 0
        ws = make_ws()
        room.add("a", ws)
        room.add("b", ws)
        assert room.count == 2
        room.remove("a")
        assert room.count == 1

    @pytest.mark.asyncio
    async def test_room_broadcast(self) -> None:
        room = Room("chat")
        ws1 = make_ws()
        ws2 = make_ws()
        room.add("c1", ws1)
        room.add("c2", ws2)

        msg = WSMessage(type="message", data="hello", room="chat")
        await room.broadcast(msg)

        assert len(ws1.sent) == 1
        assert len(ws2.sent) == 1
        parsed = json.loads(ws1.sent[0])
        assert parsed["data"] == "hello"

    @pytest.mark.asyncio
    async def test_room_broadcast_exclude(self) -> None:
        room = Room("chat")
        ws1 = make_ws()
        ws2 = make_ws()
        room.add("sender", ws1)
        room.add("receiver", ws2)

        msg = WSMessage(type="message", data="test")
        await room.broadcast(msg, exclude="sender")

        assert len(ws1.sent) == 0  # sender excluded
        assert len(ws2.sent) == 1  # receiver gets it

    @pytest.mark.asyncio
    async def test_room_broadcast_empty_room(self) -> None:
        room = Room("empty")
        msg = WSMessage(type="ping")
        await room.broadcast(msg)  # should not raise

    def test_room_client_ids_sorted(self) -> None:
        room = Room("r")
        for cid in ["c3", "c1", "c2"]:
            room.add(cid, make_ws())
        assert room.client_ids == ["c1", "c2", "c3"]


# ── RoomManager ───────────────────────────────────────────────────────────────


class TestRoomManager:
    @pytest.mark.asyncio
    async def test_room_manager_join_leave(self) -> None:
        mgr = RoomManager()
        ws = make_ws()
        room = await mgr.join("lobby", "c1", ws)
        assert room.name == "lobby"
        assert "c1" in room.client_ids
        await mgr.leave("lobby", "c1")
        assert "c1" not in room.client_ids

    @pytest.mark.asyncio
    async def test_room_manager_get_or_create(self) -> None:
        mgr = RoomManager()
        r1 = mgr.get_or_create("alpha")
        r2 = mgr.get_or_create("alpha")
        assert r1 is r2

    @pytest.mark.asyncio
    async def test_room_manager_get_missing(self) -> None:
        mgr = RoomManager()
        assert mgr.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_room_manager_leave_all(self) -> None:
        mgr = RoomManager()
        ws = make_ws()
        await mgr.join("room1", "c1", ws)
        await mgr.join("room2", "c1", ws)
        await mgr.leave_all("c1")
        assert "c1" not in mgr.get_or_create("room1").client_ids
        assert "c1" not in mgr.get_or_create("room2").client_ids
        assert mgr.rooms_for("c1") == []

    @pytest.mark.asyncio
    async def test_room_manager_rooms_for(self) -> None:
        mgr = RoomManager()
        ws = make_ws()
        await mgr.join("alpha", "c1", ws)
        await mgr.join("beta", "c1", ws)
        rooms = mgr.rooms_for("c1")
        assert sorted(rooms) == ["alpha", "beta"]

    @pytest.mark.asyncio
    async def test_room_manager_rooms_for_unknown_client(self) -> None:
        mgr = RoomManager()
        assert mgr.rooms_for("nobody") == []

    @pytest.mark.asyncio
    async def test_room_manager_cleanup_empty(self) -> None:
        mgr = RoomManager()
        ws = make_ws()
        await mgr.join("occupied", "c1", ws)
        mgr.get_or_create("empty1")
        mgr.get_or_create("empty2")
        removed = mgr.cleanup_empty()
        assert removed == 2
        assert mgr.get("empty1") is None
        assert mgr.get("empty2") is None
        assert mgr.get("occupied") is not None

    @pytest.mark.asyncio
    async def test_room_manager_leave_nonexistent_room(self) -> None:
        mgr = RoomManager()
        await mgr.leave("ghost-room", "c1")  # should not raise

    @pytest.mark.asyncio
    async def test_room_manager_broadcast(self) -> None:
        mgr = RoomManager()
        ws1 = make_ws()
        ws2 = make_ws()
        await mgr.join("lobby", "c1", ws1)
        await mgr.join("lobby", "c2", ws2)
        msg = WSMessage(type="message", data="from manager")
        await mgr.broadcast("lobby", msg)
        assert len(ws1.sent) == 1
        assert len(ws2.sent) == 1

    @pytest.mark.asyncio
    async def test_room_manager_broadcast_missing_room(self) -> None:
        mgr = RoomManager()
        msg = WSMessage(type="ping")
        await mgr.broadcast("nonexistent", msg)  # should not raise


# ── WSHandler lifecycle ───────────────────────────────────────────────────────


class TestWSHandlerLifecycle:
    @pytest.mark.asyncio
    async def test_ws_handler_lifecycle(self) -> None:
        """on_connect / on_message / on_disconnect are called in order."""
        calls: list[str] = []

        class TrackingHandler(WSHandler):
            async def on_connect(self, client_id, ws):
                calls.append(f"connect:{client_id}")

            async def on_message(self, client_id, ws, message):
                calls.append(f"message:{message.data}")

            async def on_disconnect(self, client_id, ws):
                calls.append(f"disconnect:{client_id}")

        raw_msg = WSMessage(type="message", data="hi").to_json()
        ws = make_ws(raw_msg)
        handler = TrackingHandler()
        await handler.handle("test-client", ws)

        assert calls == [
            "connect:test-client",
            "message:hi",
            "disconnect:test-client",
        ]

    @pytest.mark.asyncio
    async def test_ws_handler_invalid_json_sends_error(self) -> None:
        """Non-JSON frames cause an error reply, not a crash."""

        class SimpleHandler(WSHandler):
            pass

        ws = make_ws("this is not json")
        handler = SimpleHandler()
        await handler.handle("c1", ws)

        assert len(ws.sent) == 1
        parsed = json.loads(ws.sent[0])
        assert parsed["type"] == "error"

    @pytest.mark.asyncio
    async def test_ws_handler_disconnect_on_error(self) -> None:
        """on_disconnect is always called, even if iteration raises."""
        disconnected: list[str] = []

        class ErrorHandler(WSHandler):
            async def on_connect(self, client_id, ws):
                raise RuntimeError("deliberate connect error")

            async def on_disconnect(self, client_id, ws):
                disconnected.append(client_id)

        ws = make_ws()
        handler = ErrorHandler()
        await handler.handle("err-client", ws)
        assert "err-client" in disconnected

    @pytest.mark.asyncio
    async def test_ws_handler_sender_set_on_message(self) -> None:
        """message.sender is set to client_id before on_message is called."""
        received: list[WSMessage] = []

        class CaptureHandler(WSHandler):
            async def on_message(self, client_id, ws, message):
                received.append(message)

        raw = WSMessage(type="message", data="test").to_json()
        ws = make_ws(raw)
        handler = CaptureHandler()
        await handler.handle("my-client", ws)

        assert len(received) == 1
        assert received[0].sender == "my-client"

    @pytest.mark.asyncio
    async def test_ws_handler_default_room_manager(self) -> None:
        handler = WSHandler()
        assert isinstance(handler.rooms, RoomManager)

    @pytest.mark.asyncio
    async def test_ws_handler_shared_room_manager(self) -> None:
        shared = RoomManager()
        h1 = WSHandler(rooms=shared)
        h2 = WSHandler(rooms=shared)
        assert h1.rooms is h2.rooms


# ── EventBridge ───────────────────────────────────────────────────────────────


class TestEventBridge:
    def test_event_bridge_link(self) -> None:
        mgr = RoomManager()
        bridge = EventBridge(mgr)
        bridge.link("chat", "chat.messages")
        assert bridge.topic_for("chat") == "chat.messages"
        assert "chat" in bridge.linked_rooms()

    def test_event_bridge_unlink(self) -> None:
        mgr = RoomManager()
        bridge = EventBridge(mgr)
        bridge.link("chat", "chat.*")
        bridge.unlink("chat")
        assert bridge.topic_for("chat") is None

    def test_event_bridge_linked_rooms(self) -> None:
        mgr = RoomManager()
        bridge = EventBridge(mgr)
        bridge.link("alpha", "a.*")
        bridge.link("beta", "b.*")
        assert bridge.linked_rooms() == ["alpha", "beta"]

    @pytest.mark.asyncio
    async def test_event_bridge_events_to_ws_broadcasts(self) -> None:
        """events_to_ws broadcasts a 'broadcast' WSMessage to the room."""
        mgr = RoomManager()
        ws = make_ws()
        await mgr.join("lobby", "c1", ws)

        bridge = EventBridge(mgr)
        bridge.link("lobby", "lobby.*")
        await bridge.events_to_ws("lobby", {"event": "update"})

        assert len(ws.sent) == 1
        parsed = json.loads(ws.sent[0])
        assert parsed["type"] == "broadcast"
        assert parsed["data"] == {"event": "update"}

    @pytest.mark.asyncio
    async def test_event_bridge_events_to_ws_missing_room(self) -> None:
        """events_to_ws on a non-existent room is a no-op."""
        mgr = RoomManager()
        bridge = EventBridge(mgr)
        bridge.link("nowhere", "x.*")
        await bridge.events_to_ws("nowhere", "payload")  # should not raise

    @pytest.mark.asyncio
    async def test_event_bridge_ws_to_events_no_link(self) -> None:
        """ws_to_events on an unlinked room is a no-op."""
        mgr = RoomManager()
        bridge = EventBridge(mgr)
        msg = WSMessage(type="message", data="hello", room="unlinked")
        await bridge.ws_to_events("unlinked", msg)  # should not raise

    @pytest.mark.asyncio
    async def test_event_bridge_ws_to_events_publishes(self) -> None:
        """ws_to_events publishes to the PubSub system."""
        mgr = RoomManager()
        bridge = EventBridge(mgr)
        bridge.link("chat", "chat.messages")

        msg = WSMessage(type="message", data="hello", room="chat", sender="c1")

        with patch("nitro_events.publish", new_callable=AsyncMock) as mock_publish:
            await bridge.ws_to_events("chat", msg)
            mock_publish.assert_awaited_once()
            call_args = mock_publish.call_args
            assert call_args[0][0] == "chat.messages"

    @pytest.mark.asyncio
    async def test_event_bridge_ws_to_events_import_error(self) -> None:
        """ws_to_events handles import errors gracefully."""
        mgr = RoomManager()
        bridge = EventBridge(mgr)
        bridge.link("chat", "chat.*")

        msg = WSMessage(type="message", data="x")
        with patch.dict("sys.modules", {"nitro_events": None}):
            # Should not raise; logs error instead
            await bridge.ws_to_events("chat", msg)
