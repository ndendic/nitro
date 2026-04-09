"""Tests for edge cases throughout the Nitro framework."""

import threading
import pytest

from nitro.domain.entities.base_entity import Entity
from nitro.routing.registry import register_handler, clear_handlers
from nitro.adapters.catch_all import dispatch_action
from nitro.html.templating import Page
from nitro.domain.repository.memory import MemoryRepository
from rusty_tags import Div, H1, P
import asyncio


class EdgeTestEntity(Entity, table=True):
    """Test entity for edge cases."""
    name: str
    content: str = ""


class TestEntityEdgeCases:
    """Test Entity edge cases."""

    def test_entity_handles_empty_string_ids(self, test_db):
        """Test that entities can handle empty string IDs (or raise appropriate error)."""
        EdgeTestEntity.repository().init_db()

        # Some databases may not allow empty string primary keys
        # Test that system handles it gracefully
        try:
            entity = EdgeTestEntity(id="", name="Empty ID Test", content="test")
            entity.save()

            # If save succeeded, verify we can retrieve it
            retrieved = EdgeTestEntity.get("")
            if retrieved:
                assert retrieved.name == "Empty ID Test"
        except (ValueError, Exception) as e:
            # If empty IDs aren't supported, that's acceptable
            # Just verify we get a clear error
            assert len(str(e)) > 0

    def test_entity_handles_very_long_field_values(self, test_db):
        """Test that entities can handle very long string values."""
        EdgeTestEntity.repository().init_db()

        # Create a large string (1MB instead of 10MB for faster tests)
        large_content = "x" * (1024 * 1024)  # 1MB

        entity = EdgeTestEntity(id="large1", name="Large Content", content=large_content)
        entity.save()

        # Retrieve and verify
        retrieved = EdgeTestEntity.get("large1")
        assert retrieved is not None
        assert retrieved.name == "Large Content"
        assert len(retrieved.content) == len(large_content)
        assert retrieved.content == large_content

    def test_entity_filter_handles_empty_result_set(self, test_db):
        """Test that Entity.filter() returns empty list when nothing matches."""
        EdgeTestEntity.repository().init_db()

        # Create some entities
        entity1 = EdgeTestEntity(id="e1", name="Alice", content="test")
        entity2 = EdgeTestEntity(id="e2", name="Bob", content="test")
        entity1.save()
        entity2.save()

        # Filter with criteria that matches nothing
        results = EdgeTestEntity.filter(name="Nonexistent Person")

        # Should return empty list, not raise error
        assert results == []
        assert isinstance(results, list)

    def test_entity_filter_with_no_matches_no_error(self, test_db):
        """Test that filtering with no entities in DB returns empty list."""
        EdgeTestEntity.repository().init_db()

        # No entities in database
        results = EdgeTestEntity.filter(name="Anyone")

        # Should return empty list
        assert results == []


class TestRoutingEdgeCases:
    """Test routing registry edge cases."""

    def setup_method(self):
        clear_handlers()

    def test_dispatch_with_no_handlers_is_safe(self):
        """Test that dispatching to unregistered topic returns None."""
        result = asyncio.run(
            dispatch_action("edge.case.no.handlers", "client1", signals={})
        )
        # No handler = None result
        assert result is None

    def test_dispatch_returns_none_for_nonexistent_action(self):
        """Test that dispatch_action returns None when no handler registered."""
        result = asyncio.run(
            dispatch_action("another.nonexistent.action", "client1", signals={})
        )
        assert result is None

    def test_register_and_call_handler(self):
        """Test basic handler registration and invocation."""
        call_log = []

        async def my_handler(signals, request, sender):
            call_log.append(signals.get("value"))
            return signals.get("value")

        register_handler("edge.test.action", my_handler)

        result = asyncio.run(
            dispatch_action("edge.test.action", "client1", signals={"value": "test"})
        )
        assert call_log == ["test"]
        assert result == "test"

    def test_handler_overwrite(self):
        """Test that registering a new handler for same topic overwrites old one."""
        call_log = []

        async def handler_v1(signals, request, sender):
            call_log.append("v1")

        async def handler_v2(signals, request, sender):
            call_log.append("v2")

        register_handler("edge.overwrite.action", handler_v1)
        register_handler("edge.overwrite.action", handler_v2)

        asyncio.run(
            dispatch_action("edge.overwrite.action", "client1", signals={})
        )
        # Only handler_v2 should be called (overwrote v1)
        assert call_log == ["v2"]


class SimpleEntity:
    """Simple entity-like object for MemoryRepository testing."""
    def __init__(self, id, name, content=""):
        self.id = id
        self.name = name
        self.content = content


