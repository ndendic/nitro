# nitro/tests/test_entity_registration.py
import pytest
import asyncio
from sqlmodel import SQLModel, Field
from nitro.domain.entities.base_entity import Entity
from nitro.routing.decorator import get, post, delete
from nitro.routing.metadata import get_action_metadata
from nitro.events.events import event, default_namespace


class TestEntityRegistration:
    """Entity.__init_subclass__ registers event handlers for decorated methods."""

    def setup_method(self):
        default_namespace.clear()

    def test_instance_method_registered(self):
        class RegTestCounter(Entity, table=True):
            __tablename__ = "reg_test_counter"
            id: str = Field(primary_key=True)
            count: int = 0

            @post()
            def increment(self, amount: int = 1):
                self.count += amount

        evt = event("RegTestCounter.increment")
        assert len(list(evt.receivers_for(None))) > 0

    def test_class_method_registered(self):
        class RegTestItem(Entity, table=True):
            __tablename__ = "reg_test_item"
            id: str = Field(primary_key=True)
            name: str = ""

            @get()
            @classmethod
            def load_all(cls):
                return []

        evt = event("RegTestItem.load_all")
        assert len(list(evt.receivers_for(None))) > 0

    def test_undecorated_method_not_registered(self):
        class RegTestPlain(Entity, table=True):
            __tablename__ = "reg_test_plain"
            id: str = Field(primary_key=True)

            def not_an_action(self):
                pass

        # Should not have created this event with any receivers
        evt = event("RegTestPlain.not_an_action")
        assert len(list(evt.receivers_for(None))) == 0

    def test_route_name_override(self):
        class RegTestUser(Entity, table=True):
            __tablename__ = "reg_test_user"
            __route_name__ = "users"
            id: str = Field(primary_key=True)

            @get()
            def profile(self):
                return {}

        evt = event("users.profile")
        assert len(list(evt.receivers_for(None))) > 0

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
