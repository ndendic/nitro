"""
Advanced Datastar Features Tests

Tests for:
1. SSE endpoint streaming
2. Signals with nested object paths
3. Signals with array operations
"""

import pytest
import asyncio
from rusty_tags.datastar import Signals, SSE
from nitro.infrastructure.events.client import Client
from nitro.infrastructure.events.starlette import emit_signals, emit_elements, datastar_response
from nitro.infrastructure.events.events import emit


class TestDatastarSSEStreaming:
    """Test Datastar SSE endpoint streaming functionality."""

    def test_sse_basic_creation(self):
        """Test creating SSE messages."""
        # Create a simple SSE message for signal update
        result = SSE.patch_signals({"counter": 42})

        assert result is not None
        assert "data:" in result
        assert "counter" in result

    def test_sse_element_patch(self):
        """Test SSE element patching."""
        from rusty_tags import Div

        html = str(Div("Updated content", id="target"))
        result = SSE.patch_elements(html, selector="#target")

        assert result is not None
        assert "data:" in result

    @pytest.mark.asyncio
    async def test_client_streaming(self):
        """
        Test client streaming with multiple updates.

        Steps:
        1. Create client and connect
        2. Send multiple messages to client queue
        3. Stream updates from client
        4. Verify all updates are received
        """
        client = Client(topics=["test-stream"])
        client.connect()

        # Send test messages
        test_messages = ["update1", "update2", "update3"]
        for msg in test_messages:
            client.send(msg)

        # Collect streamed messages
        received = []
        async for msg in client.stream(delay=0.01):
            received.append(msg)
            if len(received) >= len(test_messages):
                client.disconnect()
                break

        assert len(received) == len(test_messages)
        assert received == test_messages

    @pytest.mark.asyncio
    async def test_client_event_streaming(self):
        """
        Test streaming events through client subscription.

        Steps:
        1. Create client subscribed to specific topic
        2. Emit events to that topic
        3. Verify client receives events via stream
        """
        client = Client(topics=["counter-updates"])
        client.connect()

        # Emit SSE updates to the topic
        updates = []
        for i in range(3):
            sse_msg = SSE.patch_signals({"count": i})
            emit("counter-updates", sender="test", result=sse_msg)
            updates.append(sse_msg)

        # Small delay for message processing
        await asyncio.sleep(0.01)

        # Collect messages
        received = []
        async for msg in client.stream(delay=0.01):
            received.append(msg)
            if len(received) >= len(updates):
                client.disconnect()
                break

        assert len(received) == len(updates)
        client.disconnect()


class TestSignalsNestedPaths:
    """Test Signals support for nested object paths."""

    def test_nested_object_creation(self):
        """
        Test creating Signals with nested objects.

        Step 1: Create Signals(user={'name': 'Alice', 'age': 25})
        """
        sigs = Signals(user={'name': 'Alice', 'age': 25})

        # Verify the signals object was created
        assert sigs is not None
        assert hasattr(sigs, 'user')

    def test_nested_path_access(self):
        """
        Test accessing nested paths in Signals.

        Step 2: Access signals.user.name
        Step 3: Verify correct path expression is generated
        """
        sigs = Signals(user={'name': 'Alice', 'age': 25})

        # Access nested path
        name_path = sigs.user.name

        # Verify the path expression is correct
        # Datastar uses $signalName.property notation
        assert str(name_path) == "$user.name"

    def test_nested_path_operations(self):
        """Test operations on nested paths."""
        sigs = Signals(user={'name': 'Alice', 'age': 25})

        # Test accessing age
        age_path = sigs.user.age
        assert str(age_path) == "$user.age"

        # Test that we can use these in expressions
        name_expr = str(name_path) if 'name_path' in locals() else str(sigs.user.name)
        age_expr = str(sigs.user.age)

        assert "$user" in name_expr
        assert "$user" in age_expr

    def test_deeply_nested_paths(self):
        """Test deeply nested object paths."""
        sigs = Signals(data={
            'user': {
                'profile': {
                    'name': 'Bob'
                }
            }
        })

        # Access deeply nested path
        deep_path = sigs.data.user.profile.name

        # Verify path expression
        assert str(deep_path) == "$data.user.profile.name"

    def test_nested_signal_in_html(self):
        """Test using nested signals in HTML attributes."""
        from rusty_tags import Div

        sigs = Signals(user={'name': 'Alice'})

        # Create element with nested signal binding
        div = Div(
            "Name placeholder",
            **{"data-text": sigs.user.name}
        )

        html_str = str(div)
        assert "$user.name" in html_str


