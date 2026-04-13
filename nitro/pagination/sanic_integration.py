"""
Sanic integration helpers for nitro.pagination.

Provides ``paginate_request`` which extracts pagination parameters from
a Sanic request's query string and delegates to the appropriate paginator.

Example::

    from sanic import Sanic
    from sanic.response import json
    from nitro.pagination import paginate_request

    app = Sanic("MyApp")

    @app.get("/items")
    async def list_items(request):
        result = paginate_request(request, entity_class=Item)
        return json(result.model_dump())
"""

from __future__ import annotations

from typing import Any, Sequence

from .base import Page
from .paginator import paginate, paginate_query


def paginate_request(
    request: Any,
    entity_class: Any = None,
    items: Sequence[Any] | None = None,
    default_size: int = 20,
    max_size: int = 100,
    **filters: Any,
) -> Page:
    """Extract page/size from a Sanic request and paginate.

    Reads ``page`` and ``size`` query parameters, clamps ``size`` to
    ``max_size``, then paginates either an Entity class or an in-memory
    sequence.

    Args:
        request:      A Sanic ``Request`` object.
        entity_class: An Entity subclass to paginate via the repository.
                      Mutually exclusive with ``items``.
        items:        An in-memory sequence to paginate.
                      Mutually exclusive with ``entity_class``.
        default_size: Default page size when ``size`` is absent.
        max_size:     Maximum allowed page size (clamps larger values).
        **filters:    Additional filters forwarded to ``paginate_query``.

    Returns:
        A :class:`~nitro.pagination.base.Page` with the requested slice.

    Raises:
        ValueError: If both ``entity_class`` and ``items`` are provided,
                    or if neither is provided.
    """
    if entity_class is not None and items is not None:
        raise ValueError("Provide either entity_class or items, not both.")
    if entity_class is None and items is None:
        raise ValueError("Provide either entity_class or items.")

    try:
        page = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    try:
        size = int(request.args.get("size", default_size))
    except (ValueError, TypeError):
        size = default_size

    page = max(1, page)
    size = max(1, min(size, max_size))

    if entity_class is not None:
        return paginate_query(entity_class, page=page, size=size, **filters)

    return paginate(items, page=page, size=size)  # type: ignore[arg-type]
