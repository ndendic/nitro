"""Dropdown Menu component with Datastar reactivity.

A compound component for building accessible dropdown menus using the
closure pattern for signal coordination between trigger, content, and items.
"""

from itertools import count
from typing import Any, Optional, Callable
import rusty_tags as rt
from rusty_tags.datastar import Signals
from .utils import cn, uniq


_dropdown_ids = count(1)


def DropdownMenu(
    *children: Any,
    id: Optional[str] = None,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Dropdown menu container with signal state management.

    Uses Datastar signals for open/close state. The dropdown uses CSS-based
    positioning via Basecoat's popover styles with `data-popover` attribute.

    Args:
        *children: DropdownTrigger and DropdownContent components
        id: Unique identifier (auto-generated if not provided)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Complete dropdown structure with signal coordination

    Example:
        DropdownMenu(
            DropdownTrigger(Button("Options", variant="outline")),
            DropdownContent(
                DropdownItem("Edit", on_click="handleEdit()"),
                DropdownSeparator(),
                DropdownItem("Delete", on_click="handleDelete()"),
            ),
            id="options-menu",
        )
    """
    dropdown_id = id or f"dropdown_{next(_dropdown_ids)}"
    signal_name = f"{dropdown_id.replace('-', '_')}_open"

    # Process children by calling closures with context
    processed_children = [
        child(dropdown_id, signal_name) if callable(child) else child
        for child in children
    ]

    return rt.Div(
        *processed_children,
        signals=Signals(**{signal_name: False}),
        cls=cn("dropdown-menu", cls),
        id=dropdown_id,
        # Close on click outside - when clicking the wrapper itself (not children)
        on_click__outside=f"${signal_name} = false",
        **attrs,
    )


def DropdownTrigger(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> Callable:
    """Trigger button that toggles the dropdown menu.

    Returns a closure that receives dropdown context from parent.

    Args:
        *children: Trigger content (typically a Button component)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Closure function for compound component pattern

    Example:
        DropdownTrigger(Button("Options", variant="outline"))
    """
    def create_trigger(dropdown_id: str, signal_name: str) -> rt.HtmlString:
        # If children is a single Button, we need to wrap it and pass click handler
        # For simplicity, we wrap in a span with click handling
        return rt.Span(
            *children,
            cls=cn("dropdown-trigger", cls),
            on_click=f"${signal_name} = !${signal_name}",
            aria_haspopup="menu",
            aria_expanded="false",  # Initial value
            **{"data-attr:aria-expanded": f"${signal_name}"},  # Dynamic update
            **attrs,
        )

    return create_trigger


def DropdownContent(
    *children: Any,
    align: str = "start",
    side: str = "bottom",
    cls: str = "",
    **attrs: Any,
) -> Callable:
    """Content container for dropdown menu items.

    Returns a closure that receives dropdown context from parent.
    Uses Basecoat's `data-popover` styling for positioning and animations.

    Args:
        *children: DropdownItem, DropdownSeparator, or other elements
        align: Horizontal alignment - "start", "center", or "end"
        side: Which side to appear - "bottom", "top", "left", "right"
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Closure function for compound component pattern

    Example:
        DropdownContent(
            DropdownItem("Edit"),
            DropdownItem("Delete"),
            align="end",
        )
    """
    def create_content(dropdown_id: str, signal_name: str) -> rt.HtmlString:
        return rt.Div(
            *children,
            cls=cn(cls),
            role="menu",
            data_popover="",
            data_align=align,
            data_side=side,
            aria_labelledby=f"{dropdown_id}-trigger",
            tabindex="-1",
            # Show/hide based on signal - initial value is hidden
            aria_hidden="true",
            **{"data-attr:aria-hidden": f"!${signal_name}"},  # Dynamic update
            # Close on Escape key
            on_keydown=f"evt.key === 'Escape' && (${signal_name} = false)",
            **attrs,
        )

    return create_content


def DropdownItem(
    *children: Any,
    on_click: Optional[str] = None,
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Individual menu item within a dropdown.

    Args:
        *children: Item content (text, icons, etc.)
        on_click: Datastar on_click handler expression
        disabled: Whether the item is disabled
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Menu item element

    Example:
        DropdownItem("Edit", on_click="handleEdit()")
        DropdownItem(LucideIcon("trash"), "Delete", on_click="handleDelete()")
        DropdownItem("Disabled Option", disabled=True)
    """
    item_attrs: dict[str, Any] = {
        "role": "menuitem",
        "tabindex": "-1" if disabled else "0",
        "cls": cn(cls),
    }

    if disabled:
        item_attrs["aria_disabled"] = "true"

    if on_click and not disabled:
        item_attrs["on_click"] = on_click

    item_attrs.update(attrs)

    return rt.Div(*children, **item_attrs)


def DropdownSeparator(
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Visual separator between menu item groups.

    Args:
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Separator element

    Example:
        DropdownContent(
            DropdownItem("Edit"),
            DropdownSeparator(),
            DropdownItem("Delete"),
        )
    """
    return rt.Hr(
        role="separator",
        cls=cn(cls),
        **attrs,
    )


def DropdownLabel(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Non-interactive label/heading for a group of menu items.

    Args:
        *children: Label content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Label element

    Example:
        DropdownContent(
            DropdownLabel("Actions"),
            DropdownItem("Edit"),
            DropdownItem("Delete"),
        )
    """
    return rt.Div(
        *children,
        role="heading",
        cls=cn(cls),
        **attrs,
    )
