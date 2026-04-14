"""Sanic route registration for serving OpenAPI spec and Swagger UI."""
from __future__ import annotations

import json
from typing import Optional

from .info import OpenAPIInfo
from .spec import EntityRegistration, generate_openapi
from nitro.rest.config import RESTConfig


_SWAGGER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title} — API Docs</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"/>
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({{
  url: "{spec_url}",
  dom_id: "#swagger-ui",
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
  layout: "StandaloneLayout",
}});
</script>
</body>
</html>"""


_registry: list[EntityRegistration] = []


def add_entity(entity_class, config: Optional[RESTConfig] = None) -> None:
    """Register an entity for OpenAPI spec generation.

    Called automatically by register_openapi_routes when entities are
    already registered via register_rest_routes. Can also be called
    manually before route registration.
    """
    cfg = config or RESTConfig()
    _registry.append(EntityRegistration(entity_class=entity_class, config=cfg))


def get_registry() -> list[EntityRegistration]:
    """Return the current entity registry."""
    return list(_registry)


def clear_registry() -> None:
    """Clear all registered entities (useful for testing)."""
    _registry.clear()


def register_openapi_routes(
    app,
    entities: Optional[list[tuple]] = None,
    info: Optional[OpenAPIInfo] = None,
    servers: Optional[list[dict[str, str]]] = None,
    spec_path: str = "/openapi.json",
    docs_path: str = "/docs",
) -> None:
    """Register /openapi.json and /docs routes on a Sanic app.

    Args:
        app: Sanic application.
        entities: List of (entity_class, RESTConfig | None) tuples.
            If None, uses the module-level registry populated by add_entity().
        info: API metadata.
        servers: Server list for the spec.
        spec_path: URL path for the JSON spec (default: /openapi.json).
        docs_path: URL path for Swagger UI (default: /docs).
    """
    try:
        from sanic.response import json as json_response, html as html_response
    except ImportError as exc:
        raise ImportError(
            "Sanic is required for register_openapi_routes. "
            "Install with: pip install sanic"
        ) from exc

    info = info or OpenAPIInfo()

    registrations = []
    if entities:
        for entity_class, config in entities:
            registrations.append(EntityRegistration(
                entity_class=entity_class,
                config=config or RESTConfig(),
            ))
    else:
        registrations = get_registry()

    if not registrations:
        raise ValueError(
            "No entities registered for OpenAPI. "
            "Pass entities=[(MyEntity, config)] or call add_entity() first."
        )

    spec = generate_openapi(registrations, info=info, servers=servers)

    @app.get(spec_path)
    async def openapi_spec(request):
        return json_response(spec)

    openapi_spec.__name__ = "openapi_spec"

    title = info.title
    @app.get(docs_path)
    async def openapi_docs(request):
        page = _SWAGGER_HTML.format(title=title, spec_url=spec_path)
        return html_response(page)

    openapi_docs.__name__ = "openapi_docs"
