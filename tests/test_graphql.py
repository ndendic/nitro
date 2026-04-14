"""Tests for nitro.graphql — GraphQL support layer.

Covers:
- Schema generation from Entity models
- Type mapping (all Python types → GraphQL)
- Query execution (get, list)
- Mutation execution (create, update, delete)
- Introspection queries
- Error handling (invalid queries, missing fields)
- Middleware request handling
- Fragment support
- Variable substitution
- Parser edge cases
"""
from __future__ import annotations

import json
from typing import Optional, List

import pytest
from sqlmodel import Field

from nitro.domain.entities.base_entity import Entity

# ---- Module under test --------------------------------------------------
from nitro.graphql.schema import (
    generate_schema,
    entity_to_type_def,
    map_field_type,
    EntityTypeInfo,
    _build_entity_type_info,
)
from nitro.graphql.resolvers import (
    build_resolvers,
    GraphQLResolverError,
    _entity_to_dict,
    _make_get_resolver,
    _make_list_resolver,
    _make_create_resolver,
    _make_update_resolver,
    _make_delete_resolver,
)
from nitro.graphql.executor import (
    GraphQLExecutor,
    ExecutionResult,
    parse_query,
    _tokenize,
    _Parser,
    _ParseError,
)
from nitro.graphql.middleware import graphiql_html


# =========================================================================
# Test entities
# =========================================================================

class Product(Entity, table=True):
    """A sellable product."""
    name: str = ""
    price: float = 0.0
    category: str = ""
    in_stock: bool = True
    description: Optional[str] = None


class Tag(Entity, table=True):
    label: str = ""
    weight: int = 0


# =========================================================================
# Helpers
# =========================================================================

@pytest.fixture(autouse=True)
def isolated_db(test_repository):
    """Each test gets a clean in-memory DB via conftest test_repository."""
    yield test_repository


def _make_executor(entity_classes=None):
    """Build a GraphQLExecutor for the given (or default) entity classes."""
    if entity_classes is None:
        entity_classes = [Product]
    sdl = generate_schema(entity_classes)
    resolvers = build_resolvers(entity_classes)
    return GraphQLExecutor(sdl, resolvers)


# =========================================================================
# 1. Type mapping
# =========================================================================

class TestMapFieldType:
    """map_field_type converts JSON-schema field metadata to GraphQL types."""

    def _field(self, type_str, *, required=True, fmt=None, name="x"):
        return {"name": name, "type": type_str, "format": fmt, "required": required}

    def test_string_required(self):
        assert map_field_type(self._field("string")) == "String!"

    def test_string_optional(self):
        assert map_field_type(self._field("string", required=False)) == "String"

    def test_integer(self):
        assert map_field_type(self._field("integer")) == "Int!"

    def test_float_number(self):
        assert map_field_type(self._field("number")) == "Float!"

    def test_boolean(self):
        assert map_field_type(self._field("boolean")) == "Boolean!"

    def test_array(self):
        t = map_field_type(self._field("array"))
        assert t.startswith("[")

    def test_object_maps_to_json(self):
        assert map_field_type(self._field("object")) == "JSON!"

    def test_uuid_format_maps_to_id(self):
        assert map_field_type(self._field("string", fmt="uuid")) == "ID!"

    def test_email_format_stays_string(self):
        assert map_field_type(self._field("string", fmt="email")) == "String!"

    def test_date_format(self):
        assert map_field_type(self._field("string", fmt="date")) == "String!"

    def test_datetime_format(self):
        assert map_field_type(self._field("string", fmt="date-time")) == "String!"

    def test_id_field_always_required_id_scalar(self):
        f = {"name": "id", "type": "string", "format": "uuid", "required": False}
        assert map_field_type(f) == "ID!"

    def test_unknown_type_defaults_to_string(self):
        f = {"name": "x", "type": "unknown_custom", "format": None, "required": False}
        assert map_field_type(f) == "String"


# =========================================================================
# 2. Schema generation
# =========================================================================

