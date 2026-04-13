"""
Comprehensive tests for nitro.pagination module.

Covers:
- paginate()         — offset/page pagination of in-memory sequences
- cursor_paginate()  — cursor-based pagination of in-memory sequences
- paginate_query()   — Entity-backed pagination via the repository
- Paginator()        — UI component HTML output
- paginate_request() — Sanic request helper
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from nitro.pagination import (
    CursorInfo,
    CursorPage,
    Page,
    PageInfo,
    cursor_paginate,
    paginate,
    paginate_query,
    paginate_request,
)
from nitro.pagination.components import Paginator


# ── Helpers ──────────────────────────────────────────────────────────


def make_items(n: int) -> list[int]:
    """Return [0, 1, ..., n-1]."""
    return list(range(n))


def make_dicts(n: int, key: str = "id") -> list[dict]:
    """Return list of dicts with the given key."""
    return [{key: i, "name": f"item-{i}"} for i in range(n)]


# ══════════════════════════════════════════════════════════════════════
# paginate() — offset/page pagination
# ══════════════════════════════════════════════════════════════════════


class TestPaginateBasic:
    def test_page1_returns_first_slice(self):
        items = make_items(50)
        p = paginate(items, page=1, size=10)

        assert isinstance(p, Page)
        assert list(p.items) == list(range(10))
        assert p.info.page == 1
        assert p.info.size == 10
        assert p.info.total == 50
        assert p.info.pages == 5
        assert p.info.has_prev is False
        assert p.info.has_next is True

    def test_middle_page(self):
        items = make_items(50)
        p = paginate(items, page=3, size=10)

        assert list(p.items) == list(range(20, 30))
        assert p.info.has_prev is True
        assert p.info.has_next is True
        assert p.info.page == 3

    def test_last_page_partial(self):
        """Last page has fewer items than size."""
        items = make_items(25)
        p = paginate(items, page=3, size=10)

        assert list(p.items) == list(range(20, 25))
        assert len(p.items) == 5
        assert p.info.has_next is False
        assert p.info.has_prev is True
        assert p.info.pages == 3

    def test_empty_list(self):
        p = paginate([], page=1, size=10)

        assert list(p.items) == []
        assert p.info.total == 0
        assert p.info.pages == 0
        assert p.info.has_next is False
        assert p.info.has_prev is False

    def test_single_item(self):
        p = paginate([42], page=1, size=10)

        assert list(p.items) == [42]
        assert p.info.total == 1
        assert p.info.pages == 1
        assert p.info.has_next is False
        assert p.info.has_prev is False

    def test_out_of_range_page_returns_empty(self):
        """Requesting a page beyond total returns empty items but correct info."""
        items = make_items(10)
        p = paginate(items, page=99, size=10)

        assert list(p.items) == []
        assert p.info.total == 10
        assert p.info.pages == 1

    def test_page_clamped_to_1_when_zero(self):
        items = make_items(10)
        p = paginate(items, page=0, size=5)

        assert p.info.page == 1
        assert list(p.items) == [0, 1, 2, 3, 4]

    def test_page_clamped_to_1_when_negative(self):
        items = make_items(10)
        p = paginate(items, page=-5, size=5)

        assert p.info.page == 1


class TestPageInfoCalculations:
    def test_has_next_false_on_last_page(self):
        items = make_items(20)
        p = paginate(items, page=2, size=10)
        assert p.info.has_next is False

    def test_has_prev_false_on_first_page(self):
        items = make_items(20)
        p = paginate(items, page=1, size=10)
        assert p.info.has_prev is False

    def test_pages_rounds_up(self):
        items = make_items(21)
        p = paginate(items, page=1, size=10)
        assert p.info.pages == 3

    def test_exact_division(self):
        items = make_items(20)
        p = paginate(items, page=1, size=10)
        assert p.info.pages == 2

    def test_single_page(self):
        items = make_items(5)
        p = paginate(items, page=1, size=10)
        assert p.info.pages == 1
        assert p.info.has_next is False
        assert p.info.has_prev is False

    def test_pageinfo_direct_construction(self):
        info = PageInfo(page=2, size=10, total=50, pages=5, has_next=True, has_prev=True)
        assert info.pages == 5
        assert info.has_next is True
        assert info.has_prev is True

    def test_pageinfo_auto_derives_fields(self):
        """PageInfo auto-computes pages/has_next/has_prev when omitted."""
        info = PageInfo(page=2, size=10, total=50)
        assert info.pages == 5
        assert info.has_next is True
        assert info.has_prev is True


# ══════════════════════════════════════════════════════════════════════
# cursor_paginate() — cursor-based pagination
# ══════════════════════════════════════════════════════════════════════


class TestCursorPaginateBasic:
    def test_first_page_no_cursor(self):
        items = make_dicts(30)
        cp = cursor_paginate(items, cursor=None, size=10)

        assert isinstance(cp, CursorPage)
        assert isinstance(cp.info, CursorInfo)
        assert len(cp.items) == 10
        assert cp.items[0]["id"] == 0
        assert cp.items[-1]["id"] == 9
        assert cp.info.has_more is True
        assert cp.info.cursor is None
        assert cp.info.next_cursor == "9"

    def test_continue_from_cursor(self):
        items = make_dicts(30)
        page1 = cursor_paginate(items, cursor=None, size=10)
        page2 = cursor_paginate(items, cursor=page1.info.next_cursor, size=10)

        assert len(page2.items) == 10
        assert page2.items[0]["id"] == 10
        assert page2.items[-1]["id"] == 19
        assert page2.info.has_more is True

    def test_last_page_no_more(self):
        items = make_dicts(25)
        page1 = cursor_paginate(items, cursor=None, size=10)
        page2 = cursor_paginate(items, cursor=page1.info.next_cursor, size=10)
        page3 = cursor_paginate(items, cursor=page2.info.next_cursor, size=10)

        assert len(page3.items) == 5
        assert page3.info.has_more is False
        assert page3.info.next_cursor is None

    def test_empty_sequence(self):
        cp = cursor_paginate([], cursor=None, size=10)

        assert list(cp.items) == []
        assert cp.info.has_more is False
        assert cp.info.next_cursor is None

    def test_cursor_on_objects_with_id(self):
        """Works with objects that have an .id attribute."""

        class Item:
            def __init__(self, id_: int):
                self.id = id_

        items = [Item(i) for i in range(20)]
        page1 = cursor_paginate(items, cursor=None, size=5, key="id")
        assert page1.info.next_cursor == "4"
        assert page1.info.has_more is True

        page2 = cursor_paginate(items, cursor=page1.info.next_cursor, size=5, key="id")
        assert page2.items[0].id == 5


# ══════════════════════════════════════════════════════════════════════
# paginate_query() — Entity-backed pagination
# ══════════════════════════════════════════════════════════════════════


class TestPaginateQueryEntity:
    """paginate_query() with a mock entity class."""

    def _make_entity(self, n: int, has_count: bool = True):
        """Build a minimal mock entity class returning n items."""
        all_items = list(range(n))

        entity = MagicMock()
        entity.all.return_value = all_items

        if has_count:
            entity.count.return_value = n

        def _where(limit=None, offset=None, **kwargs):
            subset = all_items
            if offset is not None:
                subset = subset[offset:]
            if limit is not None:
                subset = subset[:limit]
            return subset

        entity.where.side_effect = _where
        return entity

    def test_paginate_first_page(self):
        entity = self._make_entity(50)
        p = paginate_query(entity, page=1, size=10)

        assert list(p.items) == list(range(10))
        assert p.info.total == 50
        assert p.info.pages == 5
        assert p.info.has_next is True
        assert p.info.has_prev is False

    def test_paginate_second_page(self):
        entity = self._make_entity(50)
        p = paginate_query(entity, page=2, size=10)

        assert list(p.items) == list(range(10, 20))
        assert p.info.page == 2
        assert p.info.has_prev is True

    def test_paginate_last_page(self):
        entity = self._make_entity(25)
        p = paginate_query(entity, page=3, size=10)

        assert list(p.items) == list(range(20, 25))
        assert p.info.has_next is False


# ══════════════════════════════════════════════════════════════════════
# Paginator() — UI component
# ══════════════════════════════════════════════════════════════════════


class TestPaginatorComponent:
    def test_renders_html_string(self):
        nav = Paginator(page=1, pages=5, total=100, base_url="/items")
        html = str(nav)

        assert "<nav" in html
        assert "Page 1 of 5" in html

    def test_prev_disabled_on_first_page(self):
        nav = Paginator(page=1, pages=5, total=100, base_url="/items")
        html = str(nav)

        # First page → prev button has disabled attribute
        assert "disabled" in html

    def test_next_disabled_on_last_page(self):
        nav = Paginator(page=5, pages=5, total=100, base_url="/items")
        html = str(nav)

        assert "disabled" in html

    def test_page_url_in_buttons(self):
        nav = Paginator(page=2, pages=5, total=100, base_url="/items", size=20)
        html = str(nav)

        # Navigation buttons should contain the base_url
        assert "/items" in html
        assert "page=" in html

    def test_shows_total_in_label(self):
        nav = Paginator(page=1, pages=3, total=25, base_url="/x")
        html = str(nav)

        assert "25" in html

    def test_single_page_both_buttons_disabled(self):
        nav = Paginator(page=1, pages=1, total=5, base_url="/items")
        html = str(nav)

        # Both prev and next are disabled
        assert "disabled" in html

    def test_ellipsis_rendered_for_large_page_count(self):
        nav = Paginator(page=5, pages=20, total=400, base_url="/x")
        html = str(nav)

        assert "..." in html

    def test_cls_forwarded(self):
        nav = Paginator(page=1, pages=2, total=20, base_url="/x", cls="my-custom-class")
        html = str(nav)

        assert "my-custom-class" in html

    def test_datastar_action_in_buttons(self):
        nav = Paginator(page=2, pages=5, total=100, base_url="/items")
        html = str(nav)

        assert "@get(" in html


# ══════════════════════════════════════════════════════════════════════
# paginate_request() — Sanic helper
# ══════════════════════════════════════════════════════════════════════


class TestPaginateRequest:
    def _mock_request(self, page: int | None = None, size: int | None = None) -> MagicMock:
        """Build a minimal mock Sanic request."""
        request = MagicMock()
        args = {}
        if page is not None:
            args["page"] = str(page)
        if size is not None:
            args["size"] = str(size)
        request.args.get.side_effect = lambda key, default=None: args.get(key, default)
        return request

    def test_reads_page_and_size_from_args(self):
        request = self._mock_request(page=2, size=5)
        items = make_items(50)

        p = paginate_request(request, items=items)

        assert p.info.page == 2
        assert p.info.size == 5
        assert list(p.items) == list(range(5, 10))

    def test_defaults_when_args_absent(self):
        request = self._mock_request()
        items = make_items(50)

        p = paginate_request(request, items=items, default_size=20)

        assert p.info.page == 1
        assert p.info.size == 20

    def test_max_size_clamping(self):
        request = self._mock_request(size=9999)
        items = make_items(100)

        p = paginate_request(request, items=items, max_size=50)

        assert p.info.size == 50

    def test_entity_class_path(self):
        request = self._mock_request(page=1, size=10)

        all_items = list(range(30))
        entity = MagicMock()
        entity.count.return_value = 30

        def _where(limit=None, offset=None, **kwargs):
            subset = all_items
            if offset:
                subset = subset[offset:]
            if limit:
                subset = subset[:limit]
            return subset

        entity.where.side_effect = _where

        p = paginate_request(request, entity_class=entity)

        assert p.info.total == 30
        assert len(p.items) == 10

    def test_raises_when_both_provided(self):
        request = self._mock_request()
        entity = MagicMock()
        items = make_items(10)

        with pytest.raises(ValueError, match="not both"):
            paginate_request(request, entity_class=entity, items=items)

    def test_raises_when_neither_provided(self):
        request = self._mock_request()

        with pytest.raises(ValueError, match="Provide either"):
            paginate_request(request)

    def test_invalid_page_arg_defaults_to_1(self):
        request = MagicMock()
        request.args.get.side_effect = lambda key, default=None: (
            "not-a-number" if key == "page" else default
        )
        items = make_items(20)

        p = paginate_request(request, items=items)

        assert p.info.page == 1

    def test_page_clamped_to_1_when_zero(self):
        request = self._mock_request(page=0)
        items = make_items(20)

        p = paginate_request(request, items=items)

        assert p.info.page == 1
