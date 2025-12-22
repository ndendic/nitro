"""
Sidebar component documentation page.

Demonstrates the Sidebar component with Datastar reactivity for state management.
"""

from fastapi import APIRouter
from nitro.infrastructure.events import on, emit_elements
from pages.templates.base import (
    template,
    TitledSection,
    ComponentShowcase,
    Div,
    H1,
    H2,
    H3,
    P,
    A,
    Span,
    Code,
    Fragment,
    Sidebar,
    SidebarHeader,
    SidebarContent,
    SidebarFooter,
    SidebarNav,
    SidebarGroup,
    SidebarGroupLabel,
    SidebarItem,
    SidebarCollapsible,
    SidebarSeparator,
    SidebarToggle,
    Button,
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
    Badge,
    LucideIcon,
)

router = APIRouter()
page = "sidebar"

# Example functions for ComponentShowcase

def basic_sidebar_example():
    """Basic sidebar structure."""
    return Div(
        P(
            "This page already uses the Sidebar component! Check the left side of the screen.",
            cls="text-muted-foreground mb-4",
        ),
        Div(
            Code(
                """
Sidebar(
    SidebarHeader(H3("Navigation")),
    SidebarContent(
        SidebarNav(
            SidebarGroup(
                SidebarGroupLabel("Main"),
                SidebarItem("Home", href="/", icon="home"),
                SidebarItem("Dashboard", href="/dashboard", icon="layout-dashboard"),
            ),
        ),
    ),
    SidebarFooter(P("Footer content")),
    default_open=True,
)
""",
                cls="block whitespace-pre text-sm",
            ),
            cls="bg-muted p-4 rounded-lg font-mono",
        ),
    )


def toggle_example():
    """Sidebar toggle button."""
    return Div(
        Div(
            SidebarToggle(target_signal="sidebar_1"),
            SidebarToggle(icon="menu", target_signal="sidebar_1", cls="ml-2"),
            SidebarToggle(
                Span("Toggle Sidebar"),
                target_signal="sidebar_1",
                cls="ml-2",
            ),
            cls="flex items-center gap-2 flex-wrap",
        ),
        P(
            "Click any button above to toggle the main sidebar.",
            cls="text-muted-foreground text-sm mt-2",
        ),
    )


def nav_groups_example():
    """Navigation groups with labels."""
    return Card(
        CardContent(
            Div(
                Div(
                    H3("Getting Started", cls="text-sm font-medium text-muted-foreground mb-2"),
                    Div(
                        A(
                            LucideIcon("book-open", cls="w-4 h-4"),
                            Span("Introduction"),
                            cls="flex items-center gap-2 p-2 rounded hover:bg-accent",
                            href="#",
                        ),
                        A(
                            LucideIcon("download", cls="w-4 h-4"),
                            Span("Installation"),
                            cls="flex items-center gap-2 p-2 rounded hover:bg-accent",
                            href="#",
                        ),
                        cls="space-y-1",
                    ),
                    cls="mb-4",
                ),
                Div(
                    H3("Components", cls="text-sm font-medium text-muted-foreground mb-2"),
                    Div(
                        A(
                            LucideIcon("square", cls="w-4 h-4"),
                            Span("Button"),
                            cls="flex items-center gap-2 p-2 rounded hover:bg-accent",
                            href="#",
                        ),
                        A(
                            LucideIcon("credit-card", cls="w-4 h-4"),
                            Span("Card"),
                            cls="flex items-center gap-2 p-2 rounded hover:bg-accent",
                            href="#",
                        ),
                        A(
                            LucideIcon("message-square", cls="w-4 h-4"),
                            Span("Dialog"),
                            cls="flex items-center gap-2 p-2 rounded hover:bg-accent",
                            href="#",
                        ),
                        cls="space-y-1",
                    ),
                ),
                cls="p-4",
            ),
        ),
        cls="max-w-xs",
    )


