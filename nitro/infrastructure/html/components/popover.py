"""Popover component with Datastar reactivity.

A compound component for building positioned overlay containers using the
closure pattern for signal coordination between trigger and content.
"""

from itertools import count
from typing import Any, Optional, Callable
import rusty_tags as rt
from rusty_tags.datastar import Signals
from .utils import cn


_popover_ids = count(1)


def Popover(
    *children: Any,
    id: Optional[str] = None,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Popover container with signal state management.

    Uses Datastar signals for open/close state. The popover uses CSS-based
    positioning via Basecoat's popover styles with `data-popover` attribute.

    Args:
        *children: PopoverTrigger and PopoverContent components
        id: Unique identifier (auto-generated if not provided)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Complete popover structure with signal coordination

    Example:
        Popover(
            PopoverTrigger(Button("Open Popover")),
            PopoverContent(
                H4("Settings"),
                P("Configure your preferences here."),
                side="bottom",
                align="start",
            ),
            id="settings-popover",
        )
    """
    popover_id = id or f"popover_{next(_popover_ids)}"
    signal_name = f"{popover_id.replace('-', '_')}_open"

    # Process children by calling closures with context
    processed_children = [
        child(popover_id, signal_name) if callable(child) else child
        for child in children
    ]

    return rt.Div(
        *processed_children,
        signals=Signals(**{signal_name: False}),
        cls=cn("popover", cls),
        id=popover_id,
        # Close on click outside - when clicking the wrapper itself (not children)
        on_click__outside=f"${signal_name} = false",
        **attrs,
    )


def PopoverTrigger(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> Callable:
    """Trigger element that toggles the popover.

    Returns a closure that receives popover context from parent.

    Args:
        *children: Trigger content (typically a Button component)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Closure function for compound component pattern

    Example:
        PopoverTrigger(Button("Open Popover", variant="outline"))
    """
    def create_trigger(popover_id: str, signal_name: str) -> rt.HtmlString:
        return rt.Span(
            *children,
            cls=cn("popover-trigger", cls),
            on_click=f"${signal_name} = !${signal_name}",
            aria_haspopup="dialog",
            aria_expanded="false",  # Initial value
            **{"data-attr:aria-expanded": f"${signal_name}"},  # Dynamic update
            **attrs,
        )

    return create_trigger


def PopoverContent(
    *children: Any,
    side: str = "bottom",
    align: str = "center",
    cls: str = "",
    **attrs: Any,
) -> Callable:
    """Content container for the popover overlay.

    Returns a closure that receives popover context from parent.
    Uses Basecoat's `data-popover` styling for positioning and animations.

    Args:
        *children: Any content (text, forms, other components, including PopoverClose)
        side: Which side to appear - "bottom", "top", "left", "right"
        align: Alignment relative to trigger - "start", "center", "end"
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Closure function for compound component pattern

    Example:
        PopoverContent(
            H4("Settings"),
            P("Configure your preferences."),
            side="bottom",
            align="start",
        )
    """
    def create_content(popover_id: str, signal_name: str) -> rt.HtmlString:
        # Process any child closures (like PopoverClose) with the signal context
        processed_children = [
            child(popover_id, signal_name) if callable(child) else child
            for child in children
        ]

        return rt.Div(
            *processed_children,
            cls=cn(cls),
            role="dialog",
            data_popover="",
            data_side=side,
            data_align=align,
            aria_labelledby=f"{popover_id}-title",
            tabindex="-1",
            # Show/hide based on signal - initial value is hidden
            aria_hidden="true",
            **{"data-attr:aria-hidden": f"!${signal_name}"},  # Dynamic update
            # Close on Escape key
            on_keydown=f"evt.key === 'Escape' && (${signal_name} = false)",
            **attrs,
        )

    return create_content


def PopoverClose(
    *children: Any,
    popover_id: str,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Close button for the popover content.

    A non-closure component that explicitly takes the popover_id to create
    the close button. This allows it to be placed anywhere in the DOM tree.

    Args:
        *children: Close button content (text, icon, etc.)
        popover_id: The id of the parent Popover component
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Button element that closes the popover

    Example:
        Popover(
            PopoverTrigger(Button("Open")),
            PopoverContent(
                Div(
                    H4("Title"),
                    PopoverClose(LucideIcon("x"), popover_id="my-popover"),
                ),
            ),
            id="my-popover",
        )
    """
    signal_name = f"{popover_id.replace('-', '_')}_open"
    return rt.Button(
        *children,
        cls=cn("popover-close", cls),
        on_click=f"${signal_name} = false",
        aria_label="Close",
        type="button",
        **attrs,
    )
