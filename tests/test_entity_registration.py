# nitro/tests/test_entity_registration.py
import pytest
import asyncio
from sqlmodel import SQLModel, Field
from nitro.domain.entities.base_entity import Entity
from nitro.routing.decorator import get, post, delete
from nitro.routing.metadata import get_action_metadata
from nitro.routing.registry import get_handler, clear_handlers


class TestEntityRegistration:
    """Entity.__init_subclass__ registers handlers in the routing registry for decorated methods."""

    def setup_method(self):
        clear_handlers()

    def test_instance_method_registered(self):
        class RegTestCounter(Entity, table=True):
            __tablename__ = "reg_test_counter"
            id: str = Field(primary_key=True)
            count: int = 0

            @post()
            def increment(self, amount: int = 1):
                self.count += amount

        handler = get_handler("RegTestCounter.increment")
        assert handler is not None

    def test_class_method_registered(self):
        class RegTestItem(Entity, table=True):
            __tablename__ = "reg_test_item"
            id: str = Field(primary_key=True)
            name: str = ""

            @get()
            @classmethod
            def load_all(cls):
                return []

        handler = get_handler("RegTestItem.load_all")
        assert handler is not None

    def test_undecorated_method_not_registered(self):
        class RegTestPlain(Entity, table=True):
            __tablename__ = "reg_test_plain"
            id: str = Field(primary_key=True)

            def not_an_action(self):
                pass

        # Should NOT have registered a handler for undecorated method
        handler = get_handler("RegTestPlain.not_an_action")
        assert handler is None

    def test_route_name_override(self):
        class RegTestUser(Entity, table=True):
            __tablename__ = "reg_test_user"
            __route_name__ = "users"
            id: str = Field(primary_key=True)

            @get()
            def profile(self):
                return {}

        handler = get_handler("users.profile")
        assert handler is not None

    def test_metadata_entity_class_name_filled(self):
        class RegTestWidget(Entity, table=True):
            __tablename__ = "reg_test_widget"
            id: str = Field(primary_key=True)

            @post()
            def activate(self):
                pass

        meta = get_action_metadata(RegTestWidget.activate)
        assert meta.entity_class_name == "RegTestWidget"
        assert meta.event_name == "RegTestWidget.activate"