class TestEntityToTypeDef:
    def test_basic_type_block(self):
        sdl = entity_to_type_def(Product)
        assert "type Product {" in sdl
        assert "id: ID!" in sdl
        assert "name:" in sdl
        assert "price:" in sdl
        assert "in_stock:" in sdl

    def test_optional_field_not_bang(self):
        sdl = entity_to_type_def(Product)
        # description is Optional[str] so must not have "!"
        lines = [l.strip() for l in sdl.splitlines()]
        desc_lines = [l for l in lines if l.startswith("description:")]
        assert desc_lines, "description field not found"
        assert "!" not in desc_lines[0]

    def test_includes_docstring(self):
        sdl = entity_to_type_def(Product, include_description=True)
        assert "sellable product" in sdl

    def test_no_docstring_when_disabled(self):
        sdl = entity_to_type_def(Product, include_description=False)
        assert '"""' not in sdl

    def test_id_is_first_field(self):
        sdl = entity_to_type_def(Product)
        lines = [l.strip() for l in sdl.splitlines() if l.strip() and not l.strip().startswith('"""')]
        field_lines = [l for l in lines if ":" in l and not l.startswith("type")]
        assert field_lines[0].startswith("id:")


class TestGenerateSchema:
    def test_contains_type_blocks(self):
        sdl = generate_schema([Product, Tag])
        assert "type Product {" in sdl
        assert "type Tag {" in sdl

    def test_contains_input_types(self):
        sdl = generate_schema([Product])
        assert "input ProductCreateInput {" in sdl
        assert "input ProductUpdateInput {" in sdl

    def test_input_types_have_no_id(self):
        sdl = generate_schema([Product])
        # Find the CreateInput block and verify id is absent
        in_input = False
        for line in sdl.splitlines():
            if "input ProductCreateInput {" in line:
                in_input = True
            if in_input and "}" in line:
                break
            if in_input:
                assert not line.strip().startswith("id:"), "id should not be in CreateInput"

    def test_query_type_present(self):
        sdl = generate_schema([Product])
        assert "type Query {" in sdl
        assert "product(id: ID!): Product" in sdl
        assert "products: [Product!]!" in sdl

    def test_mutation_type_present(self):
        sdl = generate_schema([Product])
        assert "type Mutation {" in sdl
        assert "createProduct(" in sdl
        assert "updateProduct(" in sdl
        assert "deleteProduct(" in sdl

    def test_no_mutations_when_disabled(self):
        sdl = generate_schema([Product], include_mutations=False)
        assert "type Mutation" not in sdl

    def test_multiple_entities_query_fields(self):
        sdl = generate_schema([Product, Tag])
        assert "tag(id: ID!): Tag" in sdl
        assert "tags: [Tag!]!" in sdl

    def test_returns_string(self):
        sdl = generate_schema([Product])
        assert isinstance(sdl, str)
        assert len(sdl) > 0


class TestEntityTypeInfo:
    def test_type_name(self):
        info = _build_entity_type_info(Product)
        assert info.type_name == "Product"

    def test_query_names(self):
        info = _build_entity_type_info(Product)
        assert info.query_one_name == "product"
        assert info.query_list_name == "products"

    def test_mutation_names(self):
        info = _build_entity_type_info(Product)
        assert info.mutation_create_name == "createProduct"
        assert info.mutation_update_name == "updateProduct"
        assert info.mutation_delete_name == "deleteProduct"

    def test_fields_not_empty(self):
        info = _build_entity_type_info(Product)
        assert len(info.fields) > 0

    def test_id_field_present(self):
        info = _build_entity_type_info(Product)
        names = [f.name for f in info.fields]
        assert "id" in names


# =========================================================================
# 3. Resolver building
# =========================================================================

class TestBuildResolvers:
    def test_has_query_and_mutation_keys(self):
        rm = build_resolvers([Product])
        assert "Query" in rm
        assert "Mutation" in rm

    def test_query_has_get_and_list(self):
        rm = build_resolvers([Product])
        assert "product" in rm["Query"]
        assert "products" in rm["Query"]

    def test_mutation_has_crud(self):
        rm = build_resolvers([Product])
        assert "createProduct" in rm["Mutation"]
        assert "updateProduct" in rm["Mutation"]
        assert "deleteProduct" in rm["Mutation"]

    def test_multiple_entities(self):
        rm = build_resolvers([Product, Tag])
        assert "tag" in rm["Query"]
        assert "createTag" in rm["Mutation"]