def collapsible_example():
    """Collapsible navigation sections."""
    return Card(
        CardContent(
            Div(
                Div(
                    Div(
                        LucideIcon("shield", cls="w-4 h-4"),
                        Span("Admin", cls="flex-1"),
                        LucideIcon("chevron-down", cls="w-4 h-4 transition-transform"),
                        cls="flex items-center gap-2 p-2 rounded hover:bg-accent cursor-pointer",
                    ),
                    Div(
                        A(
                            Span("Users"),
                            cls="block p-2 pl-8 rounded hover:bg-accent",
                            href="#",
                        ),
                        A(
                            Span("Roles"),
                            cls="block p-2 pl-8 rounded hover:bg-accent",
                            href="#",
                        ),
                        A(
                            Span("Permissions"),
                            cls="block p-2 pl-8 rounded hover:bg-accent",
                            href="#",
                        ),
                        cls="mt-1 space-y-1",
                    ),
                    cls="mb-2",
                ),
                Div(
                    Div(
                        LucideIcon("settings", cls="w-4 h-4"),
                        Span("Settings", cls="flex-1"),
                        LucideIcon("chevron-down", cls="w-4 h-4 transition-transform"),
                        cls="flex items-center gap-2 p-2 rounded hover:bg-accent cursor-pointer",
                    ),
                    cls="mb-2",
                ),
                cls="p-4",
            ),
        ),
        cls="max-w-xs",
    )


def active_state_example():
    """Active state on navigation items."""
    return Card(
        CardContent(
            Div(
                A(
                    LucideIcon("home", cls="w-4 h-4"),
                    Span("Home"),
                    cls="flex items-center gap-2 p-2 rounded hover:bg-accent",
                    href="#",
                ),
                A(
                    LucideIcon("layout-dashboard", cls="w-4 h-4"),
                    Span("Dashboard"),
                    cls="flex items-center gap-2 p-2 rounded bg-accent font-medium",
                    href="#",
                    **{"aria-current": "page"},
                ),
                A(
                    LucideIcon("settings", cls="w-4 h-4"),
                    Span("Settings"),
                    cls="flex items-center gap-2 p-2 rounded hover:bg-accent",
                    href="#",
                ),
                cls="space-y-1 p-4",
            ),
        ),
        cls="max-w-xs",
    )


def placement_example():
    """Sidebar placement options."""
    return Div(
        Div(
            Button(
                LucideIcon("panel-left", cls="w-4 h-4 mr-2"),
                "Left Sidebar",
                variant="outline",
            ),
            Button(
                LucideIcon("panel-right", cls="w-4 h-4 mr-2"),
                "Right Sidebar",
                variant="outline",
            ),
            cls="flex gap-2",
        ),
        P(
            'Use side="left" (default) or side="right" to control placement.',
            cls="text-muted-foreground text-sm mt-2",
        ),
    )


def custom_signal_example():
    """Custom signal name for multiple sidebars."""
    return Div(
        Div(
            Code(
                """
# Main navigation sidebar
Sidebar(
    ...,
    signal="main_nav",
)

# Secondary panel
Sidebar(
    ...,
    signal="detail_panel",
    side="right",
)

# Toggle buttons targeting specific sidebars
SidebarToggle(target_signal="main_nav")
SidebarToggle(target_signal="detail_panel")
""",
                cls="block whitespace-pre text-sm",
            ),
            cls="bg-muted p-4 rounded-lg font-mono",
        ),
    )


def api_table(rows):
    """Helper to create API documentation table."""
    from nitro.infrastructure.html.components import Table, TableHeader, TableBody, TableRow, TableHead, TableCell

    return Table(
        TableHeader(
            TableRow(
                TableHead("Prop"),
                TableHead("Type"),
                TableHead("Default"),
                TableHead("Description"),
            ),
        ),
        TableBody(
            *[
                TableRow(
                    TableCell(Code(prop), cls="font-mono"),
                    TableCell(Code(type_), cls="font-mono text-muted-foreground"),
                    TableCell(Code(default) if default else Span("-", cls="text-muted-foreground")),
                    TableCell(desc),
                )
                for prop, type_, default, desc in rows
            ]
        ),
        cls="text-sm",
    )


