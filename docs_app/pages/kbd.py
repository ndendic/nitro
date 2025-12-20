"""Kbd (Keyboard) component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import Kbd

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Kbd("Esc"),
        Kbd("Enter"),
        Kbd("Tab"),
        Kbd("Space"),
        cls="flex flex-wrap gap-2"
    )


def example_sizes():
    return Div(
        Kbd("Ctrl", size="sm"),
        Kbd("Ctrl", size="md"),
        Kbd("Ctrl", size="lg"),
        cls="flex flex-wrap items-center gap-2"
    )


def example_combinations():
    return Div(
        Div(
            Kbd("Ctrl"), Span(" + ", cls="mx-1"), Kbd("C"),
            Span(" - Copy", cls="ml-2"),
            cls="flex items-center"
        ),
        Div(
            Kbd("Ctrl"), Span(" + ", cls="mx-1"), Kbd("V"),
            Span(" - Paste", cls="ml-2"),
            cls="flex items-center"
        ),
        Div(
            Kbd("Ctrl"), Span(" + ", cls="mx-1"), Kbd("Z"),
            Span(" - Undo", cls="ml-2"),
            cls="flex items-center"
        ),
        Div(
            Kbd("Ctrl"), Span(" + ", cls="mx-1"), Kbd("Shift"), Span(" + ", cls="mx-1"), Kbd("Z"),
            Span(" - Redo", cls="ml-2"),
            cls="flex items-center"
        ),
        cls="space-y-2"
    )


def example_special_keys():
    return Div(
        Kbd("↑"),
        Kbd("↓"),
        Kbd("←"),
        Kbd("→"),
        Kbd("⌘"),
        Kbd("⌥"),
        Kbd("⇧"),
        Kbd("⌃"),
        cls="flex flex-wrap gap-2"
    )


def example_in_context():
    return Div(
        P(
            "Press ",
            Kbd("Esc"),
            " to close the dialog, or ",
            Kbd("Enter"),
            " to confirm.",
        ),
        P(
            "Use ",
            Kbd("↑"),
            " and ",
            Kbd("↓"),
            " to navigate the list.",
            cls="mt-2"
        ),
        P(
            "Quick save with ",
            Kbd("Ctrl"),
            " + ",
            Kbd("S"),
            ".",
            cls="mt-2"
        ),
    )


def example_shortcuts_table():
    return Table(
        Thead(
            Tr(
                Th("Action"),
                Th("Shortcut"),
            ),
        ),
        Tbody(
            Tr(
                Td("Save"),
                Td(Kbd("Ctrl"), " + ", Kbd("S")),
            ),
            Tr(
                Td("Open"),
                Td(Kbd("Ctrl"), " + ", Kbd("O")),
            ),
            Tr(
                Td("New"),
                Td(Kbd("Ctrl"), " + ", Kbd("N")),
            ),
            Tr(
                Td("Find"),
                Td(Kbd("Ctrl"), " + ", Kbd("F")),
            ),
            Tr(
                Td("Replace"),
                Td(Kbd("Ctrl"), " + ", Kbd("H")),
            ),
        ),
        cls="table w-full max-w-md"
    )


page = Div(
        H1("Kbd Component"),
        P(
            "Displays a keyboard key or shortcut in a visual representation "
            "similar to a physical key. Used to indicate keyboard shortcuts."
        ),
        TitledSection(
            "Design Philosophy",
            P("The Kbd component:"),
            Ul(
                Li("Uses the semantic <kbd> HTML element"),
                Li("Styled to look like physical keyboard keys"),
                Li("Works inline with text for documentation"),
                Li("Supports special characters and symbols"),
            ),
        ),
        TitledSection(
            "Basic Keys",
            P("Single keyboard keys:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "Sizes",
            P("Three sizes for different contexts:"),
            ComponentShowcase(example_sizes),
        ),
        TitledSection(
            "Key Combinations",
            P("Show keyboard shortcuts with multiple keys:"),
            ComponentShowcase(example_combinations),
        ),
        TitledSection(
            "Special Keys",
            P("Arrow keys and modifier symbols:"),
            ComponentShowcase(example_special_keys),
        ),
        TitledSection(
            "Inline Usage",
            P("Keys work naturally inline with text:"),
            ComponentShowcase(example_in_context),
        ),
        TitledSection(
            "Shortcuts Table",
            P("Document keyboard shortcuts in a table:"),
            ComponentShowcase(example_shortcuts_table),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
def Kbd(
    *children,                              # Key content (single key or symbol)
    size: str = "md",                       # sm, md, lg
    cls: str = "",                          # Additional CSS classes
    **attrs                                 # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/kbd")
@template(title="Kbd Component Documentation")
def kbd_page():
    return page

@on("page.kbd")
async def get_kbd(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.kbd")