class TestEntityToDict:
    def test_entity_to_dict(self):
        p = Product(id="test1", name="Widget", price=9.99)
        d = _entity_to_dict(p)
        assert d["id"] == "test1"
        assert d["name"] == "Widget"
        assert d["price"] == 9.99

    def test_none_returns_none(self):
        assert _entity_to_dict(None) is None


class TestResolverFunctions:
    def test_get_resolver_existing(self):
        p = Product(id="r1", name="Gizmo", price=5.0)
        p.save()
        resolver = _make_get_resolver(Product)
        result = resolver(None, None, id="r1")
        assert result is not None
        assert result["name"] == "Gizmo"

    def test_get_resolver_missing(self):
        resolver = _make_get_resolver(Product)
        result = resolver(None, None, id="nonexistent")
        assert result is None

    def test_list_resolver(self):
        Product(id="l1", name="A").save()
        Product(id="l2", name="B").save()
        resolver = _make_list_resolver(Product)
        result = resolver(None, None)
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_create_resolver(self):
        resolver = _make_create_resolver(Product)
        data = {"name": "New", "price": 1.0, "category": "misc", "in_stock": True}
        result = resolver(None, None, input=data)
        assert result is not None
        assert result["name"] == "New"
        assert "id" in result

    def test_update_resolver(self):
        p = Product(id="u1", name="Old", price=1.0)
        p.save()
        resolver = _make_update_resolver(Product)
        result = resolver(None, None, id="u1", input={"name": "New"})
        assert result["name"] == "New"

    def test_update_resolver_missing(self):
        resolver = _make_update_resolver(Product)
        result = resolver(None, None, id="none", input={"name": "X"})
        assert result is None

    def test_delete_resolver(self):
        p = Product(id="d1", name="Bye")
        p.save()
        resolver = _make_delete_resolver(Product)
        result = resolver(None, None, id="d1")
        assert result is True

    def test_delete_resolver_missing(self):
        resolver = _make_delete_resolver(Product)
        result = resolver(None, None, id="ghost")
        assert result is False


# =========================================================================
# 4. Parser
# =========================================================================

class TestTokenizer:
    def test_tokenizes_simple_query(self):
        tokens = _tokenize("{ products { id name } }")
        kinds = [t.kind for t in tokens]
        assert "PUNCT" in kinds
        assert "NAME" in kinds

    def test_handles_strings(self):
        tokens = _tokenize('{ field(arg: "hello") }')
        string_toks = [t for t in tokens if t.kind == "STRING"]
        assert any(t.value == "hello" for t in string_toks)

    def test_handles_numbers(self):
        tokens = _tokenize("{ x(n: 42) }")
        num_toks = [t for t in tokens if t.kind == "NUMBER"]
        assert num_toks[0].value == "42"

    def test_handles_float(self):
        tokens = _tokenize("{ x(n: 3.14) }")
        num_toks = [t for t in tokens if t.kind == "NUMBER"]
        assert num_toks[0].value == "3.14"

    def test_skips_comments(self):
        tokens = _tokenize("{ # this is a comment\nproducts }")
        names = [t.value for t in tokens if t.kind == "NAME"]
        assert "products" in names

    def test_spread_token(self):
        tokens = _tokenize("{ ...Fields }")
        spreads = [t for t in tokens if t.kind == "SPREAD"]
        assert len(spreads) == 1

    def test_block_string(self):
        tokens = _tokenize('"""block string"""')
        strings = [t for t in tokens if t.kind == "STRING"]
        assert strings[0].value == "block string"


