"""CRUDConfig — per-entity CRUD configuration."""
from __future__ import annotations

from pydantic import BaseModel, model_validator


def _pluralize(name: str) -> str:
    """Simple English pluralization."""
    if name.endswith("y") and not name[-2] in "aeiou":
        return name[:-1] + "ies"
    if name.endswith(("s", "sh", "ch", "x", "z")):
        return name + "es"
    return name + "s"


class CRUDConfig(BaseModel):
    """Configuration for CRUD view generation."""

    title: str = ""
    """Human-readable plural name (auto-derived from class name if empty)."""

    title_singular: str = ""
    """Singular form (auto-derived from class name if empty)."""

    icon: str = ""
    """Lucide icon name, e.g. 'package'."""

    exclude_fields: list[str] = ["id"]
    """Fields excluded from all views by default."""

    list_fields: list[str] | None = None
    """Fields shown in table (None = all non-excluded)."""

    detail_fields: list[str] | None = None
    """Fields shown in detail card (None = all non-excluded)."""

    form_fields: list[str] | None = None
    """Fields in create/edit forms (None = all non-excluded)."""

    title_field: str | None = None
    """Field used as entity title in detail/card view."""

    description_field: str | None = None
    """Field used as subtitle in detail/card view."""

    sortable: bool = True
    """Enable sortable table headers."""

    page_size: int = 20
    """Rows per page (pagination)."""

    searchable: bool = True
    """Include search input above the list table."""

    search_fields: list[str] | None = None
    """Fields to search across (None = all string fields)."""

    actions: list[str] = ["create", "edit", "delete"]
    """Allowed CRUD actions."""

    url_prefix: str = ""
    """URL prefix for routes (auto-derived from class name if empty)."""

    @model_validator(mode="after")
    def _fill_defaults(self) -> CRUDConfig:
        # url_prefix is filled lazily via resolve() because we need the class name.
        return self

    def resolve(self, entity_class) -> CRUDConfig:
        """Return a copy with auto-derived fields filled in from *entity_class*."""
        name = entity_class.__name__
        data = self.model_dump()
        if not data["title"]:
            data["title"] = _pluralize(name)
        if not data["title_singular"]:
            data["title_singular"] = name
        if not data["url_prefix"]:
            data["url_prefix"] = "/" + _pluralize(name).lower()
        return CRUDConfig(**data)
