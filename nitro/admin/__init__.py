"""nitro.admin — Auto-generated admin panel from Entity classes.

Public API
----------
AdminSite
    Configuration for the admin panel (title, branding, entity configs).

AdminEntityConfig
    Per-entity admin configuration (extends CRUDConfig with admin-specific options).

register_admin(app, site=None)
    Register admin routes on a Sanic application — auto-discovers entities.

admin_dashboard_view(site) -> HtmlString
    Dashboard page with entity counts and quick links.

Quick start::

    from nitro.admin import AdminSite, register_admin

    site = AdminSite(title="My Admin")
    register_admin(app, site=site)
    # Admin panel available at /admin/
"""

from .config import AdminSite, AdminEntityConfig
from .discovery import discover_entities
from .views import (
    admin_dashboard_view,
    admin_entity_list_view,
    admin_entity_detail_view,
    admin_entity_create_view,
    admin_entity_edit_view,
)
from .routes import register_admin
from .layout import admin_layout

__all__ = [
    "AdminSite",
    "AdminEntityConfig",
    "discover_entities",
    "admin_dashboard_view",
    "admin_entity_list_view",
    "admin_entity_detail_view",
    "admin_entity_create_view",
    "admin_entity_edit_view",
    "register_admin",
    "admin_layout",
]