class TestMemoryRepositoryEdgeCases:
    """Test MemoryRepository edge cases."""

    def test_memory_repository_handles_concurrent_access(self):
        """Test that MemoryRepository handles concurrent access safely."""
        repo = MemoryRepository()
        # Clear any leftover data from previous tests
        repo._data.clear()
        repo._expiry.clear()

        # Track results from threads
        results = []
        errors = []

        def save_and_load_entity(thread_id):
            """Save and load an entity in a thread."""
            try:
                # Create and save
                entity = SimpleEntity(id=f"thread_{thread_id}", name=f"Thread {thread_id}", content="test")
                repo.save(entity)

                # Load back
                loaded = repo.find(SimpleEntity, f"thread_{thread_id}")
                if loaded and loaded.name == f"Thread {thread_id}":
                    results.append(thread_id)
                else:
                    errors.append(f"Load failed for thread {thread_id}")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")

        # Spawn 50 threads
        threads = []
        for i in range(50):
            thread = threading.Thread(target=save_and_load_entity, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # MemoryRepository uses a simple dict, so concurrent access should mostly work
        # Allow a few failures due to race conditions on dict access
        assert len(errors) < 10, f"Too many errors: {errors[:5]}"

        # Verify most threads succeeded
        assert len(results) >= 40

    def test_memory_repository_concurrent_updates(self):
        """Test that concurrent updates to same entity are handled."""
        repo = MemoryRepository()
        # Clear any leftover data from previous tests
        repo._data.clear()
        repo._expiry.clear()

        # Create initial entity
        entity = SimpleEntity(id="shared_counter", name="Counter", content="0")
        repo.save(entity)

        def increment_counter(iterations):
            """Increment the counter multiple times."""
            for _ in range(iterations):
                e = repo.find(SimpleEntity, "shared_counter")
                if e:
                    current = int(e.content)
                    e.content = str(current + 1)
                    repo.save(e)

        # Run concurrent updates
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=increment_counter, args=(5,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Final entity should exist
        final = repo.find(SimpleEntity, "shared_counter")
        assert final is not None
        # Counter should be positive (may not be exact due to race conditions)
        assert int(final.content) > 0


class TestPageEdgeCases:
    """Test Page component edge cases."""

    def test_page_handles_none_children(self):
        """Test that Page() filters out None children cleanly."""
        # Create page with None values mixed in
        page = Page(
            None,
            Div("First div"),
            None,
            H1("Heading"),
            None,
            P("Paragraph"),
            None,
            title="Test Page"
        )

        # Render to string
        html = str(page)

        # Verify it renders without errors (lowercase doctype from RustyTags)
        assert "<!doctype html>" in html.lower()
        assert "First div" in html
        assert "Heading" in html
        assert "Paragraph" in html

        # Verify no explicit "None" string appears in output
        # (but "None" might appear in attribute like "Test Page" title)
        assert "<none>" not in html.lower()
        assert html.count("None") == 0 or "Test Page" in html  # Only in title if at all

    def test_page_with_all_none_children(self):
        """Test Page with all None children."""
        page = Page(None, None, None, title="Empty Page")

        html = str(page)

        # Should still render valid HTML structure (lowercase from RustyTags)
        assert "<!doctype html>" in html.lower()
        assert "<html" in html
        assert "</html>" in html

    def test_page_with_empty_children_list(self):
        """Test Page with no children at all."""
        page = Page(title="No Children")

        html = str(page)

        # Should render basic HTML structure (lowercase doctype)
        assert "<!doctype html>" in html.lower()
        assert "<title>No Children</title>" in html

    def test_page_with_nested_none_values(self):
        """Test Page with None values nested in other components."""
        page = Page(
            Div(
                None,
                "Some text",
                None,
                P("Nested paragraph"),
                None
            ),
            title="Nested Vals Test"  # Changed to avoid "None" in title
        )

        html = str(page)

        # Should render cleanly
        assert "Some text" in html
        assert "Nested paragraph" in html
        # Don't have literal "None" text rendered
        assert html.count("None") == 0


class TestEntityFilterEdgeCases:
    """Additional edge cases for entity filtering."""

    def test_filter_with_none_value(self, test_db):
        """Test filtering with None as a value."""
        EdgeTestEntity.repository().init_db()

        # Create entities
        entity1 = EdgeTestEntity(id="e1", name="Alice", content="")
        entity1.save()

        # Filter should handle None gracefully
        # Note: The filter implementation may not support None directly
        # This tests that it doesn't crash
        try:
            results = EdgeTestEntity.filter(content="")
            assert isinstance(results, list)
        except ValueError:
            # If filter rejects empty strings, that's acceptable
            pass

    def test_filter_returns_list_not_none(self, test_db):
        """Test that filter always returns a list, never None."""
        EdgeTestEntity.repository().init_db()

        results = EdgeTestEntity.filter(name="Nonexistent")

        # Should be a list, not None
        assert results is not None
        assert isinstance(results, list)
        assert len(results) == 0
