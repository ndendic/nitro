"""Admin view generators — dashboard and entity pages."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from rusty_tags import Div, H1, H2, H3, Span, A, P, HtmlString, Fragment
from nitro.html.components import Card, CardHeader, CardTitle, CardContent, LucideIcon, Badge
from nitro.crud.views import crud_list_view, crud_detail_view, crud_create_view, crud_edit_view

if TYPE_CHECKING:
    from .config import AdminSite, AdminEntityConfig


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def _entity_card(
    entity_class,
    config: AdminEntityConfig,
    prefix: str,
    count: int,
) -> HtmlString:
    """A single dashboard card for an entity type."""
    name = entity_class.__name__
    icon = config.icon or "database"
    title = config.title or name

    return A(
        Card(
            CardHeader(
                Div(
                    LucideIcon(icon, cls="h-5 w-5 text-muted-foreground"),
                    CardTitle(title, cls="text-base"),
                    cls="flex items-center gap-2",
                ),
                Div(
                    Span(str(count), cls="text-3xl font-bold"),
                    Span("records", cls="text-xs text-muted-foreground ml-1"),
                    cls="flex items-baseline gap-1 mt-1",
                ),
            ),
            CardContent(
                P(config.description or f"Manage {title.lower()}", cls="text-sm text-muted-foreground"),
            ) if config.description or True else Fragment(),
            cls="hover:shadow-md transition-shadow cursor-pointer",
        ),
        href=f"{prefix}/{name.lower()}/",
        cls="no-underline text-foreground",
    )


def admin_dashboard_view(
    site: AdminSite,
    entity_configs: list[tuple[type, AdminEntityConfig]],
    entity_counts: dict[str, int],
) -> HtmlString:
    """Render the admin dashboard with entity cards.

    Args:
        site: Admin site configuration.
        entity_configs: List of (entity_class, config) tuples.
        entity_counts: Dict mapping entity class name -> record count.

    Returns:
        Dashboard HTML fragment (without layout wrapper).
    """
    prefix = site.url_prefix.rstrip("/")

    header = Div(
        H1(site.title, cls="text-3xl font-bold"),
        P(f"{len(entity_configs)} registered entities", cls="text-muted-foreground mt-1"),
        cls="mb-8",
    )

    # Build cards for visible entities
    cards = []
    for cls, cfg in sorted(entity_configs, key=lambda x: (x[1].priority, x[0].__name__)):
        if not cfg.dashboard_visible:
            continue
        count = entity_counts.get(cls.__name__, 0)
        cards.append(_entity_card(cls, cfg, prefix, count))

    grid = Div(*cards, cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4")

    return Div(header, grid, cls="admin-dashboard")


# ---------------------------------------------------------------------------
# Entity list/detail/create/edit — wrappers that use crud views
# ---------------------------------------------------------------------------

def admin_entity_list_view(
    entity_class,
    config: AdminEntityConfig,
    site: AdminSite,
    request=None,
) -> HtmlString:
    """CRUD list view wrapped with admin-specific header."""
    crud_view = crud_list_view(entity_class, request=request, config=config)

    return Div(crud_view, cls="admin-entity-list")


def admin_entity_detail_view(
    entity_class,
    entity_id: str,
    config: AdminEntityConfig,
    site: AdminSite,
) -> HtmlString:
    """CRUD detail view wrapped for admin context."""
    prefix = site.url_prefix.rstrip("/")
    entity_name = entity_class.__name__

    # Override the back link to go to admin entity list
    crud_view = crud_detail_view(entity_class, entity_id, config=config)

    return Div(crud_view, cls="admin-entity-detail")


def admin_entity_create_view(
    entity_class,
    config: AdminEntityConfig,
    site: AdminSite,
) -> HtmlString:
    """CRUD create form for admin context."""
    return Div(crud_create_view(entity_class, config=config), cls="admin-entity-create")


def admin_entity_edit_view(
    entity_class,
    entity_id: str,
    config: AdminEntityConfig,
    site: AdminSite,
) -> HtmlString:
    """CRUD edit form for admin context."""
    return Div(crud_edit_view(entity_class, entity_id, config=config), cls="admin-entity-edit")
