from typing import Any, Literal
from rusty_tags import Kbd as HTMLKbd, HtmlString
from .utils import cn

KbdSize = Literal["sm", "md", "lg"]


def Kbd(
    *children: Any,
    size: KbdSize = "md",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Keyboard shortcut display component.

    Displays a keyboard key or shortcut in a visual representation
    similar to a physical key. Used to indicate keyboard shortcuts
    or key combinations.

    Args:
        *children: Key content (single key or combination)
        size: Size of the key display
            - "sm": Small size
            - "md": Medium size (default)
            - "lg": Large size
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered keyboard element

    Example:
        # Single key
        Kbd("Esc")

        # Key combination (use multiple Kbd)
        Div(Kbd("Ctrl"), " + ", Kbd("S"))

        # With description
        Span("Press ", Kbd("Enter"), " to submit")

        # Modifier keys
        Kbd("⌘")  # Command key
        Kbd("⇧")  # Shift key
    """
    return HTMLKbd(
        *children,
        cls=cn("kbd", cls),
        data_size=size,
        **attrs,
    )