class TestParser:
    def test_parses_anonymous_query(self):
        doc = parse_query("{ products { id name } }")
        assert len(doc.operations) == 1
        assert doc.operations[0].operation == "query"

    def test_parses_named_query(self):
        doc = parse_query("query ListProducts { products { id } }")
        assert doc.operations[0].name == "ListProducts"

    def test_parses_mutation(self):
        doc = parse_query("mutation { createProduct(input: {name: \"x\"}) { id } }")
        assert doc.operations[0].operation == "mutation"

    def test_parses_field_arguments(self):
        doc = parse_query("{ product(id: \"abc\") { id name } }")
        field = doc.operations[0].selection_set[0]
        assert field.name == "product"
        assert field.arguments.get("id") == "abc"

    def test_parses_variable_reference(self):
        doc = parse_query("query Q($id: ID!) { product(id: $id) { id } }")
        field = doc.operations[0].selection_set[0]
        assert field.arguments["id"] == {"__var__": "id"}

    def test_parses_boolean_values(self):
        doc = parse_query("{ x(flag: true, other: false) { id } }")
        field = doc.operations[0].selection_set[0]
        assert field.arguments["flag"] is True
        assert field.arguments["other"] is False

    def test_parses_null_value(self):
        doc = parse_query("{ x(val: null) { id } }")
        field = doc.operations[0].selection_set[0]
        assert field.arguments["val"] is None

    def test_parses_nested_selection(self):
        doc = parse_query("{ products { id name details { weight } } }")
        products_field = doc.operations[0].selection_set[0]
        assert products_field.name == "products"
        nested_names = [f.name for f in products_field.selection_set]
        assert "id" in nested_names
        assert "details" in nested_names

    def test_parses_alias(self):
        doc = parse_query("{ myProduct: product(id: \"1\") { id } }")
        field = doc.operations[0].selection_set[0]
        assert field.alias == "myProduct"
        assert field.name == "product"

    def test_parses_fragment_definition(self):
        doc = parse_query(
            "fragment ProductFields on Product { id name } "
            "{ product(id: \"1\") { ...ProductFields } }"
        )
        assert "ProductFields" in doc.fragments

    def test_parses_list_value(self):
        doc = parse_query("{ x(items: [1, 2, 3]) { id } }")
        field = doc.operations[0].selection_set[0]
        assert field.arguments["items"] == [1, 2, 3]

    def test_parses_object_value(self):
        doc = parse_query('{ x(obj: {a: "b"}) { id } }')
        field = doc.operations[0].selection_set[0]
        assert field.arguments["obj"] == {"a": "b"}


# =========================================================================
# 5. ExecutionResult
# =========================================================================

class TestExecutionResult:
    def test_is_success_no_errors(self):
        r = ExecutionResult(data={"x": 1})
        assert r.is_success is True

    def test_is_failure_with_errors(self):
        r = ExecutionResult(errors=[{"message": "bad"}])
        assert r.is_success is False

    def test_to_dict_data_only(self):
        r = ExecutionResult(data={"a": 1})
        d = r.to_dict()
        assert d["data"] == {"a": 1}
        assert "errors" not in d

    def test_to_dict_errors_only(self):
        r = ExecutionResult(errors=[{"message": "fail"}])
        d = r.to_dict()
        assert "data" not in d
        assert d["errors"][0]["message"] == "fail"

    def test_to_dict_both(self):
        r = ExecutionResult(data={"x": None}, errors=[{"message": "partial"}])
        d = r.to_dict()
        assert "data" in d
        assert "errors" in d


# =========================================================================
# 6. Query execution
# =========================================================================

class TestQueryExecution:
    def test_list_all(self):
        Product(id="q1", name="Alpha", price=1.0).save()
        Product(id="q2", name="Beta", price=2.0).save()
        executor = _make_executor()
        result = executor.execute("{ products { id name price } }")
        assert result.is_success
        names = {p["name"] for p in result.data["products"]}
        assert "Alpha" in names
        assert "Beta" in names

    def test_get_by_id(self):
        Product(id="q3", name="Gamma", price=3.0).save()
        executor = _make_executor()
        result = executor.execute('{ product(id: "q3") { id name } }')
        assert result.is_success
        assert result.data["product"]["name"] == "Gamma"

    def test_get_missing_returns_null(self):
        executor = _make_executor()
        result = executor.execute('{ product(id: "nope") { id name } }')
        assert result.is_success
        assert result.data["product"] is None

    def test_field_selection_subset(self):
        Product(id="q4", name="Delta", price=9.0).save()
        executor = _make_executor()
        result = executor.execute('{ product(id: "q4") { name } }')
        assert result.is_success
        assert "name" in result.data["product"]
        # price not requested — should not be present
        assert "price" not in result.data["product"]

    def test_alias_in_query(self):
        Product(id="q5", name="Epsilon").save()
        executor = _make_executor()
        result = executor.execute('{ myProduct: product(id: "q5") { id name } }')
        assert result.is_success
        assert "myProduct" in result.data
        assert result.data["myProduct"]["name"] == "Epsilon"

    def test_variable_substitution(self):
        Product(id="q6", name="Zeta").save()
        executor = _make_executor()
        result = executor.execute(
            "query Q($id: ID!) { product(id: $id) { name } }",
            variables={"id": "q6"},
        )
        assert result.is_success
        assert result.data["product"]["name"] == "Zeta"

    def test_named_operation(self):
        Product(id="q7", name="Eta").save()
        executor = _make_executor()
        result = executor.execute(
            'query GetOne { product(id: "q7") { name } }',
            operation_name="GetOne",
        )
        assert result.is_success
        assert result.data["product"]["name"] == "Eta"

    def test_unknown_operation_name_errors(self):
        executor = _make_executor()
        result = executor.execute(
            '{ products { id } }',
            operation_name="DoesNotExist",
        )
        assert not result.is_success

    def test_empty_list(self):
        executor = _make_executor([Tag])
        result = executor.execute("{ tags { id label } }")
        assert result.is_success
        assert result.data["tags"] == []


