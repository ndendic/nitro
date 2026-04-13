"""Route registration for CRUD views in Sanic applications."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .config import CRUDConfig
from .views import (
    crud_list_view,
    crud_detail_view,
    crud_create_view,
    crud_edit_view,
)

if TYPE_CHECKING:
    pass


def register_crud_routes(
    app,
    entity_class,
    config: Optional[CRUDConfig] = None,
    url_prefix: Optional[str] = None,
) -> None:
    """Register Sanic routes for full CRUD on *entity_class*.

    Registers:
        GET  <prefix>/             → crud_list_view
        GET  <prefix>/create       → crud_create_view
        POST <prefix>/create       → create entity, redirect to list
        GET  <prefix>/<id>         → crud_detail_view
        GET  <prefix>/<id>/edit    → crud_edit_view
        POST <prefix>/<id>/edit    → update entity, redirect to detail
        DELETE <prefix>/<id>/delete → delete entity, redirect to list

    Args:
        app: Sanic application instance.
        entity_class: Entity subclass to register routes for.
        config: Optional CRUDConfig; defaults auto-derived.
        url_prefix: Override URL prefix (also settable via config).
    """
    try:
        from sanic.response import html as html_response, redirect
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Sanic is required to use register_crud_routes. "
            "Install it with: pip install sanic"
        ) from exc

    cfg = config or CRUDConfig()
    if url_prefix:
        cfg = CRUDConfig(**{**cfg.model_dump(), "url_prefix": url_prefix})
    cfg = cfg.resolve(entity_class)

    prefix = cfg.url_prefix.rstrip("/")
    entity_name = entity_class.__name__

    # ---- LIST ---------------------------------------------------------------
    @app.get(f"{prefix}/")
    async def _crud_list(request):
        content = crud_list_view(entity_class, request=request, config=cfg)
        return html_response(str(content))

    _crud_list.__name__ = f"crud_{entity_name}_list"

    # ---- CREATE FORM --------------------------------------------------------
    @app.get(f"{prefix}/create")
    async def _crud_create_form(request):
        content = crud_create_view(entity_class, config=cfg)
        return html_response(str(content))

    _crud_create_form.__name__ = f"crud_{entity_name}_create_form"

    # ---- CREATE (POST) -------------------------------------------------------
    @app.post(f"{prefix}/create")
    async def _crud_create(request):
        data = request.json or request.form
        # Filter to known fields
        from nitro.html.components.model_views import get_model_fields
        known = set(get_model_fields(entity_class).keys())
        filtered = {k: v for k, v in data.items() if k in known}
        instance = entity_class(**filtered)
        instance.save()
        return redirect(f"{prefix}/")

    _crud_create.__name__ = f"crud_{entity_name}_create"

    # ---- DETAIL -------------------------------------------------------------
    @app.get(f"{prefix}/<entity_id>")
    async def _crud_detail(request, entity_id: str):
        try:
            content = crud_detail_view(entity_class, entity_id, config=cfg)
            return html_response(str(content))
        except ValueError:
            return html_response(f"<p>{cfg.title_singular} not found.</p>", status=404)

    _crud_detail.__name__ = f"crud_{entity_name}_detail"

    # ---- EDIT FORM ----------------------------------------------------------
    @app.get(f"{prefix}/<entity_id>/edit")
    async def _crud_edit_form(request, entity_id: str):
        try:
            content = crud_edit_view(entity_class, entity_id, config=cfg)
            return html_response(str(content))
        except ValueError:
            return html_response(f"<p>{cfg.title_singular} not found.</p>", status=404)

    _crud_edit_form.__name__ = f"crud_{entity_name}_edit_form"

    # ---- EDIT (POST) --------------------------------------------------------
    @app.post(f"{prefix}/<entity_id>/edit")
    async def _crud_edit(request, entity_id: str):
        instance = entity_class.get(entity_id)
        if instance is None:
            return html_response(f"<p>{cfg.title_singular} not found.</p>", status=404)
        data = request.json or request.form
        from nitro.html.components.model_views import get_model_fields
        known = set(get_model_fields(entity_class).keys())
        for k, v in data.items():
            if k in known:
                setattr(instance, k, v)
        instance.save()
        return redirect(f"{prefix}/{entity_id}")

    _crud_edit.__name__ = f"crud_{entity_name}_edit"

    # ---- DELETE -------------------------------------------------------------
    @app.delete(f"{prefix}/<entity_id>/delete")
    async def _crud_delete(request, entity_id: str):
        instance = entity_class.get(entity_id)
        if instance is None:
            return html_response(f"<p>{cfg.title_singular} not found.</p>", status=404)
        instance.delete()
        return redirect(f"{prefix}/")

    _crud_delete.__name__ = f"crud_{entity_name}_delete"
