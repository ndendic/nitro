"""Full OpenAPI 3.1 spec builder from entity registrations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Type

from pydantic import BaseModel

from nitro.rest.config import RESTConfig
from .info import OpenAPIInfo
from .schema import generate_schema, generate_create_schema, generate_update_schema


@dataclass
class EntityRegistration:
    """Tracks an entity registered for REST + OpenAPI generation."""

    entity_class: Type[BaseModel]
    config: RESTConfig

    @property
    def name(self) -> str:
        return self.entity_class.__name__

    @property
    def resolved_config(self) -> RESTConfig:
        return self.config.resolve(self.entity_class)


def _api_response_schema(data_schema: dict[str, Any]) -> dict[str, Any]:
    """Wrap a data schema in the standard ApiResponse envelope."""
    return {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": data_schema,
            "meta": {
                "type": "object",
                "nullable": True,
                "properties": {
                    "total": {"type": "integer"},
                    "page": {"type": "integer"},
                    "page_size": {"type": "integer"},
                    "total_pages": {"type": "integer"},
                },
            },
            "errors": {
                "type": "array",
                "nullable": True,
                "items": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "code": {"type": "string"},
                        "field": {"type": "string"},
                    },
                },
            },
        },
        "required": ["success"],
    }


def _error_response() -> dict[str, Any]:
    return _api_response_schema({"type": "object", "nullable": True})


def _build_paths(reg: EntityRegistration) -> dict[str, Any]:
    """Build OpenAPI path items for one entity registration."""
    cfg = reg.resolved_config
    prefix = cfg.url_prefix.rstrip("/")
    name = reg.name
    tag = name

    entity_ref = f"#/components/schemas/{name}"
    create_ref = f"#/components/schemas/{name}Create"
    update_ref = f"#/components/schemas/{name}Update"

    paths: dict[str, Any] = {}

    collection_path = f"{prefix}/"
    item_path = f"{prefix}/{{id}}"
    collection_ops: dict[str, Any] = {}
    item_ops: dict[str, Any] = {}

    if "list" in cfg.actions:
        params = [
            {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
            {"name": "page_size", "in": "query", "schema": {"type": "integer", "default": cfg.page_size}},
            {"name": "sort", "in": "query", "schema": {"type": "string"}, "description": "Field name; prefix with '-' for descending"},
            {"name": "fields", "in": "query", "schema": {"type": "string"}, "description": "Comma-separated field names to return"},
        ]
        if cfg.enable_search:
            params.append({"name": "q", "in": "query", "schema": {"type": "string"}, "description": "Text search query"})

        list_data = {"type": "array", "items": {"$ref": entity_ref}}
        collection_ops["get"] = {
            "summary": f"List {name} records",
            "operationId": f"list_{name}",
            "tags": [tag],
            "parameters": params,
            "responses": {
                "200": {
                    "description": f"Paginated list of {name} records",
                    "content": {"application/json": {"schema": _api_response_schema(list_data)}},
                },
            },
        }

    if "create" in cfg.actions:
        collection_ops["post"] = {
            "summary": f"Create a {name}",
            "operationId": f"create_{name}",
            "tags": [tag],
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": create_ref}}},
            },
            "responses": {
                "201": {
                    "description": f"{name} created",
                    "content": {"application/json": {"schema": _api_response_schema({"$ref": entity_ref})}},
                },
                "400": {"description": "Invalid request body", "content": {"application/json": {"schema": _error_response()}}},
                "422": {"description": "Creation failed", "content": {"application/json": {"schema": _error_response()}}},
            },
        }

    id_param = {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}

    if "get" in cfg.actions:
        item_ops["get"] = {
            "summary": f"Get a {name} by ID",
            "operationId": f"get_{name}",
            "tags": [tag],
            "parameters": [id_param],
            "responses": {
                "200": {
                    "description": f"{name} details",
                    "content": {"application/json": {"schema": _api_response_schema({"$ref": entity_ref})}},
                },
                "404": {"description": "Not found", "content": {"application/json": {"schema": _error_response()}}},
            },
        }

    if "update" in cfg.actions:
        item_ops["put"] = {
            "summary": f"Update a {name}",
            "operationId": f"update_{name}",
            "tags": [tag],
            "parameters": [id_param],
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": update_ref}}},
            },
            "responses": {
                "200": {
                    "description": f"{name} updated",
                    "content": {"application/json": {"schema": _api_response_schema({"$ref": entity_ref})}},
                },
                "404": {"description": "Not found", "content": {"application/json": {"schema": _error_response()}}},
                "422": {"description": "Update failed", "content": {"application/json": {"schema": _error_response()}}},
            },
        }
        item_ops["patch"] = {
            "summary": f"Partially update a {name}",
            "operationId": f"patch_{name}",
            "tags": [tag],
            "parameters": [id_param],
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": update_ref}}},
            },
            "responses": {
                "200": {
                    "description": f"{name} updated",
                    "content": {"application/json": {"schema": _api_response_schema({"$ref": entity_ref})}},
                },
                "404": {"description": "Not found", "content": {"application/json": {"schema": _error_response()}}},
                "422": {"description": "Update failed", "content": {"application/json": {"schema": _error_response()}}},
            },
        }

    if "delete" in cfg.actions:
        item_ops["delete"] = {
            "summary": f"Delete a {name}",
            "operationId": f"delete_{name}",
            "tags": [tag],
            "parameters": [id_param],
            "responses": {
                "200": {
                    "description": f"{name} deleted",
                    "content": {"application/json": {"schema": _api_response_schema({"type": "object", "properties": {"deleted": {"type": "string"}}})}},
                },
                "404": {"description": "Not found", "content": {"application/json": {"schema": _error_response()}}},
            },
        }

    if collection_ops:
        paths[collection_path] = collection_ops
    if item_ops:
        paths[item_path] = item_ops

    return paths


def generate_openapi(
    registrations: list[EntityRegistration],
    info: Optional[OpenAPIInfo] = None,
    servers: Optional[list[dict[str, str]]] = None,
) -> dict[str, Any]:
    """Build a complete OpenAPI 3.1.0 specification.

    Args:
        registrations: List of EntityRegistration objects.
        info: API metadata. Defaults to a basic Nitro API info.
        servers: Optional server list (e.g. [{"url": "http://localhost:8000"}]).

    Returns:
        Complete OpenAPI 3.1.0 spec as a dict.
    """
    info = info or OpenAPIInfo()

    spec: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": info.to_openapi(),
    }

    if servers:
        spec["servers"] = servers

    paths: dict[str, Any] = {}
    schemas: dict[str, Any] = {}
    tags: list[dict[str, str]] = []

    for reg in registrations:
        cfg = reg.resolved_config
        name = reg.name

        schemas[name] = generate_schema(
            reg.entity_class,
            exclude=cfg.exclude_fields,
            readonly_fields=cfg.readonly_fields,
        )
        schemas[f"{name}Create"] = generate_create_schema(
            reg.entity_class,
            exclude=cfg.exclude_fields,
            readonly_fields=cfg.readonly_fields,
        )
        schemas[f"{name}Update"] = generate_update_schema(
            reg.entity_class,
            exclude=cfg.exclude_fields,
            readonly_fields=cfg.readonly_fields,
        )

        entity_paths = _build_paths(reg)
        paths.update(entity_paths)

        tags.append({"name": name, "description": f"{name} operations"})

    spec["paths"] = paths
    if tags:
        spec["tags"] = tags
    spec["components"] = {"schemas": schemas}

    return spec
