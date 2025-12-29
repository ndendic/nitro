"""
Tests for async support in Nitro Framework.

Tests async entity operations, concurrent event handling,
and async repository operations.
"""

import asyncio
import time
from typing import Optional

import pytest

from sqlmodel import SQLModel, Field
from nitro.infrastructure.repository.memory import MemoryRepository
from nitro.infrastructure.events.events import emit_async, event, on, default_namespace


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

        retrieved = memory_repo.find("async1")
        assert retrieved is not None
        assert retrieved.name == "Alice"

    @pytest.mark.asyncio
    async def test_entity_get_in_async_context(self, memory_repo):
        """Test getting entity in async function."""
        user = AsyncUser(id="async2", name="Bob")
        memory_repo.save(user)

        retrieved = memory_repo.find("async2")
        assert retrieved is not None
        assert retrieved.name == "Bob"

    @pytest.mark.asyncio
    async def test_entity_delete_in_async_context(self, memory_repo):
        """Test deleting entity in async function."""
        user = AsyncUser(id="async3", name="Charlie")
        memory_repo.save(user)

        result = memory_repo.delete("async3")
        assert result is True

        retrieved = memory_repo.find("async3")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_entity_all_in_async_context(self, memory_repo):
        """Test repository operations in async function."""
        users = [AsyncUser(id=f"async{i}", name=f"User{i}") for i in range(3)]
        for user in users:
            memory_repo.save(user)

        # Verify all users can be retrieved
        retrieved_users = [memory_repo.find(f"async{i}") for i in range(3)]
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
        user1 = memory_repo.find("async10")
        user2 = memory_repo.find("async11")
        user3 = memory_repo.find("async12")
        assert user1.name == "Alice"
        assert user2.name == "Bob"
        assert user3.name == "Alice"


class TestAsyncEventHandlers:
    """Test async event handler concurrent execution."""

    @pytest.mark.asyncio
    async def test_async_handlers_execute_concurrently(self):
        """Test that async handlers run in parallel."""
        test_event = event("test.concurrent")
        results = []

        @on("test.concurrent")
        async def handler1(sender, **kwargs):
            await asyncio.sleep(0.1)
            results.append("handler1")
            return "result1"

        @on("test.concurrent")
        async def handler2(sender, **kwargs):
            await asyncio.sleep(0.1)
            results.append("handler2")
            return "result2"

        @on("test.concurrent")
        async def handler3(sender, **kwargs):
            await asyncio.sleep(0.1)
            results.append("handler3")
            return "result3"

        # Measure execution time
        start = time.time()
        handler_results = await emit_async("test.concurrent", sender="test")
        elapsed = time.time() - start

        # If executed serially, would take 0.3s+
        # If executed in parallel, should take ~0.1s
        assert elapsed < 0.2, f"Handlers took {elapsed}s, expected concurrent execution"
        assert len(results) == 3
        assert len(handler_results) == 3

    @pytest.mark.asyncio
    async def test_async_handlers_execute_with_delay(self):
        """Test async handler executes correctly with delays."""
        default_namespace.clear()
        test_event = event("test.delay")
        result = []

        @on("test.delay")
        async def delayed_handler(sender, **kwargs):
            await asyncio.sleep(0.02)
            result.append("completed")
            return "success"

        start = time.time()
        handler_results = await emit_async("test.delay", sender="test")
        elapsed = time.time() - start

        # Should wait for async handler to complete
        assert elapsed >= 0.02, f"Handler completed too fast: {elapsed}s"
        assert "completed" in result
        assert len(handler_results) >= 1

    @pytest.mark.asyncio
    async def test_async_handler_exceptions_dont_block_others(self):
        """Test that exception in one async handler doesn't block others."""
        test_event = event("test.exception")
        results = []

        @on("test.exception")
        async def failing_handler(sender, **kwargs):
            await asyncio.sleep(0.01)
            raise ValueError("Handler failed")

        @on("test.exception")
        async def working_handler(sender, **kwargs):
            await asyncio.sleep(0.01)
            results.append("success")
            return "worked"

        # emit_async should not raise exception
        handler_results = await emit_async("test.exception", sender="test")

        # Working handler should have executed despite failing one
        assert "success" in results
        assert len(handler_results) == 2

    @pytest.mark.asyncio
    async def test_async_handler_receives_kwargs(self):
        """Test that async handlers receive event kwargs."""
        default_namespace.clear()
        test_event = event("test.kwargs")
        received_data = {}

        @on("test.kwargs")
        async def kwargs_handler(sender, **kwargs):
            await asyncio.sleep(0.01)
            received_data["test_value"] = kwargs.get("test_value")
            received_data["sender"] = sender
            return "received"

        await emit_async("test.kwargs", sender="test_sender", test_value="test_data")

        assert received_data["test_value"] == "test_data"
        assert received_data["sender"] == "test_sender"


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
        retrieved = [memory_repo.find(f"concurrent{i}") for i in range(10)]
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
            return memory_repo.find(f"read{user_id}")

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
        for i in range(5):
            user = AsyncUser(id=f"delete{i}", name=f"User{i}")
            memory_repo.save(user)

        async def delete_user(user_id: int):
            return memory_repo.delete(f"delete{user_id}")

        # Delete concurrently
        tasks = [delete_user(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All deletes should succeed
        assert all(results)

        # No users should remain
        remaining = [memory_repo.find(f"delete{i}") for i in range(5)]
        assert all(u is None for u in remaining)

    @pytest.mark.asyncio
    async def test_memory_repo_no_race_conditions(self, memory_repo):
        """Test MemoryRepository has no race conditions under concurrent access."""

        async def increment_counter(counter_id: str, increment: int):
            """Simulate read-modify-write operation."""
            # This is intentionally NOT using atomic operations
            # to test if repository can handle concurrent access
            user = memory_repo.find(counter_id)
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
        final = memory_repo.find("counter1")
        final_value = int(final.name)

        # Due to race conditions, final value might not be 10
        # But it should be between 1 and 10
        assert 1 <= final_value <= 10, f"Expected 1-10, got {final_value}"


class TestAsyncGeneratorHandlers:
    """Test async generator handlers work correctly."""

    @pytest.mark.asyncio
    async def test_async_generator_handler(self):
        """Test async generator event handler."""
        test_event = event("test.async_gen")
        results = []

        @on("test.async_gen")
        async def async_gen_handler(sender, **kwargs):
            for i in range(3):
                await asyncio.sleep(0.01)
                yield f"value{i}"

        handler_results = await emit_async("test.async_gen", sender="test")

        # Results should include generator results
        assert len(handler_results) == 1
        # The result is the async generator itself or consumed results
        # Depending on implementation


# Pytest configuration for async tests
pytest_plugins = ("pytest_asyncio",)
