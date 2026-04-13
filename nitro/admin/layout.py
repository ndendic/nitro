"""Admin layout — sidebar + content shell."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from rusty_tags import (
    Div, Nav, A, Span, H1, Header, Main, Aside, HtmlString, Fragment,
)
from nitro.html import Page
from nitro.html.components import LucideIcon, Badge

if TYPE_CHECKING:
    from .config import AdminSite, AdminEntityConfig


def _sidebar_item(label: str, href: str, icon: str = "", active: bool = False, count: int | None = None) -> HtmlString:
    """Single sidebar navigation item."""
    active_cls = "bg-accent text-accent-foreground" if active else "hover:bg-muted"
    children = []
    if icon:
        children.append(LucideIcon(icon, cls="h-4 w-4 shrink-0"))
    children.append(Span(label, cls="truncate"))
    if count is not None:
        children.append(Badge(str(count), variant="secondary", cls="ml-auto text-xs"))
    return A(
        *children,
        href=href,
        cls=f"flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors {active_cls}",
    )


def _sidebar_group(category: str, items: list[HtmlString]) -> HtmlString:
    """Group of sidebar items under a category label."""
    children = []
    if category:
        children.append(
            Span(category, cls="px-3 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider")
        )
    children.extend(items)
    return Div(*children, cls="flex flex-col gap-0.5 mb-2")


def admin_sidebar(
    site: AdminSite,
    entity_configs: list[tuple[type, AdminEntityConfig]],
    active_entity: str = "",
    entity_counts: dict[str, int] | None = None,
) -> HtmlString:
    """Render the admin sidebar navigation."""
    prefix = site.url_prefix.rstrip("/")
    counts = entity_counts or {}

    # Dashboard link
    dashboard = _sidebar_item(
        "Dashboard", f"{prefix}/", icon="layout-dashboard",
        active=(active_entity == ""),
    )

    # Group entities by category
    groups: dict[str, list[tuple[type, AdminEntityConfig]]] = {}
    for cls, cfg in entity_configs:
        if not cfg.visible:
            continue
        cat = cfg.category or ""
        groups.setdefault(cat, []).append((cls, cfg))

    # Sort groups: empty category first, then alphabetical
    sorted_cats = sorted(groups.keys(), key=lambda c: (c != "", c))

    nav_groups = []
    for cat in sorted_cats:
        items = []
        # Sort within category by priority, then name
        for cls, cfg in sorted(groups[cat], key=lambda x: (x[1].priority, x[0].__name__)):
            name = cls.__name__
            items.append(_sidebar_item(
                cfg.title or name,
                f"{prefix}/{name.lower()}/",
                icon=cfg.icon,
                active=(active_entity == name),
                count=counts.get(name),
            ))
        nav_groups.append(_sidebar_group(cat, items))

    return Aside(
        Div(
            A(
                LucideIcon(site.brand_icon, cls="h-5 w-5"),
                Span(site.title, cls="font-bold text-lg"),
                href=f"{prefix}/",
                cls="flex items-center gap-2 no-underline text-foreground",
            ),
            cls="px-4 py-5 border-b",
        ),
        Nav(
            dashboard,
            Div(cls="my-2 border-b"),
            *nav_groups,
            cls="flex flex-col gap-0.5 p-3",
        ),
        cls=f"fixed top-0 left-0 h-screen {site.sidebar_width} border-r bg-card overflow-y-auto",
    )


def admin_layout(
    site: AdminSite,
    content: HtmlString,
    entity_configs: list[tuple[type, AdminEntityConfig]],
    active_entity: str = "",
    page_title: str = "",
    entity_counts: dict[str, int] | None = None,
) -> HtmlString:
    """Full admin page with sidebar and content area.

    Args:
        site: Admin site configuration.
        content: The main content fragment.
        entity_configs: List of (entity_class, config) tuples for sidebar.
        active_entity: Currently active entity class name (for sidebar highlight).
        page_title: Browser tab title.
        entity_counts: Optional dict of entity_name -> count for sidebar badges.

    Returns:
        Full HTML page.
    """
    sidebar = admin_sidebar(site, entity_configs, active_entity, entity_counts)

    main_content = Main(
        content,
        cls=f"{site.sidebar_width} ml-auto flex-1 p-8",
        style=f"margin-left: {'16rem' if site.sidebar_width == 'w-64' else '12rem'};",
    )

    return Page(
        sidebar,
        main_content,
        title=page_title or site.title,
        datastar=True,
        lucide=True,
    )
