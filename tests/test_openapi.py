"""Tests for nitro.openapi — OpenAPI 3.1 spec generation from Entity classes."""
import pytest
from typing import Optional

from nitro.domain.entities.base_entity import Entity
from nitro.rest.config import RESTConfig
from nitro.openapi.info import OpenAPIInfo
from nitro.openapi.schema import generate_schema, generate_create_schema, generate_update_schema
from nitro.openapi.spec import EntityRegistration, generate_openapi
from nitro.openapi.routes import add_entity, get_registry, clear_registry


# ---------------------------------------------------------------------------
# Test entities
# ---------------------------------------------------------------------------

class Product(Entity, table=True):
    name: str
    price: float = 0.0
    description: str = ""
    in_stock: bool = True
    category: Optional[str] = None


class Order(Entity, table=True):
    customer_name: str
    total: float = 0.0
    status: str = "pending"


# ---------------------------------------------------------------------------
# OpenAPIInfo
# ---------------------------------------------------------------------------

class TestOpenAPIInfo:
    def test_defaults(self):
        info = OpenAPIInfo()
        d = info.to_openapi()
        assert d["title"] == "Nitro API"
        assert d["version"] == "1.0.0"
        assert "description" not in d
        assert "contact" not in d
        assert "license" not in d

    def test_full_info(self):
        info = OpenAPIInfo(
            title="Store API",
            version="2.0.0",
            description="My store",
            contact_name="Dev",
            contact_email="dev@example.com",
            license_name="MIT",
            license_url="https://opensource.org/licenses/MIT",
        )
        d = info.to_openapi()
        assert d["title"] == "Store API"
        assert d["version"] == "2.0.0"
        assert d["description"] == "My store"
        assert d["contact"]["name"] == "Dev"
        assert d["contact"]["email"] == "dev@example.com"
        assert d["license"]["name"] == "MIT"
        assert d["license"]["url"] == "https://opensource.org/licenses/MIT"

    def test_partial_contact(self):
        info = OpenAPIInfo(contact_email="a@b.com")
        d = info.to_openapi()
        assert d["contact"] == {"email": "a@b.com"}

    def test_no_empty_sections(self):
        info = OpenAPIInfo(title="X", version="1")
        d = info.to_openapi()
        assert "contact" not in d
        assert "license" not in d
        assert "termsOfService" not in d


# ---------------------------------------------------------------------------
# Schema generation
# ---------------------------------------------------------------------------

class TestGenerateSchema:
    def test_basic_schema(self):
        schema = generate_schema(Product)
        assert schema["type"] == "object"
        props = schema["properties"]
        assert "id" in props
        assert "name" in props
        assert "price" in props
        assert "in_stock" in props

    def test_id_always_required(self):
        schema = generate_schema(Product)
        assert "id" in schema["required"]

    def test_required_field(self):
        schema = generate_schema(Product)
        assert "name" in schema["required"]

    def test_optional_field_not_required(self):
        schema = generate_schema(Product)
        assert "category" not in schema["required"]

    def test_field_with_default_not_required(self):
        schema = generate_schema(Product)
        assert "price" not in schema["required"]

    def test_field_types(self):
        schema = generate_schema(Product)
        props = schema["properties"]
        assert props["name"]["type"] == "string"
        assert props["price"]["type"] == "number"
        assert props["in_stock"]["type"] == "boolean"

    def test_exclude_fields(self):
        schema = generate_schema(Product, exclude=["description"])
        assert "description" not in schema["properties"]

    def test_readonly_fields(self):
        schema = generate_schema(Product, readonly_fields=["category"])
        assert schema["properties"]["category"].get("readOnly") is True

    def test_id_present(self):
        schema = generate_schema(Product)
        assert "id" in schema["properties"]
        assert schema["properties"]["id"]["type"] == "string"


class TestCreateSchema:
    def test_no_id(self):
        schema = generate_create_schema(Product)
        assert "id" not in schema["properties"]

    def test_skips_readonly(self):
        schema = generate_create_schema(Product, readonly_fields=["category"])
        assert "category" not in schema["properties"]

    def test_required_present(self):
        schema = generate_create_schema(Product)
        assert "name" in schema.get("required", [])

    def test_has_writable_fields(self):
        schema = generate_create_schema(Product)
        assert "name" in schema["properties"]
        assert "price" in schema["properties"]

    def test_no_readonly_marker(self):
        schema = generate_create_schema(Product)
        for prop in schema["properties"].values():
            assert "readOnly" not in prop


class TestUpdateSchema:
    def test_no_id(self):
        schema = generate_update_schema(Product)
        assert "id" not in schema["properties"]

    def test_no_required(self):
        schema = generate_update_schema(Product)
        assert "required" not in schema

    def test_skips_readonly(self):
        schema = generate_update_schema(Product, readonly_fields=["category"])
        assert "category" not in schema["properties"]

    def test_has_writable_fields(self):
        schema = generate_update_schema(Product)
        assert "name" in schema["properties"]
        assert "price" in schema["properties"]


