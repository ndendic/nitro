"""Breadcrumb navigation component.

A navigation component that shows the user's current location within a site hierarchy.
Uses Tailwind utility classes following Basecoat patterns.
"""

from typing import Any, Optional, Union
from rusty_tags import Nav, Ol, Li, A, Span, HtmlString, TagBuilder
from .icons import LucideIcon
from .utils import cn


def Breadcrumb(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> Union[TagBuilder, HtmlString]:
    """Breadcrumb navigation container.

    Creates a breadcrumb navigation with proper ARIA attributes.
    Children should be BreadcrumbItem and BreadcrumbSeparator components.

    Args:
        *children: BreadcrumbItem and BreadcrumbSeparator components
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Breadcrumb navigation element

    Example:
        Breadcrumb(
            BreadcrumbItem("Home", href="/"),
            BreadcrumbSeparator(),
            BreadcrumbItem("Products", href="/products"),
            BreadcrumbSeparator(),
            BreadcrumbItem("Shoes", current=True),
        )
    """
    return Nav(
        Ol(
            *children,
            cls=cn(
                "text-muted-foreground flex flex-wrap items-center gap-1.5 text-sm break-words sm:gap-2.5",
                cls,
            ),
        ),
        aria_label="Breadcrumb",
        **attrs,
    )


def BreadcrumbItem(
    *children: Any,
    href: str = "",
    current: bool = False,
    cls: str = "",
    **attrs: Any,
) -> Union[TagBuilder, HtmlString]:
    """Individual breadcrumb item.

    Creates a breadcrumb item as either a link (if href provided and not current)
    or as plain text (if current or no href).

    Args:
        *children: Item content (text, icons, etc.)
        href: Link URL (optional, ignored if current=True)
        current: Whether this is the current page (default False)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Breadcrumb item element

    Example:
        # Link item
        BreadcrumbItem("Products", href="/products")

        # Current page (no link)
        BreadcrumbItem("Shoes", current=True)

        # With icon
        BreadcrumbItem(LucideIcon("home"), "Home", href="/")
    """
    if current:
        # Current page - styled text, no link
        return Li(
            Span(
                *children,
                cls=cn("text-foreground font-normal", cls),
                aria_current="page",
            ),
            cls="inline-flex items-center gap-1.5",
            role="link",
            **attrs,
        )
    elif href:
        # Link item
        return Li(
            A(
                *children,
                href=href,
                cls=cn("hover:text-foreground transition-colors", cls),
            ),
            cls="inline-flex items-center gap-1.5",
            **attrs,
        )
    else:
        # Text item without link
        return Li(
            Span(
                *children,
                cls=cn("", cls),
            ),
            cls="inline-flex items-center gap-1.5",
            **attrs,
        )


def BreadcrumbSeparator(
    icon: str = "chevron-right",
    cls: str = "",
    **attrs: Any,
) -> Union[TagBuilder, HtmlString]:
    """Breadcrumb separator element.

    Creates a visual separator between breadcrumb items, typically a chevron icon.

    Args:
        icon: Lucide icon name for separator (default "chevron-right")
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Breadcrumb separator element

    Example:
        # Default chevron separator
        BreadcrumbSeparator()

        # Custom separator
        BreadcrumbSeparator(icon="slash")
    """
    return Li(
        LucideIcon(icon, cls=cn("size-3.5", cls)),
        role="presentation",
        aria_hidden="true",
        **attrs,
    )


def BreadcrumbEllipsis(
    cls: str = "",
    **attrs: Any,
) -> Union[TagBuilder, HtmlString]:
    """Breadcrumb ellipsis for collapsed items.

    Creates an ellipsis indicator for hidden breadcrumb items.
    Useful when the breadcrumb trail is too long.

    Args:
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Breadcrumb ellipsis element

    Example:
        Breadcrumb(
            BreadcrumbItem("Home", href="/"),
            BreadcrumbSeparator(),
            BreadcrumbEllipsis(),
            BreadcrumbSeparator(),
            BreadcrumbItem("Current Page", current=True),
        )
    """
    return Li(
        Span(
            LucideIcon("ellipsis", cls=cn("size-4", cls)),
            cls="flex h-9 w-9 items-center justify-center",
        ),
        cls="inline-flex items-center gap-1.5",
        role="presentation",
        aria_hidden="true",
        **attrs,
    )
