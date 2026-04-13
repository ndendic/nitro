"""
Core pagination types for nitro.pagination.

Provides two pagination strategies:
- Offset-based: PageInfo + Page[T]
- Cursor-based: CursorInfo + CursorPage[T]
"""

from __future__ import annotations

import math
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel, model_validator

T = TypeVar("T")


class PageInfo(BaseModel):
    """Pagination metadata for offset-based pagination."""

    page: int
    """Current page number (1-based)."""

    size: int
    """Number of items per page."""

    total: int
    """Total number of items across all pages."""

    pages: int
    """Total number of pages."""

    has_next: bool
    """True if there is a page after the current one."""

    has_prev: bool
    """True if there is a page before the current one."""

    @model_validator(mode="before")
    @classmethod
    def _derive_fields(cls, data: dict) -> dict:
        """Auto-compute pages/has_next/has_prev when not provided."""
        if isinstance(data, dict):
            total = data.get("total", 0)
            size = data.get("size", 1) or 1
            page = data.get("page", 1)
            if "pages" not in data:
                data["pages"] = math.ceil(total / size) if total > 0 else 0
            pages = data["pages"]
            if "has_next" not in data:
                data["has_next"] = page < pages
            if "has_prev" not in data:
                data["has_prev"] = page > 1
        return data


class Page(BaseModel, Generic[T]):
    """A page of results using offset-based pagination."""

    items: Sequence[T]
    """The items on this page."""

    info: PageInfo
    """Pagination metadata."""


class CursorInfo(BaseModel):
    """Pagination metadata for cursor-based pagination."""

    cursor: str | None
    """The cursor that was used to retrieve this page (None for first page)."""

    next_cursor: str | None
    """The cursor to use to retrieve the next page (None if no more pages)."""

    has_more: bool
    """True if there are more items beyond this page."""

    size: int
    """Number of items per page requested."""


class CursorPage(BaseModel, Generic[T]):
    """A cursor-paginated page of results."""

    items: Sequence[T]
    """The items on this page."""

    info: CursorInfo
    """Cursor pagination metadata."""
