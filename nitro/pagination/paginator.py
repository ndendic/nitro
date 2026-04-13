"""
Pagination logic for nitro.pagination.

Provides offset-based and cursor-based pagination helpers for both
in-memory sequences and Entity-backed queries.
"""

from __future__ import annotations

import math
from typing import Any, Sequence, Type, TypeVar

from .base import CursorInfo, CursorPage, Page, PageInfo

T = TypeVar("T")


def paginate(items: Sequence[T], page: int = 1, size: int = 20) -> Page[T]:
    """Paginate an in-memory sequence using offset/page logic.

    Args:
        items: The full sequence to paginate.
        page: Page number (1-based). Clamped to 1 if lower.
        size: Number of items per page. Must be >= 1.

    Returns:
        A :class:`Page` containing the requested slice and metadata.

    Example::

        items = list(range(100))
        p = paginate(items, page=3, size=10)
        # p.items == [20, 21, ..., 29]
        # p.info.total == 100, p.info.pages == 10
    """
    if size < 1:
        size = 1
    page = max(1, page)

    total = len(items)
    pages = math.ceil(total / size) if total > 0 else 0

    offset = (page - 1) * size
    slice_ = list(items[offset : offset + size])

    info = PageInfo(
        page=page,
        size=size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )
    return Page[T](items=slice_, info=info)


def paginate_query(
    entity_class: Any,
    page: int = 1,
    size: int = 20,
    **filters: Any,
) -> Page:
    """Paginate an Entity query using Entity.all() or Entity.where().

    Delegates to the entity's repository via:
    - ``entity_class.all()`` when no filters are given.
    - ``entity_class.where(limit=..., offset=...)`` when filters are given.

    For total count, always fetches all IDs (or uses Entity.count() when
    available) to compute accurate pagination metadata.

    Args:
        entity_class: An Entity subclass (must have .all() / .where() / .count()).
        page: Page number (1-based).
        size: Items per page.
        **filters: Keyword filters forwarded to Entity.where().

    Returns:
        A :class:`Page` of entity instances.

    Example::

        page = paginate_query(Product, page=2, size=10)
        page = paginate_query(Product, page=1, size=10, status="active")
    """
    if size < 1:
        size = 1
    page = max(1, page)
    offset = (page - 1) * size

    # Determine total count
    if hasattr(entity_class, "count") and not filters:
        total = entity_class.count()
    elif not filters:
        total = len(entity_class.all())
    else:
        # Count by fetching all filtered — repositories may not expose count+filter
        total = len(entity_class.where(**filters) if hasattr(entity_class, "where") else entity_class.all())

    pages = math.ceil(total / size) if total > 0 else 0

    # Fetch the slice
    if hasattr(entity_class, "where"):
        try:
            if filters:
                # Try passing limit/offset as keyword args to where()
                items = entity_class.where(limit=size, offset=offset, **filters)
            else:
                items = entity_class.where(limit=size, offset=offset)
        except TypeError:
            # Fallback: fetch all then slice
            all_items = entity_class.all() if not filters else entity_class.where(**filters)
            items = all_items[offset : offset + size]
    else:
        all_items = entity_class.all()
        items = all_items[offset : offset + size]

    info = PageInfo(
        page=page,
        size=size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )
    return Page(items=list(items), info=info)


def cursor_paginate(
    items: Sequence[T],
    cursor: str | None = None,
    size: int = 20,
    key: str = "id",
) -> CursorPage[T]:
    """Cursor-based pagination for in-memory sequences.

    Items are assumed to be ordered. The cursor is the string representation
    of the ``key`` attribute (or dict key) of the last-seen item.

    Args:
        items: The full sequence to paginate.
        cursor: Opaque cursor string from a previous response.
                Pass ``None`` to start from the beginning.
        size: Maximum number of items to return.
        key: The attribute or dict key used as the cursor value.

    Returns:
        A :class:`CursorPage` containing the requested slice and metadata.

    Example::

        items = [{"id": i, "name": f"item-{i}"} for i in range(50)]
        page1 = cursor_paginate(items, size=10)
        page2 = cursor_paginate(items, cursor=page1.info.next_cursor, size=10)
    """
    if size < 1:
        size = 1

    def _get_key(item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get(key))
        return str(getattr(item, key, None))

    # Find starting index
    start = 0
    if cursor is not None:
        for idx, item in enumerate(items):
            if _get_key(item) == cursor:
                start = idx + 1
                break

    slice_ = list(items[start : start + size])
    has_more = (start + size) < len(items)

    next_cursor: str | None = None
    if has_more and slice_:
        next_cursor = _get_key(slice_[-1])

    info = CursorInfo(
        cursor=cursor,
        next_cursor=next_cursor,
        has_more=has_more,
        size=size,
    )
    return CursorPage[T](items=slice_, info=info)
