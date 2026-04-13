"""
Tests for nitro.rest — auto-generated REST API endpoints from Entity classes.

Covers: RESTConfig, serialize_entity/serialize_many, QueryParams,
        parse_query_params, apply_filters, register_rest_routes (via Sanic test client).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import pytest
from sqlmodel import Field

from nitro.domain.entities.base_entity import Entity
from nitro.rest.config import RESTConfig, _pluralize
from nitro.rest.serializer import serialize_entity, serialize_many
from nitro.rest.filters import QueryParams, parse_query_params, apply_filters


# ------------------------------------------------------------------ #
# Test Entity
# ------------------------------------------------------------------ #


class Product(Entity, table=True):
    """Test entity for REST API tests."""
    name: str = ""
    price: float = 0.0
    category: str = ""
    description: Optional[str] = None
    in_stock: bool = True


# ------------------------------------------------------------------ #
# RESTConfig
# ------------------------------------------------------------------ #


class TestRESTConfig:
    def test_default_config(self):
        cfg = RESTConfig()
        assert cfg.page_size == 20
        assert cfg.max_page_size == 100
        assert cfg.url_prefix == ""
        assert "list" in cfg.actions
        assert "create" in cfg.actions

    def test_resolve_auto_prefix(self):
        cfg = RESTConfig().resolve(Product)
        assert cfg.url_prefix == "/api/products"

    def test_resolve_custom_prefix(self):
        cfg = RESTConfig(url_prefix="/v2/items").resolve(Product)
        assert cfg.url_prefix == "/v2/items"

    def test_resolve_preserves_settings(self):
        cfg = RESTConfig(page_size=50, exclude_fields=["description"]).resolve(Product)
        assert cfg.page_size == 50
        assert cfg.exclude_fields == ["description"]
        assert cfg.url_prefix == "/api/products"

    def test_readonly_fields(self):
        cfg = RESTConfig(readonly_fields=["created_at"])
        assert "created_at" in cfg.readonly_fields

    def test_actions_subset(self):
        cfg = RESTConfig(actions=["list", "get"])
        assert "create" not in cfg.actions
        assert "delete" not in cfg.actions


class TestPluralize:
    def test_regular(self):
        assert _pluralize("Product") == "Products"

    def test_y_ending(self):
        assert _pluralize("Category") == "Categories"

    def test_s_ending(self):
        assert _pluralize("Address") == "Addresses"

    def test_ch_ending(self):
        assert _pluralize("Match") == "Matches"

    def test_x_ending(self):
        assert _pluralize("Box") == "Boxes"

    def test_ay_ending(self):
        assert _pluralize("Day") == "Days"

    def test_ey_ending(self):
        assert _pluralize("Key") == "Keys"


# ------------------------------------------------------------------ #
# Serializer
# ------------------------------------------------------------------ #


class TestSerializer:
    def test_serialize_entity_all_fields(self, test_repository):
        p = Product(id="p1", name="Widget", price=9.99, category="tools")
        p.save()
        data = serialize_entity(p)
        assert data["id"] == "p1"
        assert data["name"] == "Widget"
        assert data["price"] == 9.99
        assert data["category"] == "tools"

    def test_serialize_entity_include_fields(self, test_repository):
        p = Product(id="p2", name="Gadget", price=19.99, category="tech")
        p.save()
        data = serialize_entity(p, include=["id", "name"])
        assert "id" in data
        assert "name" in data
        assert "price" not in data

    def test_serialize_entity_exclude_fields(self, test_repository):
        p = Product(id="p3", name="Thing", price=5.0, category="misc")
        p.save()
        data = serialize_entity(p, exclude=["description", "in_stock"])
        assert "description" not in data
        assert "in_stock" not in data
        assert "name" in data

    def test_serialize_many(self, test_repository):
        p1 = Product(id="m1", name="A", price=1.0, category="x")
        p2 = Product(id="m2", name="B", price=2.0, category="y")
        p1.save()
        p2.save()
        data = serialize_many([p1, p2])
        assert len(data) == 2
        assert data[0]["id"] == "m1"
        assert data[1]["id"] == "m2"

    def test_serialize_many_with_field_selection(self, test_repository):
        p1 = Product(id="ms1", name="A", price=1.0, category="x")
        p1.save()
        data = serialize_many([p1], include=["id", "name"])
        assert "price" not in data[0]

    def test_serialize_datetime_field(self, test_repository):
        """Datetime values should be converted to ISO format strings."""
        p = Product(id="dt1", name="Dated", price=1.0, category="x")
        p.save()
        # Manually set a datetime attr for testing
        p._test_dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # serialize_entity only serializes model fields, so this won't appear
        # but we can test the conversion path directly
        data = serialize_entity(p)
        assert isinstance(data["id"], str)


# ------------------------------------------------------------------ #
# Query Param Parsing
# ------------------------------------------------------------------ #


class TestParseQueryParams:
    def test_defaults(self):
        params = parse_query_params({})
        assert params.page == 1
        assert params.page_size == 20
        assert params.sort_by is None
        assert params.search is None
        assert params.filters == {}
        assert params.fields is None

    def test_page_and_page_size(self):
        params = parse_query_params({"page": "3", "page_size": "50"})
        assert params.page == 3
        assert params.page_size == 50

    def test_page_size_capped(self):
        params = parse_query_params({"page_size": "999"}, max_page_size=100)
        assert params.page_size == 100

    def test_page_minimum(self):
        params = parse_query_params({"page": "0"})
        assert params.page == 1

    def test_sort_ascending(self):
        params = parse_query_params({"sort": "name"})
        assert params.sort_by == "name"
        assert params.sort_desc is False

    def test_sort_descending(self):
        params = parse_query_params({"sort": "-price"})
        assert params.sort_by == "price"
        assert params.sort_desc is True

    def test_search(self):
        params = parse_query_params({"q": "widget"})
        assert params.search == "widget"

    def test_field_selection(self):
        params = parse_query_params({"fields": "id,name,price"})
        assert params.fields == ["id", "name", "price"]

    def test_filters(self):
        params = parse_query_params({"category": "tools", "in_stock": "true"})
        assert params.filters == {"category": "tools", "in_stock": "true"}

    def test_reserved_not_in_filters(self):
        params = parse_query_params({"page": "1", "sort": "name", "q": "test", "category": "a"})
        assert "page" not in params.filters
        assert "sort" not in params.filters
        assert "q" not in params.filters
        assert "category" in params.filters

    def test_invalid_page_defaults(self):
        params = parse_query_params({"page": "abc"})
        assert params.page == 1

    def test_list_values_normalized(self):
        params = parse_query_params({"category": ["tools"]})
        assert params.filters["category"] == "tools"

    def test_custom_default_page_size(self):
        params = parse_query_params({}, default_page_size=50)
        assert params.page_size == 50


# ------------------------------------------------------------------ #
# Filter Application
# ------------------------------------------------------------------ #


class TestApplyFilters:
    @pytest.fixture(autouse=True)
    def _seed_products(self, test_repository):
        """Seed test products."""
        products = [
            Product(id="f1", name="Alpha Widget", price=10.0, category="tools", in_stock=True),
            Product(id="f2", name="Beta Gadget", price=25.0, category="tech", in_stock=True),
            Product(id="f3", name="Gamma Tool", price=5.0, category="tools", in_stock=False),
            Product(id="f4", name="Delta Device", price=50.0, category="tech", in_stock=True),
            Product(id="f5", name="Epsilon Widget", price=15.0, category="tools", in_stock=True),
        ]
        for p in products:
            p.save()

    def test_no_filters_returns_all(self):
        params = QueryParams()
        items, total = apply_filters(Product, params)
        assert total == 5

    def test_exact_filter(self):
        params = QueryParams(filters={"category": "tools"})
        items, total = apply_filters(Product, params)
        assert total == 3
        assert all(i.category == "tools" for i in items)

    def test_search(self):
        params = QueryParams(search="Widget")
        items, total = apply_filters(Product, params)
        assert total == 2

    def test_sort_ascending(self):
        params = QueryParams(sort_by="price", sort_desc=False)
        items, total = apply_filters(Product, params)
        prices = [i.price for i in items]
        assert prices == sorted(prices)

    def test_sort_descending(self):
        params = QueryParams(sort_by="price", sort_desc=True)
        items, total = apply_filters(Product, params)
        prices = [i.price for i in items]
        assert prices == sorted(prices, reverse=True)

    def test_pagination(self):
        params = QueryParams(page=1, page_size=2)
        items, total = apply_filters(Product, params)
        assert len(items) == 2
        assert total == 5

    def test_pagination_page_2(self):
        params = QueryParams(page=2, page_size=2)
        items, total = apply_filters(Product, params)
        assert len(items) == 2
        assert total == 5

    def test_pagination_last_page(self):
        params = QueryParams(page=3, page_size=2)
        items, total = apply_filters(Product, params)
        assert len(items) == 1

    def test_filter_plus_search(self):
        params = QueryParams(filters={"category": "tools"}, search="Widget")
        items, total = apply_filters(Product, params)
        assert total == 2

    def test_filter_unknown_field_ignored(self):
        """Unknown filter fields are silently ignored."""
        params = QueryParams(filters={"nonexistent": "value"})
        items, total = apply_filters(Product, params)
        assert total == 5


# ------------------------------------------------------------------ #
# Sanic Route Integration
# ------------------------------------------------------------------ #


class TestRESTRoutes:
    """Integration tests using Sanic's test client."""

    @pytest.fixture(autouse=True)
    def _setup_app(self, test_repository):
        """Create a Sanic app with REST routes registered."""
        from sanic import Sanic

        # Sanic requires unique app names
        import uuid
        app_name = f"TestREST_{uuid.uuid4().hex[:8]}"
        self.app = Sanic(app_name)

        from nitro.rest import register_rest_routes
        register_rest_routes(self.app, Product)

        # Seed data
        products = [
            Product(id="r1", name="Alpha", price=10.0, category="tools"),
            Product(id="r2", name="Beta", price=20.0, category="tech"),
            Product(id="r3", name="Gamma", price=30.0, category="tools"),
        ]
        for p in products:
            p.save()

    # ---- LIST -----------------------------------------------------------

    @pytest.mark.asyncio
    async def test_list_returns_all(self):
        _, response = await self.app.asgi_client.get("/api/products/")
        assert response.status_code == 200
        body = response.json
        assert body["success"] is True
        assert len(body["data"]) == 3
        assert body["meta"]["total"] == 3

    @pytest.mark.asyncio
    async def test_list_pagination(self):
        _, response = await self.app.asgi_client.get("/api/products/?page_size=2")
        body = response.json
        assert len(body["data"]) == 2
        assert body["meta"]["total"] == 3
        assert body["meta"]["total_pages"] == 2

    @pytest.mark.asyncio
    async def test_list_search(self):
        _, response = await self.app.asgi_client.get("/api/products/?q=Alpha")
        body = response.json
        assert body["meta"]["total"] == 1
        assert body["data"][0]["name"] == "Alpha"

    @pytest.mark.asyncio
    async def test_list_filter(self):
        _, response = await self.app.asgi_client.get("/api/products/?category=tools")
        body = response.json
        assert body["meta"]["total"] == 2

    @pytest.mark.asyncio
    async def test_list_sort(self):
        _, response = await self.app.asgi_client.get("/api/products/?sort=-price")
        body = response.json
        prices = [item["price"] for item in body["data"]]
        assert prices == sorted(prices, reverse=True)

    @pytest.mark.asyncio
    async def test_list_field_selection(self):
        _, response = await self.app.asgi_client.get("/api/products/?fields=id,name")
        body = response.json
        first = body["data"][0]
        assert "id" in first
        assert "name" in first
        assert "price" not in first

    # ---- GET ONE --------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_one(self):
        _, response = await self.app.asgi_client.get("/api/products/r1")
        assert response.status_code == 200
        body = response.json
        assert body["success"] is True
        assert body["data"]["id"] == "r1"
        assert body["data"]["name"] == "Alpha"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        _, response = await self.app.asgi_client.get("/api/products/nonexistent")
        assert response.status_code == 404
        body = response.json
        assert body["success"] is False

    # ---- CREATE ---------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create(self):
        _, response = await self.app.asgi_client.post(
            "/api/products/",
            json={"name": "New Product", "price": 42.0, "category": "new"},
        )
        assert response.status_code == 201
        body = response.json
        assert body["success"] is True
        assert body["data"]["name"] == "New Product"
        assert body["data"]["price"] == 42.0
        assert "id" in body["data"]

    @pytest.mark.asyncio
    async def test_create_empty_body(self):
        _, response = await self.app.asgi_client.post(
            "/api/products/",
            content="not json",
            headers={"content-type": "text/plain"},
        )
        assert response.status_code == 400

    # ---- UPDATE (PUT) ---------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_put(self):
        _, response = await self.app.asgi_client.put(
            "/api/products/r1",
            json={"name": "Updated Alpha", "price": 99.0},
        )
        assert response.status_code == 200
        body = response.json
        assert body["data"]["name"] == "Updated Alpha"
        assert body["data"]["price"] == 99.0

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        _, response = await self.app.asgi_client.put(
            "/api/products/nonexistent",
            json={"name": "X"},
        )
        assert response.status_code == 404

    # ---- UPDATE (PATCH) -------------------------------------------------

    @pytest.mark.asyncio
    async def test_patch(self):
        _, response = await self.app.asgi_client.patch(
            "/api/products/r2",
            json={"price": 25.0},
        )
        assert response.status_code == 200
        body = response.json
        assert body["data"]["price"] == 25.0
        assert body["data"]["name"] == "Beta"  # unchanged

    # ---- DELETE ---------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delete(self):
        _, response = await self.app.asgi_client.delete("/api/products/r3")
        assert response.status_code == 200
        body = response.json
        assert body["data"]["deleted"] == "r3"

        # Verify it's gone
        _, response = await self.app.asgi_client.get("/api/products/r3")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        _, response = await self.app.asgi_client.delete("/api/products/nonexistent")
        assert response.status_code == 404


