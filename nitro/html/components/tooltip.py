"""Tooltip component with pure CSS positioning.

A simple tooltip that appears on hover using Basecoat's data-tooltip pattern.
No JavaScript/Datastar needed - uses CSS :hover and ::before pseudo-element.
"""

from typing import Any, Literal
import rusty_tags as rt
from .utils import cn


TooltipSide = Literal["top", "bottom", "left", "right"]
TooltipAlign = Literal["start", "center", "end"]


def Tooltip(
    *children: Any,
    content: str,
    side: TooltipSide = "top",
    align: TooltipAlign = "center",
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Tooltip component with pure CSS hover behavior.

    Wraps any element to show a tooltip on hover. Uses Basecoat's CSS-only
    tooltip pattern via data attributes - no JavaScript required.

    Args:
        *children: Element(s) to attach tooltip to (button, icon, text, etc.)
        content: Tooltip text to display on hover
        side: Which side to show tooltip
            - "top": Above the element (default)
            - "bottom": Below the element
            - "left": To the left of the element
            - "right": To the right of the element
        align: Alignment relative to trigger
            - "start": Align to start edge
            - "center": Center aligned (default)
            - "end": Align to end edge
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Span wrapper with tooltip data attributes

    Example:
        # Basic tooltip
        Tooltip(
            Button("Save"),
            content="Save your changes",
        )

        # Icon with tooltip
        Tooltip(
            LucideIcon("info"),
            content="More information",
            side="right",
        )

        # Button with bottom tooltip
        Tooltip(
            Button("Delete", variant="destructive"),
            content="Permanently delete this item",
            side="bottom",
            align="start",
        )
    """
    return rt.Span(
        *children,
        cls=cn(cls),
        data_tooltip=content,
        data_side=side,
        data_align=align,
        **attrs,
    )