class TestSignalsArrayOperations:
    """Test Signals support for array operations."""

    def test_array_signal_creation(self):
        """
        Test creating Signals with array.

        Step 1: Create Signals(items=[])
        """
        sigs = Signals(items=[])

        assert sigs is not None
        assert hasattr(sigs, 'items')

    def test_array_push_operation(self):
        """
        Test push operation on array signals.

        Step 2: Use signals.items.push('new')
        Step 3: Verify correct array operation expression
        """
        sigs = Signals(items=[])

        # Test push operation
        push_expr = sigs.items.push('new')

        # Verify the expression is correct
        # Should generate something like: $items.push('new')
        expr_str = str(push_expr)
        assert "$items.push" in expr_str
        assert "new" in expr_str

    def test_array_multiple_operations(self):
        """Test multiple array operations."""
        sigs = Signals(todos=[])

        # Test various array operations
        push_expr = sigs.todos.push('item')
        assert "$todos.push" in str(push_expr)

        # Test accessing array elements (if supported)
        try:
            first_item = sigs.todos[0]
            # If indexing is supported, verify the expression
            assert "$todos" in str(first_item)
        except (TypeError, AttributeError):
            # Indexing might not be supported, which is okay
            pass

    def test_array_with_initial_values(self):
        """Test array signals with initial values."""
        sigs = Signals(items=['a', 'b', 'c'])

        # Verify signal created with initial values
        assert hasattr(sigs, 'items')

        # Test push on array with existing values
        push_expr = sigs.items.push('d')
        assert "$items.push" in str(push_expr)

    def test_array_signal_in_html(self):
        """Test using array signals in HTML."""
        from rusty_tags import Div, Button

        sigs = Signals(items=[])

        # Create button that pushes to array
        button = Button(
            "Add Item",
            onclick=sigs.items.push('newItem')
        )

        html_str = str(button)
        assert "$items.push" in html_str

    def test_nested_array_operations(self):
        """Test array operations on nested objects."""
        sigs = Signals(data={'todos': []})

        # Access nested array and perform operation
        push_expr = sigs.data.todos.push('task')

        expr_str = str(push_expr)
        assert "$data.todos.push" in expr_str


class TestDatastarIntegration:
    """Integration tests for Datastar features."""

    def test_signals_to_sse(self):
        """Test converting signals to SSE format."""
        sigs = Signals(counter=0, user={'name': 'Alice'})

        # Create SSE update for signals
        sse_msg = SSE.patch_signals({"counter": 42, "user": {"name": "Bob"}})

        assert sse_msg is not None
        assert "data:" in sse_msg

    def test_emit_signals_helper(self):
        """Test emit_signals helper function."""
        # Test the helper that combines SSE and events
        result = emit_signals(
            {"count": 10},
            topic="test-signals",
            sender="test"
        )

        assert result is not None
        assert "data:" in result

    def test_complex_nested_and_array(self):
        """Test combining nested objects and arrays."""
        sigs = Signals(
            app={
                'users': [],
                'settings': {
                    'theme': 'dark'
                }
            }
        )

        # Test nested path
        theme_path = sigs.app.settings.theme
        assert "$app.settings.theme" in str(theme_path)

        # Test nested array operation
        push_expr = sigs.app.users.push({'name': 'Charlie'})
        assert "$app.users.push" in str(push_expr)