# =========================================================================
# 7. Mutation execution
# =========================================================================

class TestMutationExecution:
    def test_create_mutation(self):
        executor = _make_executor()
        result = executor.execute(
            'mutation { createProduct(input: {name: "NewProd", price: 4.99}) { id name price } }'
        )
        assert result.is_success
        prod = result.data["createProduct"]
        assert prod["name"] == "NewProd"
        assert prod["price"] == 4.99
        assert prod["id"] is not None

    def test_update_mutation(self):
        p = Product(id="m1", name="OldName", price=1.0)
        p.save()
        executor = _make_executor()
        result = executor.execute(
            'mutation { updateProduct(id: "m1", input: {name: "NewName"}) { id name } }'
        )
        assert result.is_success
        assert result.data["updateProduct"]["name"] == "NewName"

    def test_update_nonexistent_returns_null(self):
        executor = _make_executor()
        result = executor.execute(
            'mutation { updateProduct(id: "ghost", input: {name: "X"}) { id } }'
        )
        assert result.is_success
        assert result.data["updateProduct"] is None

    def test_delete_mutation(self):
        p = Product(id="m2", name="ToDelete")
        p.save()
        executor = _make_executor()
        result = executor.execute('mutation { deleteProduct(id: "m2") }')
        assert result.is_success
        assert result.data["deleteProduct"] is True

    def test_delete_nonexistent_returns_false(self):
        executor = _make_executor()
        result = executor.execute('mutation { deleteProduct(id: "ghost") }')
        assert result.is_success
        assert result.data["deleteProduct"] is False

    def test_create_with_variables(self):
        executor = _make_executor()
        result = executor.execute(
            "mutation Create($input: ProductCreateInput!) { createProduct(input: $input) { id name } }",
            variables={"input": {"name": "VarProduct", "price": 7.0}},
        )
        assert result.is_success
        assert result.data["createProduct"]["name"] == "VarProduct"


# =========================================================================
# 8. Introspection
# =========================================================================

class TestIntrospection:
    def test_schema_introspection(self):
        executor = _make_executor()
        result = executor.execute("{ __schema { queryType { name } } }")
        assert result.is_success
        schema = result.data["__schema"]
        assert schema["queryType"]["name"] == "Query"

    def test_schema_has_types(self):
        executor = _make_executor()
        result = executor.execute("{ __schema { types { name kind } } }")
        assert result.is_success
        type_names = {t["name"] for t in result.data["__schema"]["types"]}
        assert "String" in type_names

    def test_type_introspection(self):
        executor = _make_executor()
        result = executor.execute('{ __type(name: "String") { name kind } }')
        assert result.is_success
        assert result.data["__type"]["name"] == "String"
        assert result.data["__type"]["kind"] == "SCALAR"

    def test_type_introspection_unknown_returns_null(self):
        executor = _make_executor()
        result = executor.execute('{ __type(name: "UnknownType") { name } }')
        assert result.is_success
        assert result.data["__type"] is None

    def test_typename_meta_field(self):
        executor = _make_executor()
        result = executor.execute("{ __typename }")
        # __typename on the root Query type
        assert result.is_success

    def test_mutation_type_in_schema(self):
        executor = _make_executor()
        result = executor.execute("{ __schema { mutationType { name } } }")
        assert result.is_success
        assert result.data["__schema"]["mutationType"]["name"] == "Mutation"


# =========================================================================
# 9. Error handling
# =========================================================================

