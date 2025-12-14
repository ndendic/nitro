"""Command Palette component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi import APIRouter

from nitro.infrastructure.html.components import (
    Command,
    CommandDialog,
    CommandGroup,
    CommandItem,
    CommandSeparator,
    Button,
    LucideIcon,
)
from rusty_tags.datastar import Signals

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Command(
            CommandGroup(
                CommandItem("Calendar", icon="calendar"),
                CommandItem("Search Emoji", icon="smile"),
                CommandItem("Calculator", icon="calculator"),
                heading="Suggestions",
            ),
            CommandSeparator(),
            CommandGroup(
                CommandItem("Profile", icon="user", shortcut="Ctrl+P"),
                CommandItem("Billing", icon="credit-card", shortcut="Ctrl+B"),
                CommandItem("Settings", icon="settings", shortcut="Ctrl+S"),
                heading="Settings",
            ),
            id="cmd-basic",
            placeholder="Type a command or search...",
        ),
        cls="border rounded-lg w-full max-w-md",
    )


def example_with_actions():
    return Div(
        Command(
            CommandGroup(
                CommandItem(
                    "New File",
                    icon="file-plus",
                    shortcut="Ctrl+N",
                    on_select="alert('Creating new file...')",
                ),
                CommandItem(
                    "Open File",
                    icon="folder-open",
                    shortcut="Ctrl+O",
                    on_select="alert('Opening file dialog...')",
                ),
                CommandItem(
                    "Save",
                    icon="save",
                    shortcut="Ctrl+S",
                    on_select="alert('Saving...')",
                ),
                heading="File",
            ),
            CommandSeparator(),
            CommandGroup(
                CommandItem(
                    "Undo",
                    icon="undo",
                    shortcut="Ctrl+Z",
                    on_select="alert('Undo!')",
                ),
                CommandItem(
                    "Redo",
                    icon="redo",
                    shortcut="Ctrl+Shift+Z",
                    on_select="alert('Redo!')",
                ),
                heading="Edit",
            ),
            id="cmd-actions",
        ),
        cls="border rounded-lg w-full max-w-md",
    )


def example_search_filtering():
    return Div(
        P(
            "Type in the search box to filter commands. Try typing 'set' or 'file'.",
            cls="text-sm text-muted-foreground mb-4",
        ),
        Command(
            CommandGroup(
                CommandItem("New File", icon="file-plus"),
                CommandItem("Open File", icon="folder-open"),
                CommandItem("Save File", icon="save"),
                CommandItem("Close File", icon="x"),
                heading="File Operations",
            ),
            CommandSeparator(),
            CommandGroup(
                CommandItem("Settings", icon="settings"),
                CommandItem("Profile Settings", icon="user-cog"),
                CommandItem("Theme Settings", icon="palette"),
                CommandItem("Keyboard Settings", icon="keyboard"),
                heading="Settings",
            ),
            CommandSeparator(),
            CommandGroup(
                CommandItem("Help", icon="help-circle"),
                CommandItem("Documentation", icon="book-open"),
                CommandItem("About", icon="info"),
                heading="Help",
            ),
            id="cmd-filter",
            placeholder="Search commands...",
        ),
        cls="border rounded-lg w-full max-w-md",
    )


def example_empty_state():
    return Div(
        P(
            "Type something that doesn't match any command to see the empty state.",
            cls="text-sm text-muted-foreground mb-4",
        ),
        Command(
            CommandGroup(
                CommandItem("Home", icon="home"),
                CommandItem("Dashboard", icon="layout-dashboard"),
                CommandItem("Projects", icon="folder"),
                heading="Navigation",
            ),
            id="cmd-empty",
            placeholder="Search...",
            empty_text="No commands found. Try a different search.",
        ),
        cls="border rounded-lg w-full max-w-md",
    )


def example_with_dialog():
    return Div(
        Button(
            LucideIcon("command"),
            "Open Command Palette",
            variant="outline",
            id="cmd-dialog-trigger",
            data_on_click="$cmd_dialog_open = true",
        ),
        Div(
            # Dialog simulation using existing dialog patterns
            Dialog(
                Div(
                    Command(
                        CommandGroup(
                            CommandItem("New Tab", icon="plus", shortcut="Ctrl+T"),
                            CommandItem("New Window", icon="app-window", shortcut="Ctrl+N"),
                            heading="Create",
                        ),
                        CommandSeparator(),
                        CommandGroup(
                            CommandItem("Toggle Dark Mode", icon="moon"),
                            CommandItem("Toggle Sidebar", icon="panel-left"),
                            heading="View",
                        ),
                        id="cmd-in-dialog",
                        placeholder="Type a command...",
                    ),
                ),
                cls="dialog",
                id="cmd-dialog",
                **{"data-attr-open": "$cmd_dialog_open"},
                data_on_click__outside="$cmd_dialog_open = false",
                data_on_keydown__escape="$cmd_dialog_open = false",
            ),
            signals=Signals(cmd_dialog_open=False),
        ),
        cls="flex flex-col gap-4",
    )


def example_custom_icons():
    return Div(
        Command(
            CommandGroup(
                CommandItem("GitHub", icon="github"),
                CommandItem("Twitter", icon="twitter"),
                CommandItem("LinkedIn", icon="linkedin"),
                CommandItem("Discord", icon="message-circle"),
                heading="Social",
            ),
            CommandSeparator(),
            CommandGroup(
                CommandItem("Slack", icon="hash"),
                CommandItem("Email", icon="mail"),
                CommandItem("Calendar", icon="calendar"),
                heading="Communication",
            ),
            id="cmd-icons",
        ),
        cls="border rounded-lg w-full max-w-md",
    )


@router.get("/xtras/command")
@template(title="Command Palette Component Documentation")
def command_docs():
    return Div(
        H1("Command Palette Component"),
        P(
            "A command palette component for quick actions and search. Supports grouping, "
            "keyboard shortcuts, icons, and real-time filtering. Built on Basecoat's .command CSS."
        ),
        TitledSection(
            "Design Philosophy",
            P("Command palette follows these principles:"),
            Ul(
                Li("Compound component pattern - Command, CommandGroup, CommandItem work together"),
                Li("Real-time filtering - type to instantly filter commands"),
                Li("Keyboard shortcuts - display and trigger keyboard shortcuts"),
                Li("Basecoat CSS - uses existing .command styles for consistency"),
                Li("ARIA attributes - role='menu', role='menuitem' for accessibility"),
                Li("Groups - organize related commands with headings"),
            ),
        ),
        TitledSection(
            "Basic Usage",
            P("A simple command palette with groups:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "With Actions",
            P("Commands can execute actions when clicked:"),
            ComponentShowcase(example_with_actions),
        ),
        TitledSection(
            "Search Filtering",
            P("Type to filter commands in real-time:"),
            ComponentShowcase(example_search_filtering),
        ),
        TitledSection(
            "Empty State",
            P("Custom message when no commands match the search:"),
            ComponentShowcase(example_empty_state),
        ),
        TitledSection(
            "With Dialog",
            P("Command palette inside a modal dialog (common pattern):"),
            ComponentShowcase(example_with_dialog),
        ),
        TitledSection(
            "Custom Icons",
            P("Commands can include any Lucide icon:"),
            ComponentShowcase(example_custom_icons),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
# Command - Container with search input
def Command(
    *children,                   # CommandGroup, CommandItem, or CommandSeparator elements
    id: str = "",                # Unique identifier
    placeholder: str = "Type a command or search...",
    empty_text: str = "No results found",
    cls: str = "",
    **attrs
) -> HtmlString

# CommandGroup - Group of related commands (closure pattern)
def CommandGroup(
    *children,                   # CommandItem elements
    heading: str = "",           # Optional group heading
    cls: str = "",
    **attrs
) -> Callable

# CommandItem - Individual command (closure pattern)
def CommandItem(
    *children,                   # Item content (text)
    on_select: str = None,       # Datastar expression on click
    shortcut: str = None,        # Keyboard shortcut display (e.g., "Ctrl+N")
    icon: str = None,            # Lucide icon name
    disabled: bool = False,
    search_text: str = None,     # Custom text for filtering
    cls: str = "",
    **attrs
) -> Callable

# CommandSeparator - Visual divider between groups
def CommandSeparator(cls: str = "", **attrs) -> HtmlString

# CommandEmpty - Custom empty state (optional)
def CommandEmpty(*children, cls: str = "", **attrs) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Keyboard Shortcuts",
            P("The shortcut prop displays keyboard shortcuts:"),
            Ul(
                Li('Use "+" to separate keys: "Ctrl+S", "Ctrl+Shift+N"'),
                Li("Each key part becomes a Kbd component"),
                Li("Common modifiers: Ctrl, Alt, Shift, Cmd (or use symbols)"),
            ),
        ),
        TitledSection(
            "Key Behaviors",
            Ul(
                Li("Type in search input to filter commands instantly"),
                Li("Click a command to execute its on_select action"),
                Li("Groups are hidden when all their items are filtered out"),
                Li("Empty state shown when no commands match search"),
                Li("Separators hidden during active search"),
            ),
        ),
        TitledSection(
            "Accessibility",
            Ul(
                Li("role='menu' on command container"),
                Li("role='menuitem' on each command item"),
                Li("role='group' on command groups"),
                Li("role='separator' on dividers"),
                Li("aria-disabled for disabled items"),
                Li("aria-hidden for filtered-out items"),
            ),
        ),
        BackLink(),
    )
