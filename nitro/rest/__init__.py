"""nitro.rest — Auto-generate RESTful JSON API endpoints from Entity classes.

Provides:
- RESTConfig       : Per-entity REST API configuration (fields, pagination,
                     filtering, sorting, actions, URL prefix)
- register_rest_routes : Register CRUD JSON endpoints on a Sanic app
- serialize_entity : Convert an entity to a dict with field selection
- serialize_many   : Convert a list of entities
- QueryParams      : Parsed query parameter object
- parse_query_params : Parse request args into QueryParams
- apply_filters    : Apply filters/sort/pagination to entity queries

Quick start::

    from sanic import Sanic
    from nitro.rest import RESTConfig, register_rest_routes

    app = Sanic("MyAPI")
    register_rest_routes(app, Product)

    # With custom config:
    config = RESTConfig(
        page_size=50,
        exclude_fields=["internal_notes"],
        readonly_fields=["created_at"],
        actions=["list", "get", "create", "update"],  # no delete
    )
    register_rest_routes(app, Product, config=config)

Endpoints generated::

    GET    /api/products/           List (paginated, ?q=, ?sort=, ?field=val)
    POST   /api/products/           Create
    GET    /api/products/<id>       Get one
    PUT    /api/products/<id>       Full update
    PATCH  /api/products/<id>       Partial update
    DELETE /api/products/<id>       Delete

Query parameters::

    page        Page number (1-based)
    page_size   Items per page (capped by max_page_size)
    sort        Field name; prefix with '-' for descending
    q           Text search across string fields
    fields      Comma-separated fields to return
    <field>     Exact-match filter on any entity field
"""

from .config import RESTConfig
from .serializer import serialize_entity, serialize_many
from .filters import QueryParams, parse_query_params, apply_filters
from .routes import register_rest_routes

__all__ = [
    "RESTConfig",
    "register_rest_routes",
    "serialize_entity",
    "serialize_many",
    "QueryParams",
    "parse_query_params",
    "apply_filters",
]
