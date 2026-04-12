"""
Tests for nitro.domain.mixins — composable entity behaviors.

Covers: TimestampMixin, SoftDeleteMixin, SlugMixin, TaggableMixin, AuditMixin.
"""

import time
from datetime import datetime, timezone

import pytest
from sqlmodel import Field

from nitro.domain.entities.base_entity import Entity
from nitro.domain.mixins import (
    AuditMixin,
    SlugMixin,
    SoftDeleteMixin,
    TaggableMixin,
    TimestampMixin,
    utc_now,
)


# ---------------------------------------------------------------------------
# Test entities (composed with mixins)
# ---------------------------------------------------------------------------


class TimestampedItem(Entity, TimestampMixin, table=True):
    __tablename__ = "test_timestamped_items"
    title: str = ""


class SoftDeletableItem(Entity, SoftDeleteMixin, table=True):
    __tablename__ = "test_soft_deletable_items"
    name: str = ""


class SluggableItem(Entity, SlugMixin, table=True):
    __tablename__ = "test_sluggable_items"
    title: str = ""


class AuditableItem(Entity, AuditMixin, table=True):
    __tablename__ = "test_auditable_items"
    name: str = ""


class ComposedItem(Entity, TimestampMixin, SoftDeleteMixin, SlugMixin, TaggableMixin, AuditMixin, table=True):
    """All 5 mixins composed — also used for TaggableMixin tests."""
    __tablename__ = "test_composed_items"
    title: str = ""


# ---------------------------------------------------------------------------
# utc_now helper
# ---------------------------------------------------------------------------


class TestUtcNow:
    def test_returns_utc_datetime(self):
        now = utc_now()
        assert isinstance(now, datetime)
        assert now.tzinfo == timezone.utc

    def test_is_close_to_current_time(self):
        before = datetime.now(timezone.utc)
        now = utc_now()
        after = datetime.now(timezone.utc)
        assert before <= now <= after


# ---------------------------------------------------------------------------
# TimestampMixin
# ---------------------------------------------------------------------------


class TestTimestampMixin:
    def test_created_at_defaults_to_utc(self, test_repository):
        test_repository.init_db()
        item = TimestampedItem(id="ts1", title="Hello")
        assert isinstance(item.created_at, datetime)
        assert item.created_at.tzinfo == timezone.utc

    def test_updated_at_defaults_to_utc(self, test_repository):
        test_repository.init_db()
        item = TimestampedItem(id="ts2", title="Hello")
        assert isinstance(item.updated_at, datetime)
        assert item.updated_at.tzinfo == timezone.utc

    def test_created_at_set_on_save(self, test_repository):
        test_repository.init_db()
        before = datetime.now(timezone.utc)
        item = TimestampedItem(id="ts3", title="Hello")
        item.save()
        after = datetime.now(timezone.utc)
        loaded = TimestampedItem.get("ts3")
        assert loaded is not None
        # created_at should be within the window
        assert before <= loaded.created_at.replace(tzinfo=timezone.utc) <= after


# ---------------------------------------------------------------------------
# SoftDeleteMixin
# ---------------------------------------------------------------------------


class TestSoftDeleteMixin:
    def test_not_deleted_by_default(self, test_repository):
        test_repository.init_db()
        item = SoftDeletableItem(id="sd1", name="Alive")
        assert item.is_deleted is False
        assert item.deleted_at is None

    def test_soft_delete_sets_deleted_at(self, test_repository):
        test_repository.init_db()
        item = SoftDeletableItem(id="sd2", name="Soon gone")
        item.soft_delete()
        assert item.is_deleted is True
        assert item.deleted_at is not None
        assert isinstance(item.deleted_at, datetime)

    def test_restore_clears_deleted_at(self, test_repository):
        test_repository.init_db()
        item = SoftDeletableItem(id="sd3", name="Revived")
        item.soft_delete()
        assert item.is_deleted is True
        item.restore()
        assert item.is_deleted is False
        assert item.deleted_at is None

    def test_soft_delete_roundtrip_via_db(self, test_repository):
        test_repository.init_db()
        item = SoftDeletableItem(id="sd4", name="Persisted")
        item.save()
        item.soft_delete()
        item.save()
        loaded = SoftDeletableItem.get("sd4")
        assert loaded.is_deleted is True

    def test_active_classmethod_filters(self, test_repository):
        test_repository.init_db()
        alive = SoftDeletableItem(id="sd5", name="Alive")
        alive.save()
        dead = SoftDeletableItem(id="sd6", name="Dead")
        dead.soft_delete()
        dead.save()
        active = SoftDeletableItem.active()
        active_ids = [a.id for a in active]
        assert "sd5" in active_ids
        assert "sd6" not in active_ids


# ---------------------------------------------------------------------------
# SlugMixin
# ---------------------------------------------------------------------------


