from typing import Any, Literal
from rusty_tags import Div, HtmlString
from .utils import cn
from .icons import LucideIcon


SpinnerSize = Literal["sm", "md", "lg"]

# Size mappings for the loader icon
SPINNER_SIZES = {
    "sm": "16",
    "md": "24",
    "lg": "32",
}


def Spinner(
    size: SpinnerSize = "md",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Loading spinner component with animated rotation.

    A visual loading indicator using the Lucide loader-2 icon with
    Tailwind's animate-spin animation.

    Args:
        size: Spinner size
            - "sm": Small (16px)
            - "md": Medium (24px, default)
            - "lg": Large (32px)
        cls: Additional CSS classes (for color, etc.)
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered spinner element

    Example:
        # Default spinner
        Spinner()

        # Large spinner with custom color
        Spinner(size="lg", cls="text-primary")

        # Small muted spinner
        Spinner(size="sm", cls="text-muted-foreground")
    """
    icon_size = SPINNER_SIZES[size]

    return Div(
        LucideIcon(
            "loader-2",
            width=icon_size,
            height=icon_size,
            cls=cn("animate-spin", cls),
        ),
        role="status",
        aria_label="Loading",
        **attrs,
    )
