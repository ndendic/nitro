from typing import Any, Literal
from rusty_tags import Span, HtmlString
from .utils import cn, cva

# Badge variant configuration using cva
badge_variants = cva(
    base="",
    config={
        "variants": {
            "variant": {
                "default": "badge",
                "primary": "badge-primary",
                "secondary": "badge-secondary",
                "destructive": "badge-destructive",
                "outline": "badge-outline",
            },
            "size": {
                "sm": "badge-sm",
                "md": "badge-md",
                "lg": "badge-lg",
            },
        },
        "defaultVariants": {"variant": "default", "size": "md"},
    }
)


BadgeVariant = Literal["default", "primary", "secondary", "destructive", "outline"]
BadgeSize = Literal["sm", "md", "lg"]


def Badge(
    *children: Any,
    variant: BadgeVariant = "default",
    size: BadgeSize = "md",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Badge component for displaying status, labels, or counts.

    A small visual indicator typically used to highlight status,
    categories, or counts alongside other content.

    Args:
        *children: Badge content (text, icons, etc.)
        variant: Visual style variant
            - "default": Standard badge appearance
            - "primary": Primary emphasis
            - "secondary": Less prominent
            - "destructive": Error/danger status
            - "outline": Border-only style
        size: Badge size
            - "sm": Small badge
            - "md": Medium badge (default)
            - "lg": Large badge
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered badge element

    Example:
        # Status badge
        Badge("Active", variant="outline")

        # Count badge
        Badge("99+", variant="destructive")

        # Label badge
        Badge("New", variant="primary", size="sm")

        # Category badge
        Badge("Documentation", variant="secondary")
    """
    return Span(
        *children,
        cls=cn(badge_variants(variant=variant, size=size), cls),
        data_variant=variant,
        data_size=size,
        **attrs,
    )