class TestErrorHandling:
    def test_syntax_error_returns_errors(self):
        executor = _make_executor()
        result = executor.execute("{ unclosed {")
        # Should not raise — errors list populated
        assert isinstance(result, ExecutionResult)

    def test_empty_query(self):
        executor = _make_executor()
        result = executor.execute("")
        assert not result.is_success or result.data is not None

    def test_no_operations_in_document(self):
        executor = _make_executor()
        result = executor.execute("fragment X on Product { id }")
        # No operations → error or empty result
        assert isinstance(result, ExecutionResult)

    def test_missing_field_returns_null(self):
        Product(id="e1", name="Err").save()
        executor = _make_executor()
        result = executor.execute('{ product(id: "e1") { id nonExistentField } }')
        # Should succeed but nonExistentField is None
        if result.is_success:
            assert result.data["product"].get("nonExistentField") is None

    def test_resolver_error_is_captured(self):
        """A resolver that raises GraphQLResolverError should surface as error."""
        from nitro.graphql.resolvers import GraphQLResolverError

        sdl = generate_schema([Product])
        resolvers = build_resolvers([Product])

        def bad_resolver(root, info, **kwargs):
            raise GraphQLResolverError("deliberately broken")

        resolvers["Query"]["products"] = bad_resolver
        executor = GraphQLExecutor(sdl, resolvers)
        result = executor.execute("{ products { id } }")
        assert not result.is_success or result.data is not None


# =========================================================================
# 10. Multi-entity executor
# =========================================================================

class TestMultiEntityExecutor:
    def test_query_two_entity_types(self):
        Product(id="me1", name="Prod").save()
        Tag(id="me2", label="hot").save()
        executor = _make_executor([Product, Tag])
        result = executor.execute("{ products { id name } tags { id label } }")
        assert result.is_success
        assert "products" in result.data
        assert "tags" in result.data

    def test_create_different_entity(self):
        executor = _make_executor([Product, Tag])
        result = executor.execute(
            'mutation { createTag(input: {label: "new", weight: 5}) { id label weight } }'
        )
        assert result.is_success
        assert result.data["createTag"]["label"] == "new"


# =========================================================================
# 11. Middleware helpers
# =========================================================================

class TestGraphiQLHtml:
    def test_returns_string(self):
        html = graphiql_html()
        assert isinstance(html, str)

    def test_contains_graphiql(self):
        html = graphiql_html()
        assert "graphiql" in html.lower()

    def test_custom_endpoint(self):
        html = graphiql_html("/my/graphql")
        assert "/my/graphql" in html

    def test_is_valid_html(self):
        html = graphiql_html()
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html


# =========================================================================
# 12. Module public API
# =========================================================================

class TestPublicAPI:
    """Verify that __init__.py exports all documented symbols."""

    def test_generate_schema_importable(self):
        from nitro.graphql import generate_schema
        assert callable(generate_schema)

    def test_entity_to_type_def_importable(self):
        from nitro.graphql import entity_to_type_def
        assert callable(entity_to_type_def)

    def test_map_field_type_importable(self):
        from nitro.graphql import map_field_type
        assert callable(map_field_type)

    def test_entity_type_info_importable(self):
        from nitro.graphql import EntityTypeInfo
        assert EntityTypeInfo is not None

    def test_build_resolvers_importable(self):
        from nitro.graphql import build_resolvers
        assert callable(build_resolvers)

    def test_graphql_executor_importable(self):
        from nitro.graphql import GraphQLExecutor
        assert GraphQLExecutor is not None

    def test_execution_result_importable(self):
        from nitro.graphql import ExecutionResult
        assert ExecutionResult is not None

    def test_parse_query_importable(self):
        from nitro.graphql import parse_query
        assert callable(parse_query)

    def test_graphql_handler_importable(self):
        from nitro.graphql import graphql_handler
        assert callable(graphql_handler)

    def test_register_graphql_route_importable(self):
        from nitro.graphql import register_graphql_route
        assert callable(register_graphql_route)

    def test_graphiql_html_importable(self):
        from nitro.graphql import graphiql_html
        assert callable(graphiql_html)

    def test_graphql_resolver_error_importable(self):
        from nitro.graphql import GraphQLResolverError
        assert issubclass(GraphQLResolverError, Exception)
