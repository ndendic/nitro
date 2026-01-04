"""Command Palette component with search filtering and keyboard navigation.

A command palette for quick actions and search. Supports grouping,
shortcuts, and keyboard navigation. Uses Basecoat's .command CSS.
"""

from itertools import count
from typing import Any, Optional, Callable
import rusty_tags as rt
from rusty_tags.datastar import Signals
from .utils import cn
from .icons import LucideIcon
from .kbd import Kbd

_command_ids = count(1)


def Command(
    *children: Any,
    id: Optional[str] = None,
    placeholder: str = "Type a command or search...",
    empty_text: str = "No results found",
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Command palette container with search input and filterable items.

    Uses Datastar signals for:
    - search query (filter text)
    - active item index (for keyboard navigation)

    The filtering is done client-side using Datastar data_show expressions.
    Uses Basecoat's .command CSS classes for styling.

    Args:
        *children: CommandGroup, CommandItem, or CommandSeparator elements
        id: Unique identifier (auto-generated if not provided)
        placeholder: Placeholder text for search input
        empty_text: Text to show when no items match the search
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Complete command palette structure

    Example:
        Command(
            CommandGroup(
                CommandItem("New File", shortcut="Ctrl+N"),
                CommandItem("Open File", shortcut="Ctrl+O"),
                heading="File",
            ),
            CommandSeparator(),
            CommandGroup(
                CommandItem("Settings", on_select="openSettings()"),
                heading="Actions",
            ),
            id="cmd",
        )
    """
    command_id = id or f"command_{next(_command_ids)}"
    signal_prefix = command_id.replace("-", "_")
    search_signal = f"{signal_prefix}_search"

    # Process children - pass context to closures
    processed_children = []
    for child in children:
        if callable(child):
            processed_children.append(child(command_id, signal_prefix))
        else:
            processed_children.append(child)

    return rt.Div(
        # Search header
        rt.Header(
            LucideIcon("search"),
            rt.Input(
                type="text",
                placeholder=placeholder,
                autocomplete="off",
                bind=search_signal,
                id=f"{command_id}-input",
                autofocus=True,
            ),
        ),
        # Menu items
        rt.Div(
            *processed_children,
            role="menu",
            id=f"{command_id}-menu",
            data_empty=empty_text,
        ),
        # Initialize signals
        signals=Signals(**{
            search_signal: "",
        }),
        cls=cn("command", cls),
        id=command_id,
        **attrs,
    )


def CommandDialog(
    *children: Any,
    id: Optional[str] = None,
    trigger: Optional[Any] = None,
    placeholder: str = "Type a command or search...",
    empty_text: str = "No results found",
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Command palette in a dialog modal.

    Opens as a modal dialog with backdrop. Can be triggered by a button
    or keyboard shortcut (Ctrl+K / Cmd+K).

    Args:
        *children: CommandGroup, CommandItem, or CommandSeparator elements
        id: Unique identifier (auto-generated if not provided)
        trigger: Optional trigger element (button)
        placeholder: Placeholder text for search input
        empty_text: Text to show when no items match the search
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Command dialog with optional trigger

    Example:
        CommandDialog(
            CommandGroup(
                CommandItem("New File", shortcut="Ctrl+N"),
                heading="File",
            ),
            id="cmd-dialog",
            trigger=Button("Open Command Palette", variant="outline"),
        )
    """
    command_id = id or f"command_dialog_{next(_command_ids)}"
    signal_prefix = command_id.replace("-", "_")
    open_signal = f"{signal_prefix}_open"
    search_signal = f"{signal_prefix}_search"

    # Process children - pass context to closures
    processed_children = []
    for child in children:
        if callable(child):
            processed_children.append(child(command_id, signal_prefix))
        else:
            processed_children.append(child)

    # Build trigger if provided
    trigger_element = None
    if trigger is not None:
        trigger_element = rt.Span(
            trigger,
            on_click=f"${open_signal} = true",
        )

    dialog = rt.Dialog(
        rt.Div(
            # Command content
            rt.Div(
                # Search header
                rt.Header(
                    LucideIcon("search"),
                    rt.Input(
                        type="text",
                        placeholder=placeholder,
                        autocomplete="off",
                        bind=search_signal,
                        id=f"{command_id}-input",
                        autofocus=True,
                    ),
                ),
                # Menu items
                rt.Div(
                    *processed_children,
                    role="menu",
                    id=f"{command_id}-menu",
                    data_empty=empty_text,
                ),
                cls="command",
            ),
        ),
        cls=cn("command-dialog", cls),
        id=command_id,
        open=False,
        **{"data-attr:open": f"${open_signal}"},
        # on_click__outside=f"${open_signal} = false",
        on_keydown=f"evt.key === 'Escape' && (${open_signal} = false)",
        **attrs,
    )

    return rt.Div(
        trigger_element,
        dialog,
        signals=Signals(**{
            open_signal: False,
            search_signal: "",
        }),
    ) if trigger_element else rt.Div(
        dialog,
        signals=Signals(**{
            open_signal: False,
            search_signal: "",
        }),
    )


def CommandGroup(
    *children: Any,
    heading: str = "",
    cls: str = "",
    **attrs: Any,
) -> Callable:
    """Group of command items with an optional heading.

    Groups are hidden when all their items are filtered out.

    Args:
        *children: CommandItem elements in this group
        heading: Optional group heading text
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Closure function for compound component pattern

    Example:
        CommandGroup(
            CommandItem("New File", shortcut="Ctrl+N"),
            CommandItem("Open File", shortcut="Ctrl+O"),
            heading="File",
        )
    """
    def create_group(command_id: str, signal_prefix: str) -> rt.HtmlString:
        # Process children items with context
        processed_children = [
            child(command_id, signal_prefix) if callable(child) else child
            for child in children
        ]

        heading_element = rt.Div(
            heading,
            role="heading",
        ) if heading else None

        return rt.Div(
            heading_element,
            *processed_children,
            role="group",
            aria_label=heading if heading else None,
            cls=cn(cls),
            **attrs,
        )

    return create_group


def CommandItem(
    *children: Any,
    on_select: Optional[str] = None,
    shortcut: Optional[str] = None,
    icon: Optional[str] = None,
    disabled: bool = False,
    search_text: Optional[str] = None,
    cls: str = "",
    **attrs: Any,
) -> Callable:
    """Individual command item in the palette.

    Args:
        *children: Item content (typically text)
        on_select: Datastar expression to run when selected
        shortcut: Keyboard shortcut to display (e.g., "Ctrl+N")
        icon: Lucide icon name to display
        disabled: Whether the item is disabled
        search_text: Custom text for filtering (defaults to children text)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Closure function for compound component pattern

    Example:
        CommandItem("New File", on_select="newFile()", shortcut="Ctrl+N", icon="file-plus")
        CommandItem("Settings", on_select="openSettings()", icon="settings")
    """
    # Get display text for matching
    display_text = search_text
    if display_text is None:
        for child in children:
            if isinstance(child, str):
                display_text = child
                break
        if display_text is None:
            display_text = ""

    def create_item(command_id: str, signal_prefix: str) -> rt.HtmlString:
        search_signal = f"{signal_prefix}_search"

        item_attrs: dict[str, Any] = {
            "role": "menuitem",
            "tabindex": "-1" if disabled else "0",
        }

        if disabled:
            item_attrs["aria_disabled"] = "true"
        elif on_select:
            item_attrs["on_click"] = on_select
            item_attrs["on_keydown"] = "evt.key === 'Enter' && (" + on_select + ")"

        # Filter visibility based on search
        escaped_text = display_text.lower().replace("'", "\\'")
        item_attrs["data_show"] = f"!${search_signal} || '{escaped_text}'.includes(${search_signal}.toLowerCase())"
        # Also set aria-hidden for CSS filtering
        item_attrs["data-attr:aria-hidden"] = f"${search_signal} && !'{escaped_text}'.includes(${search_signal}.toLowerCase())"

        item_attrs.update(attrs)

        # Build item content
        content = []
        if icon:
            content.append(LucideIcon(icon))
        content.extend(children)

        # Add shortcut if provided
        if shortcut:
            content.append(
                rt.Span(
                    *[Kbd(part) for part in shortcut.split("+")],
                    cls="ml-auto flex gap-1 text-xs text-muted-foreground",
                )
            )

        return rt.Div(
            *content,
            cls=cn(cls),
            **item_attrs,
        )

    return create_item


def CommandSeparator(
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Visual separator between command groups.

    Args:
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Separator element

    Example:
        Command(
            CommandGroup(CommandItem("New File"), heading="File"),
            CommandSeparator(),
            CommandGroup(CommandItem("Settings"), heading="Actions"),
        )
    """
    return rt.Hr(
        role="separator",
        cls=cn(cls),
        **attrs,
    )


def CommandEmpty(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Custom empty state when no results match.

    Note: By default, the empty state is handled via CSS and data-empty attribute.
    Use this for custom empty state content.

    Args:
        *children: Content to show when empty
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Empty state element
    """
    return rt.Div(
        *children,
        cls=cn("py-6 text-center text-sm text-muted-foreground", cls),
        role="presentation",
        **attrs,
    )
