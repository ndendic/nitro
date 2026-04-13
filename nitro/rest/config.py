"""RESTConfig — per-entity REST API configuration."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, model_validator


def _pluralize(name: str) -> str:
    """Simple English pluralization."""
    if name.endswith("y") and name[-2:] not in ("ay", "ey", "oy", "uy"):
        return name[:-1] + "ies"
    if name.endswith(("s", "sh", "ch", "x", "z")):
        return name + "es"
    return name + "s"


class RESTConfig(BaseModel):
    """Configuration for REST API endpoint generation."""

    url_prefix: str = ""
    """URL prefix for routes (auto-derived from class name if empty).
    Example: '/api/products' """

    page_size: int = 20
    """Default page size for list endpoints."""

    max_page_size: int = 100
    """Maximum allowed page size (prevents abuse)."""

    include_fields: list[str] | None = None
    """Fields to include in responses (None = all)."""

    exclude_fields: list[str] | None = None
    """Fields to exclude from responses."""

    readonly_fields: list[str] | None = None
    """Fields that cannot be set via create/update (e.g. computed fields)."""

    sortable_fields: list[str] | None = None
    """Fields that can be sorted on (None = all)."""

    filterable_fields: list[str] | None = None
    """Fields that can be filtered on (None = all)."""

    searchable_fields: list[str] | None = None
    """Fields included in text search (None = all string fields)."""

    actions: list[str] = ["list", "get", "create", "update", "delete"]
    """Allowed REST actions."""

    enable_bulk: bool = False
    """Enable bulk create/update/delete endpoints."""

    enable_search: bool = True
    """Enable ?q= text search on list endpoint."""

    def resolve(self, entity_class) -> RESTConfig:
        """Return a copy with auto-derived fields filled in from *entity_class*."""
        data = self.model_dump()
        if not data["url_prefix"]:
            data["url_prefix"] = "/api/" + _pluralize(entity_class.__name__).lower()
        return RESTConfig(**data)
