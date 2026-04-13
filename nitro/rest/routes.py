"""Route registration for REST API endpoints in Sanic applications."""
from __future__ import annotations

from typing import Optional

from .config import RESTConfig
from .serializer import serialize_entity, serialize_many
from .filters import parse_query_params, apply_filters


def register_rest_routes(
    app,
    entity_class,
    config: Optional[RESTConfig] = None,
    url_prefix: Optional[str] = None,
) -> None:
    """Register RESTful JSON API routes on a Sanic app for *entity_class*.

    Registers (depending on config.actions):
        GET    <prefix>/             List (paginated, filterable, sortable, searchable)
        POST   <prefix>/             Create
        GET    <prefix>/<id>         Get one
        PUT    <prefix>/<id>         Full update
        PATCH  <prefix>/<id>         Partial update
        DELETE <prefix>/<id>         Delete

    Args:
        app: Sanic application instance.
        entity_class: Entity subclass to expose via REST.
        config: Optional RESTConfig; defaults auto-derived.
        url_prefix: Override URL prefix (also settable via config).
    """
    try:
        from sanic.response import json as json_response
    except ImportError as exc:
        raise ImportError(
            "Sanic is required for register_rest_routes. "
            "Install with: pip install sanic"
        ) from exc

    from nitro.api import ApiResponse, NotFoundError, ValidationError
    from nitro.html.components.model_views.fields import get_model_fields

    cfg = config or RESTConfig()
    if url_prefix:
        cfg = RESTConfig(**{**cfg.model_dump(), "url_prefix": url_prefix})
    cfg = cfg.resolve(entity_class)

    prefix = cfg.url_prefix.rstrip("/")
    entity_name = entity_class.__name__

    def _serialize(entity):
        return serialize_entity(entity, include=cfg.include_fields, exclude=cfg.exclude_fields)

    def _get_writable_fields():
        """Get field names that can be written via create/update."""
        fields = set(get_model_fields(entity_class).keys())
        if cfg.readonly_fields:
            fields -= set(cfg.readonly_fields)
        return fields

    # ---- LIST ---------------------------------------------------------------
    if "list" in cfg.actions:
        @app.get(f"{prefix}/")
        async def _rest_list(request):
            params = parse_query_params(
                dict(request.args) if request.args else {},
                default_page_size=cfg.page_size,
                max_page_size=cfg.max_page_size,
            )

            items, total = apply_filters(entity_class, params)

            include = params.fields or cfg.include_fields
            data = serialize_many(items, include=include, exclude=cfg.exclude_fields)

            resp = ApiResponse.paginated(data, total, params.page, params.page_size)
            return json_response(resp.to_dict())

        _rest_list.__name__ = f"rest_{entity_name}_list"

    # ---- GET ONE ------------------------------------------------------------
    if "get" in cfg.actions:
        @app.get(f"{prefix}/<entity_id>")
        async def _rest_get(request, entity_id: str):
            entity = entity_class.get(entity_id)
            if entity is None:
                resp = ApiResponse.error(f"{entity_name} not found", code="not_found")
                return json_response(resp.to_dict(), status=404)

            resp = ApiResponse.success(_serialize(entity))
            return json_response(resp.to_dict())

        _rest_get.__name__ = f"rest_{entity_name}_get"

    # ---- CREATE -------------------------------------------------------------
    if "create" in cfg.actions:
        @app.post(f"{prefix}/")
        async def _rest_create(request):
            data = request.json
            if not data or not isinstance(data, dict):
                resp = ApiResponse.error("Request body must be a JSON object", code="invalid_body")
                return json_response(resp.to_dict(), status=400)

            writable = _get_writable_fields()
            filtered = {k: v for k, v in data.items() if k in writable}

            try:
                entity = entity_class(**filtered)
                entity.save()
            except Exception as e:
                resp = ApiResponse.error(str(e), code="creation_failed")
                return json_response(resp.to_dict(), status=422)

            resp = ApiResponse.success(_serialize(entity))
            return json_response(resp.to_dict(), status=201)

        _rest_create.__name__ = f"rest_{entity_name}_create"

    # ---- UPDATE (PUT — full replace) ----------------------------------------
    if "update" in cfg.actions:
        @app.put(f"{prefix}/<entity_id>")
        async def _rest_update(request, entity_id: str):
            entity = entity_class.get(entity_id)
            if entity is None:
                resp = ApiResponse.error(f"{entity_name} not found", code="not_found")
                return json_response(resp.to_dict(), status=404)

            data = request.json
            if not data or not isinstance(data, dict):
                resp = ApiResponse.error("Request body must be a JSON object", code="invalid_body")
                return json_response(resp.to_dict(), status=400)

            writable = _get_writable_fields()
            for k, v in data.items():
                if k in writable:
                    setattr(entity, k, v)

            try:
                entity.save()
            except Exception as e:
                resp = ApiResponse.error(str(e), code="update_failed")
                return json_response(resp.to_dict(), status=422)

            resp = ApiResponse.success(_serialize(entity))
            return json_response(resp.to_dict())

        _rest_update.__name__ = f"rest_{entity_name}_update"

        # ---- PATCH (partial update) -----------------------------------------
        @app.patch(f"{prefix}/<entity_id>")
        async def _rest_patch(request, entity_id: str):
            entity = entity_class.get(entity_id)
            if entity is None:
                resp = ApiResponse.error(f"{entity_name} not found", code="not_found")
                return json_response(resp.to_dict(), status=404)

            data = request.json
            if not data or not isinstance(data, dict):
                resp = ApiResponse.error("Request body must be a JSON object", code="invalid_body")
                return json_response(resp.to_dict(), status=400)

            writable = _get_writable_fields()
            for k, v in data.items():
                if k in writable:
                    setattr(entity, k, v)

            try:
                entity.save()
            except Exception as e:
                resp = ApiResponse.error(str(e), code="update_failed")
                return json_response(resp.to_dict(), status=422)

            resp = ApiResponse.success(_serialize(entity))
            return json_response(resp.to_dict())

        _rest_patch.__name__ = f"rest_{entity_name}_patch"

    # ---- DELETE -------------------------------------------------------------
    if "delete" in cfg.actions:
        @app.delete(f"{prefix}/<entity_id>")
        async def _rest_delete(request, entity_id: str):
            entity = entity_class.get(entity_id)
            if entity is None:
                resp = ApiResponse.error(f"{entity_name} not found", code="not_found")
                return json_response(resp.to_dict(), status=404)

            try:
                entity.delete()
            except Exception as e:
                resp = ApiResponse.error(str(e), code="delete_failed")
                return json_response(resp.to_dict(), status=500)

            resp = ApiResponse.success({"deleted": entity_id})
            return json_response(resp.to_dict())

        _rest_delete.__name__ = f"rest_{entity_name}_delete"