page = Div(
        # Page Header
        Div(
            H1("Sidebar", cls="text-4xl font-bold tracking-tight"),
            P(
                "A responsive sidebar navigation component with Datastar reactivity.",
                cls="text-xl text-muted-foreground mt-2",
            ),
            Div(
                Badge("Datastar", variant="secondary"),
                Badge("Responsive", variant="outline"),
                Badge("Accessible", variant="outline"),
                cls="flex gap-2 mt-4",
            ),
            cls="mb-8",
        ),
        # Overview
        TitledSection(
            "Overview",
            P(
                "The Sidebar component provides a responsive navigation panel that uses ",
                Code("aria-hidden"),
                " state management with Datastar signals for reactivity. It supports:",
                cls="text-muted-foreground",
            ),
            Div(
                Div(
                    LucideIcon("check", cls="text-green-500 w-4 h-4 mt-1"),
                    Span("Left or right placement"),
                    cls="flex gap-2",
                ),
                Div(
                    LucideIcon("check", cls="text-green-500 w-4 h-4 mt-1"),
                    Span("Mobile overlay with click-outside to close"),
                    cls="flex gap-2",
                ),
                Div(
                    LucideIcon("check", cls="text-green-500 w-4 h-4 mt-1"),
                    Span("Desktop push layout"),
                    cls="flex gap-2",
                ),
                Div(
                    LucideIcon("check", cls="text-green-500 w-4 h-4 mt-1"),
                    Span("Escape key to close"),
                    cls="flex gap-2",
                ),
                Div(
                    LucideIcon("check", cls="text-green-500 w-4 h-4 mt-1"),
                    Span("Nested collapsible sections"),
                    cls="flex gap-2",
                ),
                cls="space-y-2 mt-4",
            ),
            cls="mb-8",
        ),
        # Basic Usage
        TitledSection(
            "Basic Usage",
            P(
                "The Sidebar uses a compound component pattern with closures for signal propagation:",
                cls="text-muted-foreground mb-4",
            ),
            ComponentShowcase(basic_sidebar_example),
            cls="mb-8",
        ),
        # Sidebar Toggle
        TitledSection(
            "Sidebar Toggle",
            P(
                "Use ",
                Code("SidebarToggle"),
                " to create a button that toggles the sidebar visibility. ",
                "It can be placed anywhere in your layout (navbar, header, etc.).",
                cls="text-muted-foreground mb-4",
            ),
            ComponentShowcase(toggle_example),
            cls="mb-8",
        ),
        # Navigation Groups
        TitledSection(
            "Navigation Groups",
            P(
                "Organize navigation items into groups with labels using ",
                Code("SidebarGroup"),
                " and ",
                Code("SidebarGroupLabel"),
                ":",
                cls="text-muted-foreground mb-4",
            ),
            ComponentShowcase(nav_groups_example),
            cls="mb-8",
        ),
        # Collapsible Sections
        TitledSection(
            "Collapsible Sections",
            P(
                "Create nested navigation with collapsible sections using ",
                Code("SidebarCollapsible"),
                ". Uses native ",
                Code("<details>/<summary>"),
                " for accessibility:",
                cls="text-muted-foreground mb-4",
            ),
            ComponentShowcase(collapsible_example),
            cls="mb-8",
        ),
        # Active State
        TitledSection(
            "Active State",
            P(
                "Mark the current page using the ",
                Code("is_active"),
                " prop on ",
                Code("SidebarItem"),
                ":",
                cls="text-muted-foreground mb-4",
            ),
            ComponentShowcase(active_state_example),
            cls="mb-8",
        ),
        # Sidebar Placement
        TitledSection(
            "Sidebar Placement",
            P(
                "Control sidebar position with the ",
                Code("side"),
                " prop. Supports ",
                Code('"left"'),
                " (default) or ",
                Code('"right"'),
                ":",
                cls="text-muted-foreground mb-4",
            ),
            ComponentShowcase(placement_example),
            cls="mb-8",
        ),
        # Custom Signal
        TitledSection(
            "Custom Signal Name",
            P(
                "Provide a custom signal name to control multiple sidebars independently:",
                cls="text-muted-foreground mb-4",
            ),
            ComponentShowcase(custom_signal_example),
            cls="mb-8",
        ),
        # Component API
        TitledSection(
            "Component API",
            # Sidebar
            Card(
                CardHeader(
                    CardTitle("Sidebar"),
                    CardDescription("Main sidebar container with Datastar reactivity."),
                ),
                CardContent(
                    api_table(
                        [
                            ("side", '"left" | "right"', '"left"', "Position of sidebar"),
                            (
                                "default_open",
                                "bool",
                                "True",
                                "Initial open state",
                            ),
                            (
                                "signal",
                                "str | None",
                                "auto",
                                "Signal name for state (auto-generated if not provided)",
                            ),
                            ("cls", "str", '""', "Additional CSS classes"),
                        ]
                    ),
                ),
                cls="mb-4",
            ),
            # SidebarItem
            Card(
                CardHeader(
                    CardTitle("SidebarItem"),
                    CardDescription("Individual navigation item."),
                ),
                CardContent(
                    api_table(
                        [
                            ("href", "str | None", "None", "Link URL"),
                            ("icon", "str | None", "None", "Lucide icon name"),
                            ("is_active", "bool", "False", "Whether item is active"),
                            (
                                "variant",
                                '"default" | "outline"',
                                '"default"',
                                "Visual variant",
                            ),
                            ("size", '"default" | "sm" | "lg"', '"default"', "Size variant"),
                            (
                                "close_on_click",
                                "bool",
                                "True",
                                "Close sidebar on mobile when clicked",
                            ),
                        ]
                    ),
                ),
                cls="mb-4",
            ),
            # SidebarCollapsible
            Card(
                CardHeader(
                    CardTitle("SidebarCollapsible"),
                    CardDescription(
                        "Collapsible section using native <details>/<summary>."
                    ),
                ),
                CardContent(
                    api_table(
                        [
                            ("label", "str", "required", "Text label for the trigger"),
                            ("icon", "str | None", "None", "Lucide icon name"),
                            ("default_open", "bool", "False", "Initial expanded state"),
                        ]
                    ),
                ),
                cls="mb-4",
            ),
            # SidebarToggle
            Card(
                CardHeader(
                    CardTitle("SidebarToggle"),
                    CardDescription("Toggle button for sidebar visibility."),
                ),
                CardContent(
                    api_table(
                        [
                            (
                                "target_signal",
                                "str | None",
                                '"sidebar_1"',
                                "Signal name to toggle",
                            ),
                            ("icon", "str", '"panel-left"', "Lucide icon name"),
                        ]
                    ),
                ),
            ),
            cls="mb-8",
        ),
        # Datastar Integration
        TitledSection(
            "Datastar Integration",
            P(
                "The Sidebar component uses Datastar for reactivity without any JavaScript:",
                cls="text-muted-foreground mb-4",
            ),
            Div(
                Div(
                    Code("signals=Signals(**{signal: default_open})"),
                    " - Initializes state",
                    cls="mb-2",
                ),
                Div(
                    Code('data-attr:aria-hidden="!$signal"'),
                    " - Binds visibility to signal",
                    cls="mb-2",
                ),
                Div(
                    Code('on_keydown__window="if (evt.key === \'Escape\') $signal = false"'),
                    " - Escape key handler",
                    cls="mb-2",
                ),
                Div(
                    Code('on_click="if (evt.target === this) $signal = false"'),
                    " - Click-outside handler",
                    cls="mb-2",
                ),
                cls="font-mono text-sm bg-muted p-4 rounded-lg",
            ),
            cls="mb-8",
        ),
        id="content"
    )

@on("page.sidebar")
async def sidebar_page(*args, **kwargs):
    """Sidebar component documentation."""
    return emit_elements(page, topic="updates.components.sidebar")