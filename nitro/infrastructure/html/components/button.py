from typing import Any, Literal
from rusty_tags import Button as HTMLButton, HtmlString
from .utils import cn, cva

# Button variant configuration using cva
button_variants = cva(
    base="btn",
    config={
        "variants": {
            "variant": {
                "default": "btn-default",
                "primary": "btn-primary",
                "secondary": "btn-secondary",
                "ghost": "btn-ghost",
                "destructive": "btn-destructive",
                "outline": "btn-outline",
                "link": "btn-link",
            },
            "size": {
                "sm": "btn-sm",
                "md": "btn-md",
                "lg": "btn-lg",
                "icon": "btn-icon",
            },
        },
        "defaultVariants": {"variant": "default", "size": "md"},
    }
)


ButtonVariant = Literal["default", "primary", "secondary", "ghost", "destructive", "outline", "link"]
ButtonSize = Literal["sm", "md", "lg", "icon"]


def Button(
    *children: Any,
    variant: ButtonVariant = "default",
    size: ButtonSize = "md",
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Button component with variant styling.

    A versatile button component that supports multiple visual variants
    and sizes. Uses semantic class names with data attributes for styling.

    Args:
        *children: Button content (text, icons, etc.)
        variant: Visual style variant
            - "default": Standard button appearance
            - "primary": Primary action emphasis
            - "secondary": Secondary/less prominent action
            - "ghost": Minimal/transparent background
            - "destructive": Dangerous/delete actions
            - "outline": Border-only style
            - "link": Appears as a link
        size: Button size
            - "sm": Small button
            - "md": Medium button (default)
            - "lg": Large button
            - "icon": Square button for icons only
        disabled: Whether the button is disabled
        cls: Additional CSS classes (merged with base classes)
        **attrs: Additional HTML attributes passed through

    Returns:
        HtmlString: Rendered button element

    Example:
        # Basic button
        Button("Click me")

        # Primary action button
        Button("Save", variant="primary")

        # Destructive button
        Button("Delete", variant="destructive", size="sm")

        # Icon button
        Button(LucideIcon("plus"), variant="ghost", size="icon")

        # With additional attributes
        Button("Submit", type="submit", form="my-form")
    """
    return HTMLButton(
        *children,
        disabled=disabled,
        cls=cn(button_variants(variant=variant, size=size), cls),
        data_variant=variant,
        data_size=size,
        **attrs,
    )


def ButtonGroup(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Container for grouping related buttons.

    Provides visual grouping of buttons, typically with connected borders.

    Args:
        *children: Button components to group
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered button group container

    Example:
        ButtonGroup(
            Button("Left"),
            Button("Center"),
            Button("Right"),
        )
    """
    from rusty_tags import Div

    return Div(
        *children,
        role="group",
        cls=cn("btn-group", cls),
        **attrs,
    )
