"""Input Group component - Input with prefix/suffix elements."""

from typing import Any
from rusty_tags import Div, Span, HtmlString
from .utils import cn


def InputGroup(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Container for input with prefix/suffix elements.

    Use with InputPrefix and InputSuffix to add icons, text, or other
    elements to the sides of an input. Uses Tailwind utility classes
    for styling.

    Args:
        *children: InputPrefix, Input, InputSuffix elements
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered input group container

    Example:
        # Input with dollar prefix
        InputGroup(
            InputPrefix("$"),
            Input(type="number", id="price", placeholder="0.00"),
        )

        # Search input with icon
        InputGroup(
            InputPrefix(LucideIcon("search")),
            Input(type="text", id="search", placeholder="Search..."),
        )

        # Input with suffix
        InputGroup(
            Input(type="text", id="website", placeholder="example"),
            InputSuffix(".com"),
        )

        # Both prefix and suffix
        InputGroup(
            InputPrefix("https://"),
            Input(type="text", id="url", placeholder="example.com"),
            InputSuffix("/path"),
        )
    """
    return Div(
        *children,
        cls=cn(
            "input-group",
            "flex items-stretch",
            # Handle border radius on first/last children
            "[&>*:first-child]:rounded-l-md [&>*:first-child]:rounded-r-none",
            "[&>*:last-child]:rounded-r-md [&>*:last-child]:rounded-l-none",
            "[&>*:not(:first-child):not(:last-child)]:rounded-none",
            # Remove double borders between adjacent elements
            "[&>*:not(:first-child)]:border-l-0",
            # Make input fill available space
            "[&>input]:flex-1 [&>input]:min-w-0",
            cls,
        ),
        **attrs,
    )


def InputPrefix(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Prefix element for InputGroup.

    Displays content (text, icon, etc.) before the input.

    Args:
        *children: Content to display in prefix (text, icons, etc.)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered prefix element

    Example:
        InputPrefix("$")
        InputPrefix(LucideIcon("mail"))
        InputPrefix("https://")
    """
    return Span(
        *children,
        cls=cn(
            "input-prefix",
            "inline-flex items-center justify-center",
            "px-3 py-1.5",
            "border border-input bg-muted/50",
            "text-muted-foreground text-sm",
            "select-none",
            cls,
        ),
        **attrs,
    )


def InputSuffix(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Suffix element for InputGroup.

    Displays content (text, icon, etc.) after the input.

    Args:
        *children: Content to display in suffix (text, icons, etc.)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered suffix element

    Example:
        InputSuffix(".00")
        InputSuffix(".com")
        InputSuffix(LucideIcon("eye"))
    """
    return Span(
        *children,
        cls=cn(
            "input-suffix",
            "inline-flex items-center justify-center",
            "px-3 py-1.5",
            "border border-input bg-muted/50",
            "text-muted-foreground text-sm",
            "select-none",
            cls,
        ),
        **attrs,
    )
