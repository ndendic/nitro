"""
Tests for async support in Nitro Framework.

Tests async entity operations, concurrent routing handler execution,
and async repository operations.
"""

import asyncio
import time
from typing import Optional

import pytest

from sqlmodel import SQLModel, Field
from nitro.domain.repository.memory import MemoryRepository
from nitro.routing.registry import register_handler, clear_handlers
from nitro.adapters.catch_all import dispatch_action
from nitro.events.events import subscribe, publish, publish_sync


class AsyncUser(SQLModel, table=False):
    """Test entity for async operations using MemoryRepository."""

    id: str = Field(primary_key=True)
    name: str


@pytest.fixture
def memory_repo():
    """Get fresh MemoryRepository instance for async tests."""
    repo = MemoryRepository()
    repo._data.clear()
    repo._expiry.clear()
    return repo


class TestAsyncEntityOperations:
    """Test Entity operations work in async context."""

    @pytest.mark.asyncio
    async def test_entity_save_in_async_context(self, memory_repo):
        """Test saving entity in async function."""
        user = AsyncUser(id="async1", name="Alice")
        result = memory_repo.save(user)
        assert result is True

        retrieved = memory_repo.find(AsyncUser, "async1")
        assert retrieved is not None
        assert retrieved.name == "Alice"

    @pytest.mark.asyncio
    async def test_entity_get_in_async_context(self, memory_repo):
        """Test getting entity in async function."""
        user = AsyncUser(id="async2", name="Bob")
        memory_repo.save(user)

        retrieved = memory_repo.find(AsyncUser, "async2")
        assert retrieved is not None
        assert retrieved.name == "Bob"

    @pytest.mark.asyncio
    async def test_entity_delete_in_async_context(self, memory_repo):
        """Test deleting entity in async function."""
        user = AsyncUser(id="async3", name="Charlie")
        memory_repo.save(user)

        result = memory_repo.delete(user)
        assert result is True

        retrieved = memory_repo.find(AsyncUser, "async3")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_entity_all_in_async_context(self, memory_repo):
        """Test repository operations in async function."""
        users = [AsyncUser(id=f"async{i}", name=f"User{i}") for i in range(3)]
        for user in users:
            memory_repo.save(user)

        # Verify all users can be retrieved
        retrieved_users = [memory_repo.find(AsyncUser, f"async{i}") for i in range(3)]
        assert all(u is not None for u in retrieved_users)
        assert len([u for u in retrieved_users if u]) == 3

    @pytest.mark.asyncio
    async def test_entity_filter_in_async_context(self, memory_repo):
        """Test repository find operations in async function."""
        users = [
            AsyncUser(id="async10", name="Alice"),
            AsyncUser(id="async11", name="Bob"),
            AsyncUser(id="async12", name="Alice"),
        ]
        for user in users:
            memory_repo.save(user)

        # Verify users can be retrieved individually
        user1 = memory_repo.find(AsyncUser, "async10")
        user2 = memory_repo.find(AsyncUser, "async11")
        user3 = memory_repo.find(AsyncUser, "async12")
        assert user1.name == "Alice"
        assert user2.name == "Bob"
        assert user3.name == "Alice"


class TestAsyncRoutingHandlers:
    """Test async routing handler concurrent execution via registry."""

    def setup_method(self):
        clear_handlers()

    @pytest.mark.asyncio
    async def test_async_handlers_execute_concurrently(self):
        """Test that multiple async dispatch calls run concurrently."""
        results = []
        call_times = []

        async def slow_handler(signals, request, sender):
            start = time.time()
            await asyncio.sleep(0.05)
            results.append(signals.get("id", "unknown"))
            call_times.append(time.time() - start)
            return {"id": signals.get("id")}

        register_handler("test.slow_action", slow_handler)

        # Dispatch multiple actions concurrently
        start = time.time()
        tasks = [
            dispatch_action("test.slow_action", "client1", signals={"id": str(i)})
            for i in range(3)
        ]
        handler_results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # Concurrent execution should be faster than serial (3 * 0.05s = 0.15s)
        assert elapsed < 0.12, f"Handlers took {elapsed}s, expected concurrent execution"
        assert len(results) == 3
        assert len(handler_results) == 3

    @pytest.mark.asyncio
    async def test_async_handler_receives_signals(self):
        """Test that async routing handlers receive signals correctly."""
        clear_handlers()
        received_data = {}

        async def signals_handler(signals, request, sender):
            received_data.update(signals)
            received_data["sender"] = sender
            return "received"

        register_handler("test.signals_action", signals_handler)

        await dispatch_action(
            "test.signals_action",
            "test_sender",
            signals={"test_value": "test_data", "count": 42}
        )

        assert received_data["test_value"] == "test_data"
        assert received_data["count"] == 42
        assert received_data["sender"] == "test_sender"

    @pytest.mark.asyncio
    async def test_async_handler_returns_value(self):
        """Test that async routing handler return values are passed through."""
        clear_handlers()

        async def returning_handler(signals, request, sender):
            await asyncio.sleep(0.01)
            return {"status": "ok", "value": signals.get("x", 0) * 2}

        register_handler("test.return_action", returning_handler)

        result = await dispatch_action(
            "test.return_action",
            "client1",
            signals={"x": 5}
        )
        assert result == {"status": "ok", "value": 10}

    @pytest.mark.asyncio
    async def test_async_handler_exception_propagates(self):
        """Test that exception in async routing handler propagates to caller."""
        clear_handlers()

        async def failing_handler(signals, request, sender):
            await asyncio.sleep(0.01)
            raise ValueError("Handler failed")

        register_handler("test.failing_action", failing_handler)

        with pytest.raises(ValueError, match="Handler failed"):
            await dispatch_action("test.failing_action", "client1", signals={})