class TestSlugMixin:
    def test_simple_slug(self):
        assert SlugMixin.generate_slug("Hello World") == "hello-world"

    def test_preserves_numbers(self):
        assert SlugMixin.generate_slug("Version 2.0") == "version-20"

    def test_strips_special_chars(self):
        assert SlugMixin.generate_slug("Hello! @World#") == "hello-world"

    def test_collapses_hyphens(self):
        assert SlugMixin.generate_slug("a---b") == "a-b"

    def test_strips_leading_trailing_hyphens(self):
        assert SlugMixin.generate_slug("--hello--") == "hello"

    def test_underscores_become_hyphens(self):
        assert SlugMixin.generate_slug("hello_world") == "hello-world"

    def test_empty_string(self):
        assert SlugMixin.generate_slug("") == ""

    def test_unicode_letters(self):
        # Non-ASCII word characters should be kept by \w
        slug = SlugMixin.generate_slug("Café Résumé")
        assert "caf" in slug
        assert "r" in slug

    def test_slug_field_persists(self, test_repository):
        test_repository.init_db()
        item = SluggableItem(id="sl1", title="My Post")
        item.slug = SlugMixin.generate_slug(item.title)
        item.save()
        loaded = SluggableItem.get("sl1")
        assert loaded.slug == "my-post"


# ---------------------------------------------------------------------------
# TaggableMixin
# ---------------------------------------------------------------------------


class TestTaggableMixin:
    def test_empty_tags_by_default(self, test_repository):
        test_repository.init_db()
        item = ComposedItem(id="tg1", title="Clean")
        assert item.tags == []

    def test_add_tag(self):
        item = ComposedItem(id="tg2", title="Tagged")
        item.add_tag("python")
        assert item.has_tag("python")
        assert "python" in item.tags

    def test_add_tag_no_duplicates(self):
        item = ComposedItem(id="tg3", title="NoDup")
        item.add_tag("python")
        item.add_tag("python")
        assert item.tags.count("python") == 1

    def test_remove_tag(self):
        item = ComposedItem(id="tg4", title="Remove")
        item.add_tag("python")
        item.add_tag("rust")
        item.remove_tag("python")
        assert not item.has_tag("python")
        assert item.has_tag("rust")

    def test_remove_nonexistent_tag_is_noop(self):
        item = ComposedItem(id="tg5", title="Safe")
        item.add_tag("python")
        item.remove_tag("golang")  # should not raise
        assert item.tags == ["python"]

    def test_has_tag_false(self):
        item = ComposedItem(id="tg6", title="Empty")
        assert not item.has_tag("anything")

    def test_tags_persist_via_db(self, test_repository):
        test_repository.init_db()
        item = ComposedItem(id="tg7", title="Saved")
        item.add_tag("web")
        item.add_tag("api")
        item.save()
        loaded = ComposedItem.get("tg7")
        assert loaded.has_tag("web")
        assert loaded.has_tag("api")


# ---------------------------------------------------------------------------
# AuditMixin
# ---------------------------------------------------------------------------


class TestAuditMixin:
    def test_defaults(self):
        item = AuditableItem(id="au1", name="Fresh")
        assert item.version == 1
        assert item.created_by is None
        assert item.updated_by is None

    def test_bump_version(self):
        item = AuditableItem(id="au2", name="Bumped")
        item.bump_version("alice")
        assert item.version == 2
        assert item.updated_by == "alice"

    def test_multiple_bumps(self):
        item = AuditableItem(id="au3", name="Multi")
        item.bump_version("alice")
        item.bump_version("bob")
        item.bump_version("charlie")
        assert item.version == 4
        assert item.updated_by == "charlie"

    def test_audit_persists(self, test_repository):
        test_repository.init_db()
        item = AuditableItem(id="au4", name="Persisted", created_by="system")
        item.bump_version("admin")
        item.save()
        loaded = AuditableItem.get("au4")
        assert loaded.version == 2
        assert loaded.created_by == "system"
        assert loaded.updated_by == "admin"


# ---------------------------------------------------------------------------
# Mixin composition (all 5 mixed in)
# ---------------------------------------------------------------------------


class TestMixinComposition:
    def test_all_mixins_compose(self, test_repository):
        test_repository.init_db()
        item = ComposedItem(id="comp1", title="Full Stack", created_by="nikola")
        item.slug = SlugMixin.generate_slug(item.title)
        item.add_tag("nitro")
        item.bump_version("nikola")
        item.save()

        loaded = ComposedItem.get("comp1")
        # TimestampMixin
        assert loaded.created_at is not None
        assert loaded.updated_at is not None
        # SoftDeleteMixin
        assert loaded.is_deleted is False
        # SlugMixin
        assert loaded.slug == "full-stack"
        # TaggableMixin
        assert loaded.has_tag("nitro")
        # AuditMixin
        assert loaded.version == 2
        assert loaded.created_by == "nikola"

    def test_soft_delete_composed(self, test_repository):
        test_repository.init_db()
        item = ComposedItem(id="comp2", title="Doomed")
        item.save()
        item.soft_delete()
        item.save()
        active = ComposedItem.active()
        assert all(a.id != "comp2" for a in active)