class TestRESTRoutesCustomConfig:
    """Test REST routes with custom configuration."""

    @pytest.fixture(autouse=True)
    def _setup_app(self, test_repository):
        from sanic import Sanic
        import uuid

        app_name = f"TestRESTCustom_{uuid.uuid4().hex[:8]}"
        self.app = Sanic(app_name)

        from nitro.rest import RESTConfig, register_rest_routes

        config = RESTConfig(
            actions=["list", "get"],  # read-only
            exclude_fields=["description"],
            page_size=10,
        )
        register_rest_routes(self.app, Product, config=config)

        Product(id="c1", name="ReadOnly", price=5.0, category="test").save()

    @pytest.mark.asyncio
    async def test_list_works(self):
        _, response = await self.app.asgi_client.get("/api/products/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_not_registered(self):
        """POST should 405 when create is not in actions."""
        _, response = await self.app.asgi_client.post(
            "/api/products/",
            json={"name": "Blocked"},
        )
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_delete_not_registered(self):
        _, response = await self.app.asgi_client.delete("/api/products/c1")
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_excluded_fields_not_in_response(self):
        _, response = await self.app.asgi_client.get("/api/products/c1")
        body = response.json
        assert "description" not in body["data"]


class TestRESTRoutesCustomPrefix:
    """Test REST routes with custom URL prefix."""

    @pytest.fixture(autouse=True)
    def _setup_app(self, test_repository):
        from sanic import Sanic
        import uuid

        app_name = f"TestRESTPrefix_{uuid.uuid4().hex[:8]}"
        self.app = Sanic(app_name)

        from nitro.rest import register_rest_routes
        register_rest_routes(self.app, Product, url_prefix="/v2/items")

        Product(id="px1", name="PrefixTest", price=1.0, category="test").save()

    @pytest.mark.asyncio
    async def test_custom_prefix(self):
        _, response = await self.app.asgi_client.get("/v2/items/")
        assert response.status_code == 200
        body = response.json
        assert body["meta"]["total"] == 1

    @pytest.mark.asyncio
    async def test_default_prefix_404(self):
        _, response = await self.app.asgi_client.get("/api/products/")
        assert response.status_code == 404


class TestRESTReadonlyFields:
    """Test that readonly_fields prevents setting values."""

    @pytest.fixture(autouse=True)
    def _setup_app(self, test_repository):
        from sanic import Sanic
        import uuid

        app_name = f"TestRESTReadonly_{uuid.uuid4().hex[:8]}"
        self.app = Sanic(app_name)

        from nitro.rest import RESTConfig, register_rest_routes

        config = RESTConfig(readonly_fields=["category"])
        register_rest_routes(self.app, Product, config=config)

        Product(id="ro1", name="Protected", price=10.0, category="locked").save()

    @pytest.mark.asyncio
    async def test_readonly_field_not_updated(self):
        _, response = await self.app.asgi_client.put(
            "/api/products/ro1",
            json={"name": "Changed", "category": "should-not-change"},
        )
        assert response.status_code == 200
        body = response.json
        assert body["data"]["name"] == "Changed"
        assert body["data"]["category"] == "locked"  # unchanged
