"""nitro.graphql — GraphQL support layer for Nitro Entity models.

Auto-generates GraphQL schemas and resolvers from Nitro Entity classes,
with a lightweight built-in executor (no required external dependencies)
and optional ``graphql-core`` integration.

Quick start::

    from nitro.graphql import (
        generate_schema,
        build_resolvers,
        GraphQLExecutor,
        register_graphql_route,
    )
    from sanic import Sanic

    # 1. Generate SDL schema from entity classes
    schema_sdl = generate_schema([Product, Order])

    # 2. Build resolver map
    resolvers = build_resolvers([Product, Order])

    # 3. Create executor
    executor = GraphQLExecutor(schema_sdl, resolvers)

    # 4. Register route on Sanic app
    app = Sanic("MyApp")
    register_graphql_route(app, executor)

    # ---- Manual execution (no web framework needed) ----
    result = executor.execute(
        "{ products { id name price } }"
    )
    print(result.data)   # {"products": [...]}
    print(result.errors) # []

    # With variables:
    result = executor.execute(
        "query GetProduct($id: ID!) { product(id: $id) { id name } }",
        variables={"id": "abc-123"},
    )

Schema generation::

    from nitro.graphql.schema import generate_schema, entity_to_type_def

    # Full SDL document
    sdl = generate_schema([Product, Order])

    # Single type block
    product_type = entity_to_type_def(Product)

Resolver map::

    from nitro.graphql.resolvers import build_resolvers

    resolvers = build_resolvers([Product])
    # resolvers["Query"]["product"](root, info, id="abc") -> dict | None
    # resolvers["Mutation"]["createProduct"](root, info, input={...}) -> dict

Middleware::

    from nitro.graphql.middleware import (
        graphql_handler,
        graphiql_html,
        register_graphql_route,
    )

    handler = graphql_handler(executor)       # Sanic async handler
    html = graphiql_html("/graphql")          # GraphiQL IDE page
    register_graphql_route(app, executor)     # Convenience registration

Public API summary
------------------
Schema
~~~~~~
generate_schema(entity_classes, include_mutations) -> str
    Full SDL document.

entity_to_type_def(entity_class) -> str
    Single ``type`` SDL block.

map_field_type(field_info) -> str
    Python/JSON-schema field → GraphQL type string.

EntityTypeInfo
    Parsed type info dataclass.

Resolvers
~~~~~~~~~
build_resolvers(entity_classes) -> ResolverMap
    Nested dict of Query/Mutation resolvers.

GraphQLResolverError
    Exception raised by auto-generated resolvers on domain errors.

Executor
~~~~~~~~
GraphQLExecutor(schema_sdl, resolvers)
    Execute GraphQL queries.

ExecutionResult(data, errors)
    Result container with ``to_dict()`` method.

parse_query(query_str) -> Document
    Parse a query string (built-in parser).

Middleware
~~~~~~~~~~
graphql_handler(executor) -> async callable
    Sanic request handler.

register_graphql_route(app, executor, path, graphiql)
    Register on a Sanic application.

graphiql_html(endpoint) -> str
    GraphiQL IDE HTML.
"""

from .schema import (
    generate_schema,
    entity_to_type_def,
    map_field_type,
    EntityTypeInfo,
)
from .resolvers import (
    build_resolvers,
    GraphQLResolverError,
    ResolverMap,
)
from .executor import (
    GraphQLExecutor,
    ExecutionResult,
    parse_query,
)
from .middleware import (
    graphql_handler,
    register_graphql_route,
    graphiql_html,
)

__all__ = [
    # Schema
    "generate_schema",
    "entity_to_type_def",
    "map_field_type",
    "EntityTypeInfo",
    # Resolvers
    "build_resolvers",
    "GraphQLResolverError",
    "ResolverMap",
    # Executor
    "GraphQLExecutor",
    "ExecutionResult",
    "parse_query",
    # Middleware
    "graphql_handler",
    "register_graphql_route",
    "graphiql_html",
]
