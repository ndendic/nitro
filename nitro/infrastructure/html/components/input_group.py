"""Input Group component - Input with left/right decorative elements."""

from typing import Any, Optional, Union
from rusty_tags import Div, HtmlString
from .utils import cn


def InputGroup(
    input_element: HtmlString,
    left: Optional[Union[str, HtmlString, Any]] = None,
    right: Optional[Union[str, HtmlString, Any]] = None,
    left_interactive: bool = False,
    right_interactive: bool = False,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Container for input with left/right decorative elements.

    Uses BasecoatUI's absolute positioning pattern. Creates a relative container
    with the input and optional absolutely-positioned left/right elements.

    Args:
        input_element: The input element (should have cls="input" and appropriate padding)
        left: Optional content for left side (text, icon, etc.)
        right: Optional content for right side (text, icon, etc.)
        left_interactive: If True, left element can be clicked (removes pointer-events-none)
        right_interactive: If True, right element can be clicked (removes pointer-events-none)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered input group container

    Example:
        # Input with dollar prefix
        InputGroup(
            Input(type="number", id="price", placeholder="0.00", cls="input pl-9"),
            left="$"
        )

        # Search input with icon
        InputGroup(
            Input(type="text", id="search", placeholder="Search...", cls="input pl-9"),
            left=LucideIcon("search", cls="w-4 h-4")
        )

        # Input with suffix
        InputGroup(
            Input(type="text", id="website", placeholder="example", cls="input pr-16"),
            right=".com"
        )

        # Both left and right
        InputGroup(
            Input(type="text", id="url", placeholder="example.com", cls="input pl-20 pr-14"),
            left="https://",
            right="/path"
        )

        # Interactive right element
        InputGroup(
            Input(type="text", id="search", placeholder="Search...", cls="input pl-9 pr-20"),
            left=LucideIcon("search", cls="w-4 h-4"),
            right=Button("Search", cls="btn-sm"),
            right_interactive=True
        )
    """
    children = [input_element]

    # Add left element if provided
    if left is not None:
        left_el = Div(
            left,
            cls=cn(
                "absolute left-3 top-1/2 -translate-y-1/2",
                "flex items-center justify-center",
                "text-muted-foreground text-sm",
                "[&>svg]:size-4",
                "pointer-events-none" if not left_interactive else "",
            ),
        )
        children.append(left_el)

    # Add right element if provided
    if right is not None:
        right_el = Div(
            right,
            cls=cn(
                "absolute right-3 top-1/2 -translate-y-1/2",
                "flex items-center justify-center",
                "text-muted-foreground text-sm",
                "[&>svg]:size-4",
                "pointer-events-none" if not right_interactive else "",
            ),
        )
        children.append(right_el)

    return Div(
        *children,
        cls=cn("input-group", "relative", cls),
        **attrs,
    )
