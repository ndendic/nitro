"""
nitro.pagination — Offset and cursor pagination with UI controls.

Provides:
- PageInfo        : Offset-pagination metadata (page, size, total, pages, has_next, has_prev)
- Page            : Generic container for a page of results + PageInfo
- CursorInfo      : Cursor-pagination metadata (cursor, next_cursor, has_more, size)
- CursorPage      : Generic container for a cursor page of results + CursorInfo
- paginate        : Paginate an in-memory sequence by offset/page
- paginate_query  : Paginate an Entity query via the repository
- cursor_paginate : Cursor-based pagination for in-memory sequences
- Paginator       : UI component — renders page-navigation controls (RustyTags + Datastar)
- paginate_request: Sanic helper — extracts page/size from request query string

Quick start (in-memory list)::

    from nitro.pagination import paginate

    items = list(range(100))
    p = paginate(items, page=2, size=10)
    # p.items    → [10, 11, ..., 19]
    # p.info.total  → 100
    # p.info.pages  → 10
    # p.info.has_next → True

Quick start (Entity query)::

    from nitro.pagination import paginate_query
    from myapp.domain import Product

    page = paginate_query(Product, page=1, size=20)
    for product in page.items:
        print(product.name)

Quick start (cursor pagination)::

    from nitro.pagination import cursor_paginate

    items = [{"id": i, "name": f"item-{i}"} for i in range(50)]
    page1 = cursor_paginate(items, size=10)
    page2 = cursor_paginate(items, cursor=page1.info.next_cursor, size=10)

UI component::

    from nitro.pagination.components import Paginator

    nav = Paginator(
        page=2,
        pages=10,
        total=200,
        base_url="/products",
        size=20,
    )

Sanic integration::

    from sanic import Sanic
    from sanic.response import json
    from nitro.pagination import paginate_request

    app = Sanic("MyApp")

    @app.get("/products")
    async def list_products(request):
        result = paginate_request(request, entity_class=Product)
        return json(result.model_dump())
"""

from .base import CursorInfo, CursorPage, Page, PageInfo
from .paginator import cursor_paginate, paginate, paginate_query
from .sanic_integration import paginate_request

__all__ = [
    "PageInfo",
    "Page",
    "CursorInfo",
    "CursorPage",
    "paginate",
    "paginate_query",
    "cursor_paginate",
    "paginate_request",
]