# ---------------------------------------------------------------------------
# Full spec generation
# ---------------------------------------------------------------------------

class TestGenerateOpenAPI:
    def _make_regs(self, *entities, **kwargs):
        return [
            EntityRegistration(entity_class=e, config=kwargs.get("config", RESTConfig()))
            for e in entities
        ]

    def test_openapi_version(self):
        spec = generate_openapi(self._make_regs(Product))
        assert spec["openapi"] == "3.1.0"

    def test_info_section(self):
        spec = generate_openapi(
            self._make_regs(Product),
            info=OpenAPIInfo(title="Test", version="0.1"),
        )
        assert spec["info"]["title"] == "Test"
        assert spec["info"]["version"] == "0.1"

    def test_servers(self):
        spec = generate_openapi(
            self._make_regs(Product),
            servers=[{"url": "http://localhost:8000"}],
        )
        assert spec["servers"] == [{"url": "http://localhost:8000"}]

    def test_no_servers_by_default(self):
        spec = generate_openapi(self._make_regs(Product))
        assert "servers" not in spec

    def test_paths_generated(self):
        spec = generate_openapi(self._make_regs(Product))
        assert "/api/products/" in spec["paths"]
        assert "/api/products/{id}" in spec["paths"]

    def test_all_crud_operations(self):
        spec = generate_openapi(self._make_regs(Product))
        collection = spec["paths"]["/api/products/"]
        item = spec["paths"]["/api/products/{id}"]
        assert "get" in collection  # list
        assert "post" in collection  # create
        assert "get" in item  # get one
        assert "put" in item  # update
        assert "patch" in item  # partial
        assert "delete" in item  # delete

    def test_limited_actions(self):
        cfg = RESTConfig(actions=["list", "get"])
        regs = [EntityRegistration(entity_class=Product, config=cfg)]
        spec = generate_openapi(regs)
        collection = spec["paths"].get("/api/products/", {})
        item = spec["paths"].get("/api/products/{id}", {})
        assert "get" in collection
        assert "post" not in collection
        assert "get" in item
        assert "put" not in item
        assert "delete" not in item

    def test_multiple_entities(self):
        spec = generate_openapi(self._make_regs(Product, Order))
        assert "/api/products/" in spec["paths"]
        assert "/api/orders/" in spec["paths"]

    def test_schemas_generated(self):
        spec = generate_openapi(self._make_regs(Product))
        schemas = spec["components"]["schemas"]
        assert "Product" in schemas
        assert "ProductCreate" in schemas
        assert "ProductUpdate" in schemas

    def test_tags_generated(self):
        spec = generate_openapi(self._make_regs(Product, Order))
        tag_names = [t["name"] for t in spec["tags"]]
        assert "Product" in tag_names
        assert "Order" in tag_names

    def test_operation_ids(self):
        spec = generate_openapi(self._make_regs(Product))
        ops = []
        for path_ops in spec["paths"].values():
            for op in path_ops.values():
                ops.append(op.get("operationId"))
        assert "list_Product" in ops
        assert "create_Product" in ops
        assert "get_Product" in ops
        assert "update_Product" in ops
        assert "patch_Product" in ops
        assert "delete_Product" in ops

    def test_list_has_pagination_params(self):
        spec = generate_openapi(self._make_regs(Product))
        list_op = spec["paths"]["/api/products/"]["get"]
        param_names = [p["name"] for p in list_op["parameters"]]
        assert "page" in param_names
        assert "page_size" in param_names
        assert "sort" in param_names

    def test_list_has_search_param(self):
        spec = generate_openapi(self._make_regs(Product))
        list_op = spec["paths"]["/api/products/"]["get"]
        param_names = [p["name"] for p in list_op["parameters"]]
        assert "q" in param_names

    def test_search_disabled(self):
        cfg = RESTConfig(enable_search=False)
        regs = [EntityRegistration(entity_class=Product, config=cfg)]
        spec = generate_openapi(regs)
        list_op = spec["paths"]["/api/products/"]["get"]
        param_names = [p["name"] for p in list_op["parameters"]]
        assert "q" not in param_names

    def test_custom_url_prefix(self):
        cfg = RESTConfig(url_prefix="/v2/items")
        regs = [EntityRegistration(entity_class=Product, config=cfg)]
        spec = generate_openapi(regs)
        assert "/v2/items/" in spec["paths"]
        assert "/v2/items/{id}" in spec["paths"]

    def test_response_envelope(self):
        spec = generate_openapi(self._make_regs(Product))
        get_resp = spec["paths"]["/api/products/{id}"]["get"]["responses"]["200"]
        schema = get_resp["content"]["application/json"]["schema"]
        assert "success" in schema["properties"]
        assert "data" in schema["properties"]
        assert "meta" in schema["properties"]
        assert "errors" in schema["properties"]

    def test_create_request_body(self):
        spec = generate_openapi(self._make_regs(Product))
        create_op = spec["paths"]["/api/products/"]["post"]
        body = create_op["requestBody"]
        assert body["required"] is True
        ref = body["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/ProductCreate"

    def test_pluralization_products(self):
        spec = generate_openapi(self._make_regs(Product))
        assert "/api/products/" in spec["paths"]

    def test_pluralization_orders(self):
        spec = generate_openapi(self._make_regs(Order))
        assert "/api/orders/" in spec["paths"]

    def test_exclude_fields_propagates(self):
        cfg = RESTConfig(exclude_fields=["description"])
        regs = [EntityRegistration(entity_class=Product, config=cfg)]
        spec = generate_openapi(regs)
        schema = spec["components"]["schemas"]["Product"]
        assert "description" not in schema["properties"]

    def test_readonly_fields_propagates(self):
        cfg = RESTConfig(readonly_fields=["status"])
        regs = [EntityRegistration(entity_class=Order, config=cfg)]
        spec = generate_openapi(regs)
        schema = spec["components"]["schemas"]["Order"]
        assert schema["properties"]["status"].get("readOnly") is True
        create_schema = spec["components"]["schemas"]["OrderCreate"]
        assert "status" not in create_schema["properties"]

    def test_page_size_in_params(self):
        cfg = RESTConfig(page_size=50)
        regs = [EntityRegistration(entity_class=Product, config=cfg)]
        spec = generate_openapi(regs)
        list_op = spec["paths"]["/api/products/"]["get"]
        ps_param = next(p for p in list_op["parameters"] if p["name"] == "page_size")
        assert ps_param["schema"]["default"] == 50

    def test_delete_only(self):
        cfg = RESTConfig(actions=["delete"])
        regs = [EntityRegistration(entity_class=Product, config=cfg)]
        spec = generate_openapi(regs)
        assert "/api/products/" not in spec["paths"]
        item = spec["paths"]["/api/products/{id}"]
        assert "delete" in item
        assert len(item) == 1


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def setup_method(self):
        clear_registry()

    def test_add_and_get(self):
        add_entity(Product)
        regs = get_registry()
        assert len(regs) == 1
        assert regs[0].entity_class is Product

    def test_clear(self):
        add_entity(Product)
        clear_registry()
        assert get_registry() == []

    def test_multiple_entities(self):
        add_entity(Product)
        add_entity(Order, config=RESTConfig(page_size=50))
        regs = get_registry()
        assert len(regs) == 2

    def test_custom_config(self):
        cfg = RESTConfig(actions=["list", "get"])
        add_entity(Product, config=cfg)
        regs = get_registry()
        assert regs[0].config.actions == ["list", "get"]


# ---------------------------------------------------------------------------
# EntityRegistration
# ---------------------------------------------------------------------------

class TestEntityRegistration:
    def test_name(self):
        reg = EntityRegistration(entity_class=Product, config=RESTConfig())
        assert reg.name == "Product"

    def test_resolved_config_auto_prefix(self):
        reg = EntityRegistration(entity_class=Product, config=RESTConfig())
        resolved = reg.resolved_config
        assert resolved.url_prefix == "/api/products"

    def test_resolved_config_custom_prefix(self):
        reg = EntityRegistration(entity_class=Product, config=RESTConfig(url_prefix="/v1/goods"))
        resolved = reg.resolved_config
        assert resolved.url_prefix == "/v1/goods"


# ---------------------------------------------------------------------------
# Pluralization (via RESTConfig.resolve)
# ---------------------------------------------------------------------------

class TestPluralization:
    """Test the _pluralize function via RESTConfig.resolve."""

    def _prefix_for(self, entity_class):
        cfg = RESTConfig().resolve(entity_class)
        return cfg.url_prefix

    def test_regular_plural(self):
        assert self._prefix_for(Product) == "/api/products"

    def test_order_plural(self):
        assert self._prefix_for(Order) == "/api/orders"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_registrations(self):
        spec = generate_openapi([])
        assert spec["openapi"] == "3.1.0"
        assert spec["paths"] == {}
        assert spec["components"]["schemas"] == {}

    def test_spec_is_json_serializable(self):
        import json
        spec = generate_openapi([
            EntityRegistration(entity_class=Product, config=RESTConfig()),
            EntityRegistration(entity_class=Order, config=RESTConfig()),
        ])
        serialized = json.dumps(spec)
        assert isinstance(serialized, str)
        roundtrip = json.loads(serialized)
        assert roundtrip["openapi"] == "3.1.0"

    def test_default_page_size_in_schema(self):
        spec = generate_openapi([EntityRegistration(entity_class=Product, config=RESTConfig())])
        list_op = spec["paths"]["/api/products/"]["get"]
        ps = next(p for p in list_op["parameters"] if p["name"] == "page_size")
        assert ps["schema"]["default"] == 20
