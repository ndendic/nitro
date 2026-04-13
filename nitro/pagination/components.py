"""
UI pagination components for nitro.pagination.

Provides the ``Paginator`` function which renders a set of page-navigation
controls using RustyTags and Datastar-compatible attributes.
"""

from __future__ import annotations

from typing import Any

from rusty_tags import Button, Div, Nav, Span, HtmlString


def Paginator(
    *,
    page: int,
    pages: int,
    total: int,
    base_url: str,
    size: int = 20,
    window: int = 2,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Render a pagination control bar.

    Generates previous/next buttons and numbered page links.  Each button
    uses a Datastar ``@get(...)`` action so navigation is handled via
    Datastar without full-page reloads.

    Args:
        page:     Current page number (1-based).
        pages:    Total number of pages.
        total:    Total number of items (used for the info label).
        base_url: Base URL for page links. Page/size query params are
                  appended automatically, e.g. ``/items?page=2&size=20``.
        size:     Items per page (forwarded in the URL).
        window:   Number of page buttons to show on each side of the
                  current page.
        cls:      Additional CSS classes for the outer ``<nav>``.
        **attrs:  Extra attributes forwarded to the ``<nav>`` element.

    Returns:
        An ``HtmlString`` containing the complete pagination nav.

    Example::

        from nitro.pagination.components import Paginator

        nav = Paginator(
            page=2,
            pages=10,
            total=200,
            base_url="/products",
            size=20,
        )
    """
    has_prev = page > 1
    has_next = page < pages

    def _page_url(p: int) -> str:
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}page={p}&size={size}"

    def _btn(
        label: str,
        target_page: int,
        *,
        active: bool = False,
        disabled: bool = False,
    ) -> HtmlString:
        base_cls = (
            "inline-flex items-center justify-center min-w-[2rem] h-8 px-2 "
            "rounded text-sm font-medium transition-colors "
            "border border-transparent "
        )
        if disabled:
            state_cls = "text-gray-400 cursor-not-allowed"
            return Button(
                label,
                cls=base_cls + state_cls,
                disabled=True,
            )
        if active:
            state_cls = (
                "bg-primary text-primary-foreground border-primary "
                "pointer-events-none"
            )
        else:
            state_cls = (
                "text-foreground hover:bg-accent hover:text-accent-foreground "
                "cursor-pointer"
            )
        return Button(
            label,
            cls=base_cls + state_cls,
            data_on_click=f"@get('{_page_url(target_page)}')",
        )

    # Build page number list with ellipsis
    page_buttons: list[HtmlString] = []

    lo = max(1, page - window)
    hi = min(pages, page + window)

    if lo > 1:
        page_buttons.append(_btn("1", 1))
        if lo > 2:
            page_buttons.append(Span("...", cls="px-1 text-gray-400 self-center"))

    for p in range(lo, hi + 1):
        page_buttons.append(_btn(str(p), p, active=(p == page)))

    if hi < pages:
        if hi < pages - 1:
            page_buttons.append(Span("...", cls="px-1 text-gray-400 self-center"))
        page_buttons.append(_btn(str(pages), pages))

    info_label = Span(
        f"Page {page} of {pages}" + (f" ({total} items)" if total else ""),
        cls="text-sm text-gray-500 dark:text-gray-400 select-none",
    )

    controls = Div(
        _btn("←", page - 1, disabled=not has_prev),
        *page_buttons,
        _btn("→", page + 1, disabled=not has_next),
        cls="flex items-center gap-1",
    )

    outer_cls = (
        "flex flex-col sm:flex-row items-center justify-between gap-2 "
        "py-3 px-1 " + cls
    ).strip()

    return Nav(
        info_label,
        controls,
        cls=outer_cls,
        **attrs,
    )
