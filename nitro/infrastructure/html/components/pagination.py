"""Pagination component.

A navigation component for paginated content with Datastar signal integration.
Uses Tailwind utility classes following Basecoat patterns.
"""

from typing import Any, Union, Optional
from rusty_tags import Nav, Ul, Li, A, Div, Span, HtmlString, TagBuilder
from rusty_tags.datastar import Signal, Signals
from .icons import LucideIcon
from .utils import cn


def Pagination(
    total: int,
    signal: Optional[Signal] = None,
    signal_name: str = "page",
    current_page: int = 1,
    show_prev_next: bool = True,
    show_first_last: bool = False,
    siblings: int = 1,
    cls: str = "",
    **attrs: Any,
) -> Union[TagBuilder, HtmlString]:
    """Pagination component with Datastar signal integration.

    Creates a pagination navigation with page numbers, previous/next buttons,
    and optional first/last buttons. Uses Datastar signals for reactive page state.

    Args:
        total: Total number of pages
        signal: Datastar Signal object for page state (optional)
        signal_name: Name for auto-created signal if signal not provided
        current_page: Initial current page number (1-indexed)
        show_prev_next: Whether to show Previous/Next buttons
        show_first_last: Whether to show First/Last buttons
        siblings: Number of siblings on each side of current page
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Pagination navigation element

    Example:
        # Basic pagination
        Pagination(total=10)

        # With custom signal
        page_signal = Signal("page", 1)
        Pagination(total=10, signal=page_signal)

        # With first/last buttons
        Pagination(total=20, show_first_last=True)
    """
    # Create or use provided signal
    if signal is None:
        signal = Signal(signal_name, current_page)

    # Build page items
    items = []

    # First button (optional)
    if show_first_last:
        items.append(
            Li(
                A(
                    LucideIcon("chevrons-left", cls="size-4"),
                    cls=cn(
                        "btn-icon-ghost",
                        "opacity-50 pointer-events-none" if current_page == 1 else "",
                    ),
                    href="#",
                    on_click=f"$event.preventDefault(); ${signal_name} = 1",
                    aria_label="Go to first page",
                    data_attr_aria_disabled=f"${signal_name} === 1",
                ),
            )
        )

    # Previous button
    if show_prev_next:
        items.append(
            Li(
                A(
                    LucideIcon("chevron-left", cls="size-4"),
                    Span("Previous", cls="sr-only sm:not-sr-only sm:ml-1"),
                    cls="btn-ghost",
                    href="#",
                    on_click=f"$event.preventDefault(); if (${signal_name} > 1) ${signal_name}--",
                    aria_label="Go to previous page",
                    data_attr_aria_disabled=f"${signal_name} === 1",
                ),
            )
        )

    # Calculate page range to show
    def get_page_range(current: int, total: int, sibs: int) -> list:
        """Calculate which page numbers to show."""
        pages = []

        # Always show first page
        pages.append(1)

        # Calculate range around current
        start = max(2, current - sibs)
        end = min(total - 1, current + sibs)

        # Add ellipsis after first if needed
        if start > 2:
            pages.append("...")

        # Add middle pages
        for p in range(start, end + 1):
            pages.append(p)

        # Add ellipsis before last if needed
        if end < total - 1:
            pages.append("...")

        # Always show last page if more than 1 page
        if total > 1:
            pages.append(total)

        return pages

    page_range = get_page_range(current_page, total, siblings)

    # Add page number items
    for page in page_range:
        if page == "...":
            # Ellipsis
            items.append(
                Li(
                    Div(
                        LucideIcon("ellipsis", cls="size-4"),
                        cls="size-9 flex items-center justify-center",
                    ),
                )
            )
        else:
            # Page number
            is_current = page == current_page
            items.append(
                Li(
                    A(
                        str(page),
                        cls=cn(
                            "btn-icon-outline" if is_current else "btn-icon-ghost",
                        ),
                        href="#",
                        on_click=f"$event.preventDefault(); ${signal_name} = {page}",
                        aria_label=f"Go to page {page}",
                        aria_current="page" if is_current else "",
                        data_class_btn_icon_outline=f"${signal_name} === {page}",
                        data_class_btn_icon_ghost=f"${signal_name} !== {page}",
                    ) if is_current else A(
                        str(page),
                        cls="btn-icon-ghost",
                        href="#",
                        on_click=f"$event.preventDefault(); ${signal_name} = {page}",
                        aria_label=f"Go to page {page}",
                        data_class_btn_icon_outline=f"${signal_name} === {page}",
                        data_class_btn_icon_ghost=f"${signal_name} !== {page}",
                    ),
                )
            )

    # Next button
    if show_prev_next:
        items.append(
            Li(
                A(
                    Span("Next", cls="sr-only sm:not-sr-only sm:mr-1"),
                    LucideIcon("chevron-right", cls="size-4"),
                    cls="btn-ghost",
                    href="#",
                    on_click=f"$event.preventDefault(); if (${signal_name} < {total}) ${signal_name}++",
                    aria_label="Go to next page",
                    data_attr_aria_disabled=f"${signal_name} === {total}",
                ),
            )
        )

    # Last button (optional)
    if show_first_last:
        items.append(
            Li(
                A(
                    LucideIcon("chevrons-right", cls="size-4"),
                    cls=cn(
                        "btn-icon-ghost",
                        "opacity-50 pointer-events-none"
                        if current_page == total
                        else "",
                    ),
                    href="#",
                    on_click=f"$event.preventDefault(); ${signal_name} = {total}",
                    aria_label="Go to last page",
                    data_attr_aria_disabled=f"${signal_name} === {total}",
                ),
            )
        )

    return Nav(
        Ul(
            *items,
            cls="flex flex-row items-center gap-1",
        ),
        role="navigation",
        aria_label="Pagination",
        cls=cn("mx-auto flex w-full justify-center", cls),
        signals=Signals(**{signal_name: current_page}),
        **attrs,
    )


def PaginationContent(
    *pages: Any,
    signal_name: str = "page",
    cls: str = "",
    **attrs: Any,
) -> Union[TagBuilder, HtmlString]:
    """Container for paginated content.

    Shows only the content for the current page based on signal value.
    Children should be page content elements, shown by index (1-indexed).

    Args:
        *pages: Content for each page (index 1 = first page)
        signal_name: Name of the page signal
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Container that shows page content based on signal

    Example:
        PaginationContent(
            Div("Page 1 content"),
            Div("Page 2 content"),
            Div("Page 3 content"),
            signal_name="page",
        )
    """
    page_elements = []
    for i, page in enumerate(pages, start=1):
        page_elements.append(
            Div(
                page,
                data_show=f"${signal_name} === {i}",
            )
        )

    return Div(
        *page_elements,
        cls=cn(cls),
        **attrs,
    )
