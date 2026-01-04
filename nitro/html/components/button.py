from typing import Any, Literal
from rusty_tags import Button as HTMLButton, HtmlString
from .utils import cn, cva

# Button variant configuration using cva
button_variants = cva(
    config={
        "base": "",
        "variants": {
            "variant": {
                "default": "btn",
                "primary": "btn-primary",
                "secondary": "btn-secondary",
                "outline": "btn-outline",
                "ghost": "btn-ghost",
                "link": "btn-link",
                "destructive": "btn-destructive",
                "sm": "btn-sm",
                "sm-primary": "btn-sm-primary",
                "sm-secondary": "btn-sm-secondary",
                "sm-outline": "btn-sm-outline",
                "sm-ghost": "btn-sm-ghost",
                "sm-link": "btn-sm-link",
                "sm-destructive": "btn-sm-destructive",
                "lg": "btn-lg",
                "lg-primary": "btn-lg-primary",
                "lg-secondary": "btn-lg-secondary",
                "lg-outline": "btn-lg-outline",
                "lg-ghost": "btn-lg-ghost",
                "lg-link": "btn-lg-link",
                "lg-destructive": "btn-lg-destructive",
                "icon": "btn-icon",
                "icon-primary": "btn-icon-primary",
                "icon-secondary": "btn-icon-secondary",
                "icon-outline": "btn-icon-outline",
                "icon-ghost": "btn-icon-ghost",
                "icon-link": "btn-icon-link",
                "icon-destructive": "btn-icon-destructive",
                "sm-icon": "btn-sm-icon",
                "sm-icon-primary": "btn-sm-icon-primary",
                "sm-icon-secondary": "btn-sm-icon-secondary",
                "sm-icon-outline": "btn-sm-icon-outline",
                "sm-icon-ghost": "btn-sm-icon-ghost",
                "sm-icon-link": "btn-sm-icon-link",
                "sm-icon-destructive": "btn-sm-icon-destructive",
                "lg-icon": "btn-lg-icon",
                "lg-icon-primary": "btn-lg-icon-primary",
                "lg-icon-secondary": "btn-lg-icon-secondary",
                "lg-icon-outline": "btn-lg-icon-outline",
                "lg-icon-ghost": "btn-lg-icon-ghost",
                "lg-icon-link": "btn-lg-icon-link",
                "lg-icon-destructive": "btn-lg-icon-destructive",
            },
            "size": {
                "default": "",
                "sm": "btn-sm",
                "md": "btn-md",
                "lg": "btn-lg",
                "icon": "btn-icon",
            },
        },
        "defaultVariants": {"variant": "default", "size": "default"},
    }
)


ButtonVariant = Literal["default", "primary", "secondary", "ghost", "destructive", "outline", "link", "sm", "sm-primary", "sm-secondary", "sm-outline", "sm-ghost", "sm-link", "sm-destructive", "lg", "lg-primary", "lg-secondary", "lg-outline", "lg-ghost", "lg-link", "lg-destructive", "icon", "icon-primary", "icon-secondary", "icon-outline", "icon-ghost", "icon-link", "icon-destructive", "sm-icon", "sm-icon-primary", "sm-icon-secondary", "sm-icon-outline", "sm-icon-ghost", "sm-icon-link", "sm-icon-destructive", "lg-icon", "lg-icon-primary", "lg-icon-secondary", "lg-icon-outline", "lg-icon-ghost", "lg-icon-link", "lg-icon-destructive"]
ButtonSize = Literal["default", "sm", "md", "lg", "icon"]


def Button(
    *children: Any,
    variant: ButtonVariant = "default",
    size: ButtonSize = "default",
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
            - "default": Default size (no prefix)
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
        cls=cn(button_variants(variant=variant), cls),
        data_variant=variant,
        data_size=size,
        **attrs,
    )

ButtonGroupOrientation = Literal["horizontal", "vertical"]

def ButtonGroup(
    *children: Any,
    cls: str = "",
    orientation: ButtonGroupOrientation = "horizontal",
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
        cls=cn("button-group", cls),
        data_orientation=orientation,
        **attrs,
    )
