from typing import Any
from rusty_tags import Div, HtmlString
from .utils import cn


def Skeleton(
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Skeleton loading placeholder component.

    A visual placeholder used to indicate loading state. Uses Tailwind's
    animate-pulse animation to create a subtle pulsing effect.

    Sizing is controlled entirely through Tailwind classes via the cls
    parameter, allowing flexible layouts.

    Args:
        cls: Tailwind classes for sizing and shape
            - Height: "h-4", "h-12", etc.
            - Width: "w-full", "w-[250px]", etc.
            - Border radius: "rounded", "rounded-full", "rounded-xl"
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered skeleton element

    Example:
        # Text line placeholder
        Skeleton(cls="h-4 w-[250px]")

        # Avatar placeholder
        Skeleton(cls="h-12 w-12 rounded-full")

        # Card placeholder
        Skeleton(cls="h-[125px] w-[250px] rounded-xl")

        # Full-width text block
        Skeleton(cls="h-4 w-full")
    """
    return Div(
        cls=cn("animate-pulse bg-muted rounded", cls),
        aria_hidden="true",
        **attrs,
    )
