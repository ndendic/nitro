"""Dropdown Menu component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.responses import HTMLResponse
from fastapi import APIRouter

from nitro.infrastructure.html.components import (
    DropdownMenu,
    DropdownTrigger,
    DropdownContent,
    DropdownItem,
    DropdownSeparator,
    DropdownLabel,
    Button,
    LucideIcon,
)

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        DropdownMenu(
            DropdownTrigger(Button("Options", variant="outline")),
            DropdownContent(
                DropdownItem("Profile"),
                DropdownItem("Settings"),
                DropdownItem("Help"),
            ),
            id="basic-dropdown",
        ),
        cls="flex gap-4"
    )


def example_with_icons():
    return Div(
        DropdownMenu(
            DropdownTrigger(Button("Actions", variant="outline")),
            DropdownContent(
                DropdownItem(LucideIcon("user"), "Profile"),
                DropdownItem(LucideIcon("settings"), "Settings"),
                DropdownItem(LucideIcon("help-circle"), "Help"),
                DropdownSeparator(),
                DropdownItem(LucideIcon("log-out"), "Logout"),
            ),
            id="icons-dropdown",
        ),
        cls="flex gap-4"
    )


def example_with_separators():
    return Div(
        DropdownMenu(
            DropdownTrigger(Button("Edit", variant="outline")),
            DropdownContent(
                DropdownLabel("Edit Actions"),
                DropdownItem("Cut"),
                DropdownItem("Copy"),
                DropdownItem("Paste"),
                DropdownSeparator(),
                DropdownLabel("Selection"),
                DropdownItem("Select All"),
                DropdownItem("Deselect"),
            ),
            id="separators-dropdown",
        ),
        cls="flex gap-4"
    )


def example_alignment():
    return Div(
        DropdownMenu(
            DropdownTrigger(Button("Start (default)", variant="outline")),
            DropdownContent(
                DropdownItem("Option 1"),
                DropdownItem("Option 2"),
                DropdownItem("Option 3"),
                align="start",
            ),
            id="align-start-dropdown",
        ),
        DropdownMenu(
            DropdownTrigger(Button("Center", variant="outline")),
            DropdownContent(
                DropdownItem("Option 1"),
                DropdownItem("Option 2"),
                DropdownItem("Option 3"),
                align="center",
            ),
            id="align-center-dropdown",
        ),
        DropdownMenu(
            DropdownTrigger(Button("End", variant="outline")),
            DropdownContent(
                DropdownItem("Option 1"),
                DropdownItem("Option 2"),
                DropdownItem("Option 3"),
                align="end",
            ),
            id="align-end-dropdown",
        ),
        cls="flex gap-4 flex-wrap"
    )


def example_disabled_items():
    return Div(
        DropdownMenu(
            DropdownTrigger(Button("With Disabled", variant="outline")),
            DropdownContent(
                DropdownItem("Available action"),
                DropdownItem("Another available action"),
                DropdownItem("Disabled action", disabled=True),
                DropdownItem("Also disabled", disabled=True),
            ),
            id="disabled-dropdown",
        ),
        cls="flex gap-4"
    )


def example_with_click_handlers():
    return Div(
        DropdownMenu(
            DropdownTrigger(Button("Click Actions", variant="outline")),
            DropdownContent(
                DropdownItem("Show Alert", on_click="alert('Hello!')"),
                DropdownItem("Log to Console", on_click="console.log('Clicked!')"),
            ),
            id="click-dropdown",
        ),
        P("Open the dropdown and click an item to see the action.", cls="text-muted-foreground text-sm mt-4"),
        cls="flex flex-col gap-4"
    )


@router.get("/xtras/dropdown")
@template(title="Dropdown Menu Component Documentation")
def dropdown_docs():
    return Div(
        H1("Dropdown Menu Component"),
        P(
            "A compound component for building accessible dropdown menus. Uses Datastar signals "
            "for state management and Basecoat CSS for styling. Supports icons, separators, "
            "disabled items, and different alignment options."
        ),
        Section(
            "Basic Dropdown",
            P("A simple dropdown menu with trigger and content:"),
            ComponentShowcase(example_basic),
        ),
        Section(
            "With Icons",
            P("Dropdown items can include icons using LucideIcon:"),
            ComponentShowcase(example_with_icons),
        ),
        Section(
            "With Separators and Labels",
            P("Group related items using separators and non-interactive labels:"),
            ComponentShowcase(example_with_separators),
        ),
        Section(
            "Alignment Options",
            P("Control horizontal alignment of the dropdown content:"),
            ComponentShowcase(example_alignment),
        ),
        Section(
            "Disabled Items",
            P("Items can be disabled to prevent interaction:"),
            ComponentShowcase(example_disabled_items),
        ),
        Section(
            "Click Handlers",
            P("Add click handlers to perform actions:"),
            ComponentShowcase(example_with_click_handlers),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
# DropdownMenu - Container component
def DropdownMenu(
    *children,                   # DropdownTrigger and DropdownContent
    id: str = "",                # Unique identifier (auto-generated if not provided)
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString

# DropdownTrigger - Button that opens the menu (closure pattern)
def DropdownTrigger(
    *children,                   # Trigger content (typically a Button)
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> Callable

# DropdownContent - Menu content container (closure pattern)
def DropdownContent(
    *children,                   # Menu items
    align: str = "start",        # Alignment: "start", "center", "end"
    side: str = "bottom",        # Side: "bottom", "top", "left", "right"
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> Callable

# DropdownItem - Individual menu item
def DropdownItem(
    *children,                   # Item content (text, icons, etc.)
    on_click: str = None,        # Datastar on_click handler
    disabled: bool = False,      # Whether item is disabled
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString

# DropdownSeparator - Visual divider between groups
def DropdownSeparator(
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString

# DropdownLabel - Non-interactive heading for groups
def DropdownLabel(
    *children,                   # Label content
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Key Behaviors",
            Ul(
                Li("Opens on trigger click"),
                Li("Closes on click outside"),
                Li("Closes on Escape key"),
                Li("ARIA attributes for accessibility"),
                Li("CSS-based positioning via Basecoat popover styles"),
            ),
        ),
        BackLink(),
    )
