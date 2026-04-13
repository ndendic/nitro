"""Route registration for the admin panel."""
from __future__ import annotations

from typing import Optional, Type

from .config import AdminSite, AdminEntityConfig
from .discovery import discover_entities
from .views import (
    admin_dashboard_view,
    admin_entity_list_view,
    admin_entity_detail_view,
    admin_entity_create_view,
    admin_entity_edit_view,
)
from .layout import admin_layout


def _get_entity_counts(entity_classes: list[Type]) -> dict[str, int]:
    """Fetch record counts for all entity classes."""
    counts = {}
    for cls in entity_classes:
        try:
            counts[cls.__name__] = cls.count()
        except Exception:
            counts[cls.__name__] = 0
    return counts


def register_admin(
    app,
    site: Optional[AdminSite] = None,
    entities: Optional[list[Type]] = None,
) -> None:
    """Register admin panel routes on a Sanic application.

    Auto-discovers all Entity subclasses (with ``table=True``) unless
    *entities* is provided explicitly.

    Args:
        app: Sanic application instance.
        site: Admin site configuration. Defaults to ``AdminSite()``.
        entities: Explicit list of entity classes. If None, auto-discovers.
    """
    try:
        from sanic.response import html as html_response, redirect
    except ImportError as exc:
        raise ImportError(
            "Sanic is required to use register_admin. "
            "Install it with: pip install sanic"
        ) from exc

    site = site or AdminSite()
    prefix = site.url_prefix.rstrip("/")

    # Discover or use explicit entities
    entity_classes = entities or discover_entities()

    # Build resolved configs for each entity
    entity_configs: list[tuple[Type, AdminEntityConfig]] = []
    for cls in entity_classes:
        cfg = site.config_for(cls)
        # Override url_prefix to be under admin
        admin_prefix = f"{prefix}/{cls.__name__.lower()}"
        cfg_data = cfg.model_dump()
        cfg_data["url_prefix"] = admin_prefix
        cfg = AdminEntityConfig(**cfg_data)
        entity_configs.append((cls, cfg))

    # Map lowercase name -> (class, config) for route lookup
    entity_map: dict[str, tuple[Type, AdminEntityConfig]] = {
        cls.__name__.lower(): (cls, cfg) for cls, cfg in entity_configs
    }

    # ---- DASHBOARD ----------------------------------------------------------
    @app.get(f"{prefix}/")
    async def _admin_dashboard(request):
        counts = _get_entity_counts([cls for cls, _ in entity_configs])
        content = admin_dashboard_view(site, entity_configs, counts)
        page = admin_layout(
            site, content, entity_configs,
            active_entity="",
            page_title=f"{site.title} Dashboard",
            entity_counts=counts,
        )
        return html_response(str(page))

    _admin_dashboard.__name__ = "admin_dashboard"

    # ---- ENTITY LIST --------------------------------------------------------
    @app.get(f"{prefix}/<entity_name>/")
    async def _admin_entity_list(request, entity_name: str):
        entry = entity_map.get(entity_name.lower())
        if not entry:
            return html_response("<p>Entity not found.</p>", status=404)
        cls, cfg = entry
        content = admin_entity_list_view(cls, cfg, site, request=request)
        counts = _get_entity_counts([c for c, _ in entity_configs])
        page = admin_layout(
            site, content, entity_configs,
            active_entity=cls.__name__,
            page_title=f"{cfg.title} — {site.title}",
            entity_counts=counts,
        )
        return html_response(str(page))

    _admin_entity_list.__name__ = "admin_entity_list"

    # ---- CREATE FORM --------------------------------------------------------
    @app.get(f"{prefix}/<entity_name>/create")
    async def _admin_create_form(request, entity_name: str):
        entry = entity_map.get(entity_name.lower())
        if not entry:
            return html_response("<p>Entity not found.</p>", status=404)
        cls, cfg = entry
        content = admin_entity_create_view(cls, cfg, site)
        counts = _get_entity_counts([c for c, _ in entity_configs])
        page = admin_layout(
            site, content, entity_configs,
            active_entity=cls.__name__,
            page_title=f"Create {cfg.title_singular} — {site.title}",
            entity_counts=counts,
        )
        return html_response(str(page))

    _admin_create_form.__name__ = "admin_create_form"

    # ---- CREATE (POST) ------------------------------------------------------
    @app.post(f"{prefix}/<entity_name>/create")
    async def _admin_create(request, entity_name: str):
        entry = entity_map.get(entity_name.lower())
        if not entry:
            return html_response("<p>Entity not found.</p>", status=404)
        cls, cfg = entry
        data = request.json or request.form
        from nitro.html.components.model_views import get_model_fields
        known = set(get_model_fields(cls).keys())
        filtered = {k: v for k, v in data.items() if k in known}
        instance = cls(**filtered)
        instance.save()
        return redirect(f"{prefix}/{entity_name.lower()}/")

    _admin_create.__name__ = "admin_create"

    # ---- DETAIL -------------------------------------------------------------
    @app.get(f"{prefix}/<entity_name>/<entity_id>")
    async def _admin_detail(request, entity_name: str, entity_id: str):
        entry = entity_map.get(entity_name.lower())
        if not entry:
            return html_response("<p>Entity not found.</p>", status=404)
        cls, cfg = entry
        try:
            content = admin_entity_detail_view(cls, entity_id, cfg, site)
        except ValueError:
            return html_response(f"<p>{cfg.title_singular} not found.</p>", status=404)
        counts = _get_entity_counts([c for c, _ in entity_configs])
        page = admin_layout(
            site, content, entity_configs,
            active_entity=cls.__name__,
            page_title=f"{cfg.title_singular} — {site.title}",
            entity_counts=counts,
        )
        return html_response(str(page))

    _admin_detail.__name__ = "admin_detail"

    # ---- EDIT FORM ----------------------------------------------------------
    @app.get(f"{prefix}/<entity_name>/<entity_id>/edit")
    async def _admin_edit_form(request, entity_name: str, entity_id: str):
        entry = entity_map.get(entity_name.lower())
        if not entry:
            return html_response("<p>Entity not found.</p>", status=404)
        cls, cfg = entry
        try:
            content = admin_entity_edit_view(cls, entity_id, cfg, site)
        except ValueError:
            return html_response(f"<p>{cfg.title_singular} not found.</p>", status=404)
        counts = _get_entity_counts([c for c, _ in entity_configs])
        page = admin_layout(
            site, content, entity_configs,
            active_entity=cls.__name__,
            page_title=f"Edit {cfg.title_singular} — {site.title}",
            entity_counts=counts,
        )
        return html_response(str(page))

    _admin_edit_form.__name__ = "admin_edit_form"

    # ---- EDIT (POST) --------------------------------------------------------
    @app.post(f"{prefix}/<entity_name>/<entity_id>/edit")
    async def _admin_edit(request, entity_name: str, entity_id: str):
        entry = entity_map.get(entity_name.lower())
        if not entry:
            return html_response("<p>Entity not found.</p>", status=404)
        cls, cfg = entry
        instance = cls.get(entity_id)
        if instance is None:
            return html_response(f"<p>{cfg.title_singular} not found.</p>", status=404)
        data = request.json or request.form
        from nitro.html.components.model_views import get_model_fields
        known = set(get_model_fields(cls).keys())
        for k, v in data.items():
            if k in known:
                setattr(instance, k, v)
        instance.save()
        return redirect(f"{prefix}/{entity_name.lower()}/{entity_id}")

    _admin_edit.__name__ = "admin_edit"

    # ---- DELETE -------------------------------------------------------------
    @app.delete(f"{prefix}/<entity_name>/<entity_id>/delete")
    async def _admin_delete(request, entity_name: str, entity_id: str):
        entry = entity_map.get(entity_name.lower())
        if not entry:
            return html_response("<p>Entity not found.</p>", status=404)
        cls, cfg = entry
        instance = cls.get(entity_id)
        if instance is None:
            return html_response(f"<p>{cfg.title_singular} not found.</p>", status=404)
        instance.delete()
        return redirect(f"{prefix}/{entity_name.lower()}/")

    _admin_delete.__name__ = "admin_delete"