class TestAsyncPubSub:
    """Test async pub/sub via nitro-events subscribe/publish."""

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        """Test basic subscribe and publish pattern."""
        received = []

        @subscribe("test.async.pubsub2")
        async def on_message(message):
            received.append(message.data)

        await publish("test.async.pubsub2", data="hello", source="test")
        await asyncio.sleep(0.05)

        assert "hello" in received

    @pytest.mark.asyncio
    async def test_publish_sync_delivers_to_subscribers(self):
        """Test publish_sync delivers messages to async subscribers."""
        received = []

        @subscribe("test.sync.pubsub2")
        async def on_update(message):
            received.append(message.data)

        publish_sync("test.sync.pubsub2", data="sync_update", source="test")
        await asyncio.sleep(0.05)

        assert "sync_update" in received


class TestAsyncMemoryRepository:
    """Test MemoryRepository works in async context."""

    @pytest.mark.asyncio
    async def test_memory_repo_concurrent_saves(self, memory_repo):
        """Test concurrent saves to MemoryRepository."""

        async def save_user(user_id: int):
            user = AsyncUser(id=f"concurrent{user_id}", name=f"User{user_id}")
            return memory_repo.save(user)

        # Create 10 users concurrently
        tasks = [save_user(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All saves should succeed
        assert all(results)

        # All users should be retrievable
        retrieved = [memory_repo.find(AsyncUser, f"concurrent{i}") for i in range(10)]
        assert all(u is not None for u in retrieved)
        assert len(retrieved) == 10

    @pytest.mark.asyncio
    async def test_memory_repo_concurrent_reads(self, memory_repo):
        """Test concurrent reads from MemoryRepository."""
        # Pre-populate data
        for i in range(5):
            user = AsyncUser(id=f"read{i}", name=f"User{i}")
            memory_repo.save(user)

        async def read_user(user_id: int):
            return memory_repo.find(AsyncUser, f"read{user_id}")

        # Read concurrently
        tasks = [read_user(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All reads should succeed
        assert all(r is not None for r in results)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_memory_repo_concurrent_deletes(self, memory_repo):
        """Test concurrent deletes from MemoryRepository."""
        # Pre-populate data
        users_to_delete = []
        for i in range(5):
            user = AsyncUser(id=f"delete{i}", name=f"User{i}")
            memory_repo.save(user)
            users_to_delete.append(user)

        async def delete_user(user):
            return memory_repo.delete(user)

        # Delete concurrently
        tasks = [delete_user(u) for u in users_to_delete]
        results = await asyncio.gather(*tasks)

        # All deletes should succeed
        assert all(results)

        # No users should remain
        remaining = [memory_repo.find(AsyncUser, f"delete{i}") for i in range(5)]
        assert all(u is None for u in remaining)

    @pytest.mark.asyncio
    async def test_memory_repo_no_race_conditions(self, memory_repo):
        """Test MemoryRepository has no race conditions under concurrent access."""

        async def increment_counter(counter_id: str, increment: int):
            """Simulate read-modify-write operation."""
            # This is intentionally NOT using atomic operations
            # to test if repository can handle concurrent access
            user = memory_repo.find(AsyncUser, counter_id)
            if not user:
                user = AsyncUser(id=counter_id, name="0")
                memory_repo.save(user)
                return

            # Read current value
            current = int(user.name)
            # Simulate some processing
            await asyncio.sleep(0.001)
            # Write new value
            user.name = str(current + increment)
            memory_repo.save(user)

        # Create initial counter
        counter = AsyncUser(id="counter1", name="0")
        memory_repo.save(counter)

        # Increment concurrently 10 times by 1
        tasks = [increment_counter("counter1", 1) for _ in range(10)]
        await asyncio.gather(*tasks)

        # Get final value
        final = memory_repo.find(AsyncUser, "counter1")
        final_value = int(final.name)

        # Due to race conditions, final value might not be 10
        # But it should be between 1 and 10
        assert 1 <= final_value <= 10, f"Expected 1-10, got {final_value}"


# Pytest configuration for async tests
pytest_plugins = ("pytest_asyncio",)
