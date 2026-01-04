from typing import Any, Literal
from rusty_tags import Div, H2, HtmlString, Section
from .utils import cn, cva
from .icons import LucideIcon

# Alert variant configuration using cva
alert_variants = cva(
    config={
        "variants": {
            "variant": {
                "default": "alert",
                "info": "alert",
                "success": "alert",
                "warning": "alert",
                "error": "alert-destructive",
                "destructive": "alert-destructive",
            },
        },
        "defaultVariants": {"variant": "default"},
    }
)


AlertVariant = Literal["default", "info", "success", "warning", "error", "destructive"]


def Alert(
    *children: Any,
    variant: AlertVariant = "default",
    icon: str|None = None,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Alert component for displaying important messages.

    Alerts are used to communicate a state that affects a system,
    feature, or page. They display contextual feedback messages.

    Args:
        *children: Alert content (typically AlertTitle and AlertDescription)
        variant: Visual style variant
            - "default": Standard alert appearance
            - "info": Informational message
            - "success": Success/positive message
            - "warning": Warning message
            - "error": Error message
            - "destructive": Alias for error (semantic)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered alert element

    Example:
        # Simple alert
        Alert(
            AlertTitle("Heads up!"),
            AlertDescription("You can add components to your app using the cli."),
        )

        # Error alert
        Alert(
            AlertTitle("Error"),
            AlertDescription("Your session has expired. Please log in again."),
            variant="error",
        )

        # Success alert with custom content
        Alert(
            AlertTitle("Success!"),
            AlertDescription("Your changes have been saved."),
            variant="success",
        )
    """
    icon_map = {
        "info": "info",
        "success": "check-circle",
        "warning": "alert-triangle",
        "error": "x-circle",
        "destructive": "trash-2",
        "default": "bell",
    }
    return Div(
        LucideIcon(icon_map[variant] if icon is None else icon, cls="size-4"),

        *children,
        role="alert",
        cls=cn(alert_variants(variant=variant), cls),
        **attrs,
    )


def AlertTitle(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Title element for an alert.

    Args:
        *children: Title content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered alert title

    Example:
        AlertTitle("Warning")
    """
    return H2(
        *children,
        cls=cn("alert-title", cls),
        **attrs,
    )


def AlertDescription(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Description/body text for an alert.

    Args:
        *children: Description content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered alert description

    Example:
        AlertDescription("Please review the form errors before submitting.")
    """
    return Section(
        *children,
        cls=cn("alert-description", cls),
        **attrs,
    )
