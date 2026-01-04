"""Combobox component with search filtering and Datastar reactivity.

A searchable dropdown that combines an input field with a filterable list
of options. Uses the compound component pattern for flexibility.
Uses Basecoat's .select CSS styles for consistent styling.
"""

from itertools import count
from typing import Any, Optional, Callable
import rusty_tags as rt
from rusty_tags.datastar import Signals
from .utils import cn
from .icons import LucideIcon

_combobox_ids = count(1)


def ComboboxItem(
    *children: Any,
    value: str,
    search_text: Optional[str] = None,
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> Callable:
    """Individual item in a combobox dropdown.

    Returns a closure that receives combobox context from parent.
    The item is hidden when the search query doesn't match its text.

    Args:
        *children: Item content (text, icons, etc.)
        value: The value when this item is selected
        search_text: Text to match against search (defaults to children text)
        disabled: Whether the item is disabled
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Closure function for compound component pattern

    Example:
        ComboboxItem("Apple", value="apple")
        ComboboxItem(LucideIcon("star"), "Featured", value="featured")
    """
    # Get display text for matching - use first string child or search_text
    display_text = search_text
    if display_text is None:
        for child in children:
            if isinstance(child, str):
                display_text = child
                break
        if display_text is None:
            display_text = str(value)

    def create_item(combobox_id: str, signal_prefix: str, bind_signal: Optional[str] = None) -> rt.HtmlString:
        open_signal = f"{signal_prefix}_open"
        search_signal = f"{signal_prefix}_search"
        value_signal = f"{signal_prefix}_value"
        display_signal = f"{signal_prefix}_display"

        item_attrs: dict[str, Any] = {
            "role": "option",
            "tabindex": "-1" if disabled else "0",
            "data_value": value,
        }

        if disabled:
            item_attrs["aria_disabled"] = "true"
        else:
            # Build the on-click handler
            # Select this item, set display text, close dropdown, clear search
            click_actions = [
                f"${value_signal} = '{value}'",
                f"${display_signal} = '{display_text}'",
                f"${open_signal} = false",
                f"${search_signal} = ''",
            ]
            # If external binding, also update that
            if bind_signal:
                click_actions.append(f"${bind_signal} = '{value}'")

            item_attrs["on_click"] = "; ".join(click_actions)
            # Keyboard support - Enter to select
            item_attrs["on_keydown"] = "evt.key === 'Enter' && (" + ", ".join(click_actions) + ")"

        # Filter visibility based on search - hide if search doesn't match
        # Escape single quotes in display text for JS
        escaped_text = display_text.lower().replace("'", "\\'")
        item_attrs["data_show"] = f"!${search_signal} || '{escaped_text}'.includes(${search_signal}.toLowerCase())"

        # Add aria-selected based on value
        item_attrs["data-attr:aria-selected"] = f"${value_signal} === '{value}'"

        item_attrs.update(attrs)

        return rt.Div(
            # Check icon for selected state
            rt.Span(
                LucideIcon("check", cls="size-4"),
                cls="mr-2 flex h-4 w-4 items-center justify-center",
                data_class=f"{{'opacity-100': ${value_signal} === '{value}', 'opacity-0': ${value_signal} !== '{value}'}}",
            ),
            *children,
            cls=cn(cls),
            **item_attrs,
        )

    return create_item


def ComboboxGroup(
    *children: Any,
    label: str,
    cls: str = "",
    **attrs: Any,
) -> Callable:
    """Group of combobox items with a label.

    Args:
        *children: ComboboxItem elements in this group
        label: Group label shown above items
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Closure function for compound component pattern

    Example:
        ComboboxGroup(
            ComboboxItem("Apple", value="apple"),
            ComboboxItem("Banana", value="banana"),
            label="Fruits"
        )
    """
    def create_group(combobox_id: str, signal_prefix: str, bind_signal: Optional[str] = None) -> rt.HtmlString:
        # Process children items with context
        processed_children = [
            child(combobox_id, signal_prefix, bind_signal) if callable(child) else child
            for child in children
        ]

        return rt.Div(
            rt.Div(
                label,
                role="heading",
            ),
            *processed_children,
            role="group",
            aria_label=label,
            cls=cn(cls),
            **attrs,
        )

    return create_group


def ComboboxSeparator(
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Visual separator between combobox item groups.

    Args:
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Separator element

    Example:
        Combobox(
            ComboboxItem("Apple", value="apple"),
            ComboboxSeparator(),
            ComboboxItem("Carrot", value="carrot"),
        )
    """
    return rt.Hr(
        role="separator",
        cls=cn(cls),
        **attrs,
    )


def Combobox(
    *children: Any,
    id: Optional[str] = None,
    placeholder: str = "Search...",
    empty_text: str = "No results found",
    bind: Any = None,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Combobox container with search input and filterable dropdown.

    Uses Datastar signals for:
    - open state (whether dropdown is visible)
    - search query (filter text)
    - selected value (current selection)
    - display text (shown in trigger button)

    The filtering is done client-side using Datastar data_show expressions.
    Uses Basecoat's .select CSS classes for consistent styling with other form elements.

    Args:
        *children: ComboboxItem elements
        id: Unique identifier (auto-generated if not provided)
        placeholder: Placeholder text for search input
        empty_text: Text to show when no items match the search
        bind: Optional Datastar Signal for two-way binding of selected value
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Complete combobox structure with signal coordination

    Example:
        Combobox(
            ComboboxItem("Apple", value="apple"),
            ComboboxItem("Banana", value="banana"),
            ComboboxItem("Orange", value="orange"),
            id="fruits",
            placeholder="Select a fruit...",
        )

        # With Datastar binding
        form = Signals(fruit="")
        Combobox(
            ComboboxItem("Apple", value="apple"),
            ComboboxItem("Banana", value="banana"),
            id="fruits",
            bind=form.fruit,
        )
    """
    combobox_id = id or f"combobox_{next(_combobox_ids)}"
    signal_prefix = combobox_id.replace("-", "_")
    open_signal = f"{signal_prefix}_open"
    search_signal = f"{signal_prefix}_search"
    value_signal = f"{signal_prefix}_value"
    display_signal = f"{signal_prefix}_display"

    # Handle external binding
    bind_signal = None
    if bind is not None:
        if hasattr(bind, 'to_js'):
            bind_signal = bind.to_js().lstrip('$')
        elif isinstance(bind, str):
            bind_signal = bind.lstrip('$')

    # Process children - pass context to closures
    processed_children = []
    for child in children:
        if callable(child):
            processed_children.append(child(combobox_id, signal_prefix, bind_signal))
        else:
            processed_children.append(child)

    # Build the trigger button that shows current selection
    trigger_button = rt.Button(
        rt.Span(
            placeholder,
            cls="truncate text-muted-foreground",
            data_show=f"!${display_signal}",
        ),
        rt.Span(
            cls="truncate",
            data_show=f"${display_signal}",
            data_text=f"${display_signal}",
        ),
        LucideIcon("chevrons-up-down", cls="ml-auto size-4 shrink-0 opacity-50"),
        type="button",
        cls="btn-outline w-full justify-between font-normal",
        role="combobox",
        aria_haspopup="listbox",
        aria_autocomplete="list",
        **{"data-attr:aria-expanded": f"${open_signal}"},
        aria_controls=f"{combobox_id}-listbox",
        on_click=f"${open_signal} = !${open_signal}",
    )

    return rt.Div(
        trigger_button,
        # Dropdown with search and options
        rt.Div(
            # Search header
            rt.Header(
                LucideIcon("search"),
                rt.Input(
                    type="text",
                    placeholder=placeholder,
                    autocomplete="off",
                    data_bind=search_signal,
                    role="combobox",
                    id=f"{combobox_id}-input",
                    autofocus=True,
                ),
            ),
            # Options list
            rt.Div(
                *processed_children,
                role="listbox",
                id=f"{combobox_id}-listbox",
                data_empty=empty_text,
            ),
            data_popover="",
            data_align="start",
            data_side="bottom",
            aria_hidden="true",
            **{"data-attr:aria-hidden": f"!${open_signal}"},
        ),
        # Initialize signals
        signals=Signals(**{
            open_signal: False,
            search_signal: "",
            value_signal: "",
            display_signal: "",
        }),
        cls=cn("select w-full", cls),
        id=combobox_id,
        # Close on click outside
        on_click__outside=f"${open_signal} = false",
        # Close on Escape
        on_keydown=f"evt.key === 'Escape' && (${open_signal} = false)",
        **attrs,
    )
