"""nitro.openapi — Auto-generate OpenAPI 3.1 specifications from Entity classes.

Provides:
- OpenAPIInfo         : API metadata (title, version, description)
- generate_schema     : Generate JSON Schema component from an Entity class
- generate_openapi    : Build a full OpenAPI 3.1 spec from registered entities
- register_openapi_routes : Serve /openapi.json and /docs (Swagger UI) on Sanic

Quick start::

    from sanic import Sanic
    from nitro.rest import register_rest_routes
    from nitro.openapi import register_openapi_routes, OpenAPIInfo

    app = Sanic("MyAPI")
    register_rest_routes(app, Product)
    register_rest_routes(app, Order)

    register_openapi_routes(app, info=OpenAPIInfo(
        title="My Store API",
        version="1.0.0",
        description="Product and order management",
    ))

    # GET /openapi.json  → OpenAPI 3.1 spec
    # GET /docs           → Swagger UI
"""

from .info import OpenAPIInfo
from .schema import generate_schema
from .spec import generate_openapi, EntityRegistration
from .routes import register_openapi_routes

__all__ = [
    "OpenAPIInfo",
    "generate_schema",
    "generate_openapi",
    "EntityRegistration",
    "register_openapi_routes",
]
