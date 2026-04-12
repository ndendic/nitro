"""
Composable entity behaviors for the Nitro framework.

Each mixin is a standalone SQLModel subclass (no table=True) that can be
combined with Entity via multiple inheritance. The final entity class sets
table=True — not the mixins.

Usage example:

    from nitro.domain import Entity
    from nitro.domain.mixins import TimestampMixin, SlugMixin

    class Post(Entity, TimestampMixin, table=True):
        title: str = ""
        slug: str = ""

        def save(self):
            self.slug = self.generate_slug(self.title)
            return super().save()
"""

import re
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel

__all__ = [
    "TimestampMixin",
    "SoftDeleteMixin",
    "SlugMixin",
    "TaggableMixin",
    "AuditMixin",
]


def utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class TimestampMixin(SQLModel):
    """Adds created_at and updated_at timestamps to an entity.

    created_at is set once at insert time.
    updated_at is set at insert time and auto-updated at the SQLAlchemy level
    on every UPDATE statement via the onupdate hook.
    """

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={"nullable": False},
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={"nullable": False, "onupdate": utc_now},
    )


class SoftDeleteMixin(SQLModel):
    """Adds non-destructive deletion support to an entity.

    Instead of removing a row, soft-delete sets deleted_at to the current
    time. The restore() method clears that timestamp. The active() classmethod
    returns only non-deleted records.
    """

    deleted_at: Optional[datetime] = Field(
        default=None,
        index=True,
    )

    @property
    def is_deleted(self) -> bool:
        """True if this record has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark this record as deleted without removing it from the database."""
        self.deleted_at = utc_now()

    def restore(self) -> None:
        """Undo a soft delete by clearing the deleted_at timestamp."""
        self.deleted_at = None

    @classmethod
    def active(cls):
        """Return all records that have not been soft-deleted.

        Requires the entity to also inherit from Entity (which provides where()).

        Returns:
            List of non-deleted instances.
        """
        return cls.where(cls.deleted_at == None)  # noqa: E711


class SlugMixin(SQLModel):
    """Adds a URL-safe slug field and slug generation helper."""

    slug: str = Field(default="", index=True)

    @staticmethod
    def generate_slug(source: str) -> str:
        """Convert a source string into a URL-safe slug.

        Steps:
          1. Lowercase the string.
          2. Replace spaces and underscores with hyphens.
          3. Strip any characters that are not alphanumeric or hyphens.
          4. Collapse consecutive hyphens into one.
          5. Strip leading/trailing hyphens.

        Args:
            source: The string to slugify (e.g. a title or name).

        Returns:
            A lowercase, hyphen-separated slug string.
        """
        slug = source.lower()
        slug = re.sub(r"[ _]+", "-", slug)
        slug = re.sub(r"[^\w-]", "", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")
        return slug


class TaggableMixin(SQLModel):
    """Adds a JSON-backed list of string tags to an entity."""

    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, default=list),
    )

    def add_tag(self, tag: str) -> None:
        """Add a tag if it is not already present.

        Args:
            tag: The tag string to add.
        """
        if tag not in self.tags:
            self.tags = [*self.tags, tag]

    def remove_tag(self, tag: str) -> None:
        """Remove a tag if it exists. No-op if the tag is absent.

        Args:
            tag: The tag string to remove.
        """
        self.tags = [t for t in self.tags if t != tag]

    def has_tag(self, tag: str) -> bool:
        """Check whether a tag is present.

        Args:
            tag: The tag string to look for.

        Returns:
            True if the tag is in the tags list, False otherwise.
        """
        return tag in self.tags


class AuditMixin(SQLModel):
    """Tracks who created and last modified an entity, plus a version counter.

    created_by and updated_by store an identifier for the acting user
    (e.g. a username or user ID string). version starts at 1 and increments
    on each call to bump_version().
    """

    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)
    version: int = Field(default=1)

    def bump_version(self, editor: str) -> None:
        """Increment the version counter and record the editor's identity.

        Args:
            editor: Identifier of the user making the change.
        """
        self.version += 1
        self.updated_by = editor
