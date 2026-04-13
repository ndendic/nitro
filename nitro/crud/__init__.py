"""nitro.crud — Auto-generate complete CRUD views from Entity classes.

Public API
----------
CRUDConfig
    Pydantic model holding per-entity CRUD configuration (title, icon,
    field lists, pagination, searchability, allowed actions, URL prefix).

crud_list_view(entity_class, request=None, config=None) -> HtmlString
    Table + create button + delete-confirm dialog fragment.

crud_detail_view(entity_class, entity_id, config=None) -> HtmlString
    Card view of a single entity with breadcrumb and action buttons.

crud_create_view(entity_class, config=None) -> HtmlString
    Blank create form fragment.

crud_edit_view(entity_class, entity_id, config=None) -> HtmlString
    Edit form pre-filled from the existing entity.

register_crud_routes(app, entity_class, config=None, url_prefix=None)
    Register the five standard CRUD routes on a Sanic application.

CRUDPage(entity_class, config=None) -> HtmlString
    Full Page() wrapping the list view — suitable for top-level handlers.

Quick start::

    from nitro.crud import CRUDConfig, register_crud_routes

    config = CRUDConfig(title="Products", icon="package")
    register_crud_routes(app, Product, config=config)
"""

from .config import CRUDConfig
from .views import (
    crud_list_view,
    crud_detail_view,
    crud_create_view,
    crud_edit_view,
)
from .routes import register_crud_routes
from .page import CRUDPage

__all__ = [
    "CRUDConfig",
    "crud_list_view",
    "crud_detail_view",
    "crud_create_view",
    "crud_edit_view",
    "register_crud_routes",
    "CRUDPage",
]
