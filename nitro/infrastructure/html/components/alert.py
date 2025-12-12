from typing import Any, Literal
from rusty_tags import Div, H5, P, HtmlString
from .utils import cn, cva

# Alert variant configuration using cva
alert_variants = cva(
    base="alert",
    config={
        "variants": {
            "variant": {
                "default": "alert-default",
                "info": "alert-info",
                "success": "alert-success",
                "warning": "alert-warning",
                "error": "alert-error",
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
    return Div(
        *children,
        role="alert",
        cls=cn(alert_variants(variant=variant), cls),
        data_variant=variant,
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
    return H5(
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
    return Div(
        *children,
        cls=cn("alert-description", cls),
        **attrs,
    )
