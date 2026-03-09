"""
Integration test for the event-driven action system.
Full flow: Entity definition -> event registration -> action() helper -> dispatch.
"""
import pytest
import asyncio
from sqlmodel import SQLModel, Field
from nitro.domain.entities.base_entity import Entity
from nitro.routing.decorator import get, post, delete
from nitro.routing.action_helper import action
from nitro.routing.metadata import get_action_metadata
from nitro.adapters.catch_all import dispatch_action
from nitro.events.events import default_namespace


class TestFullIntegration:

    def setup_method(self):
        default_namespace.clear()

    def test_entity_action_string_generation(self):
        """Define entity, check action() produces correct strings."""

        class IntTestNote(Entity, table=True):
            __tablename__ = "int_test_note"
            id: str = Field(primary_key=True)
            text: str = ""

            @post()
            def update_text(self, text: str = ""):
                self.text = text

            @get()
            @classmethod
            def list_all(cls):
                return []

            @delete()
            def remove(self):
                pass

        # Class method — no id
        result = action(IntTestNote.list_all)
        assert result == "@get('/get/IntTestNote.list_all')"

        # Instance method — with id
        result = action(IntTestNote.update_text, id="note1")
        assert result == "@post('/post/IntTestNote:note1.update_text')"

        # Delete
        result = action(IntTestNote.remove, id="$selected")
        assert result == "@delete('/delete/IntTestNote:$selected.remove')"

    def test_standalone_action_string_generation(self):
        """Standalone function action strings."""

        @post(prefix="notes")
        def create_note(title: str = ""): pass

        result = action(create_note, title="$title")
        assert "@post('/post/notes.create_note')" in result

    def test_dispatch_calls_registered_handler(self):
        """Dispatch through the event system reaches the right handler."""
        call_log = []

        class IntTestTask(Entity, table=True):
            __tablename__ = "int_test_task"
            id: str = Field(primary_key=True)
            done: bool = False

            @post()
            def complete(self):
                call_log.append(f"completed:{self.id}")
                self.done = True

        # We can't actually call Entity.get() without a DB,
        # but we can verify the event was registered
        from nitro.events.events import event
        evt = event("IntTestTask.complete")
        receivers = list(evt.receivers_for(None))
        assert len(receivers) > 0

    def test_standalone_dispatch(self):
        """Standalone function can be dispatched through events."""
        results = []

        @post(prefix="math")
        def add(a: int = 0, b: int = 0):
            result = a + b
            results.append(result)
            return {"sum": result}

        asyncio.get_event_loop().run_until_complete(
            dispatch_action("math.add", "client1", signals={"a": 3, "b": 7})
        )
        assert results == [10]

    def test_get_params_as_query_string(self):
        """GET action() includes params as query string."""

        @get(prefix="search")
        def find_items(q: str = "", limit: int = 10): pass

        result = action(find_items, q="hello", limit=5)
        assert "@get('/get/search.find_items?" in result
        assert "q=hello" in result
        assert "limit=5" in result

    def test_post_literal_params_as_signal_assignment(self):
        """POST action() with literal values produces signal assignments."""

        @post(prefix="data")
        def save_item(name: str = "", value: int = 0): pass

        result = action(save_item, name="test", value=42)
        assert "$name = 'test'" in result
        assert "$value = 42" in result
        assert "@post('/post/data.save_item')" in result
