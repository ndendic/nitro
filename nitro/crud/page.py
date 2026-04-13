"""CRUDPage — full Page() wrapper for CRUD views."""
from __future__ import annotations

from typing import Optional

from rusty_tags import HtmlString, Div, Nav, A, Span
from nitro.html import Page
from nitro.html.components import LucideIcon

from .config import CRUDConfig
from .views import crud_list_view


def CRUDPage(
    entity_class,
    config: Optional[CRUDConfig] = None,
    title: Optional[str] = None,
    datastar: bool = True,
    lucide: bool = True,
) -> HtmlString:
    """Return a full Page() wrapping the list view for *entity_class*.

    This is a convenience wrapper intended for top-level route handlers that
    want a complete standalone page (with <html>, <head>, <body>) rather than
    a bare fragment.

    Args:
        entity_class: Entity subclass to display.
        config: Optional CRUDConfig; defaults are auto-derived.
        title: Page <title> (defaults to config.title).
        datastar: Include Datastar SDK in page headers.
        lucide: Include Lucide icons in page headers.

    Returns:
        HtmlString — full HTML document.
    """
    cfg = (config or CRUDConfig()).resolve(entity_class)
    page_title = title or cfg.title

    nav = Nav(
        A(
            LucideIcon(cfg.icon) if cfg.icon else Span(),
            Span(cfg.title, cls="font-semibold"),
            href=cfg.url_prefix + "/",
            cls="flex items-center gap-2 text-sm hover:underline",
        ),
        cls="border-b px-6 py-3 flex items-center",
    )

    content = crud_list_view(entity_class, config=cfg)

    return Page(
        nav,
        Div(content, cls="container mx-auto px-6 py-8"),
        title=page_title,
        datastar=datastar,
        lucide=lucide,
    )
