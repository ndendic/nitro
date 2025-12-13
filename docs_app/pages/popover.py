"""Popover component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.responses import HTMLResponse
from fastapi import APIRouter

from nitro.infrastructure.html.components import (
    Popover,
    PopoverTrigger,
    PopoverContent,
    PopoverClose,
    Button,
    LucideIcon,
    Label,
)
from nitro.infrastructure.html import Input

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Popover(
            PopoverTrigger(Button("Open Popover", variant="outline")),
            PopoverContent(
                H4("Popover Title", cls="font-semibold mb-2"),
                P("This is a basic popover with some content.", cls="text-sm text-muted-foreground"),
            ),
            id="basic-popover",
        ),
        cls="flex gap-4"
    )


def example_with_form():
    return Div(
        Popover(
            PopoverTrigger(Button("Edit Profile", variant="outline")),
            PopoverContent(
                H4("Edit Profile", cls="font-semibold mb-4"),
                Div(
                    Label("Name", html_for="name", cls="text-sm font-medium"),
                    Input(type="text", id="name", placeholder="Enter your name", cls="input mt-1 w-full"),
                    cls="mb-3"
                ),
                Div(
                    Label("Email", html_for="email", cls="text-sm font-medium"),
                    Input(type="email", id="email", placeholder="Enter your email", cls="input mt-1 w-full"),
                    cls="mb-3"
                ),
                Button("Save", variant="default", cls="w-full"),
                cls="w-64",
            ),
            id="form-popover",
        ),
        cls="flex gap-4"
    )


def example_positioning():
    return Div(
        Popover(
            PopoverTrigger(Button("Bottom (default)", variant="outline")),
            PopoverContent(
                P("This appears below the trigger.", cls="text-sm"),
                side="bottom",
            ),
            id="position-bottom",
        ),
        Popover(
            PopoverTrigger(Button("Top", variant="outline")),
            PopoverContent(
                P("This appears above the trigger.", cls="text-sm"),
                side="top",
            ),
            id="position-top",
        ),
        Popover(
            PopoverTrigger(Button("Left", variant="outline")),
            PopoverContent(
                P("This appears to the left.", cls="text-sm"),
                side="left",
            ),
            id="position-left",
        ),
        Popover(
            PopoverTrigger(Button("Right", variant="outline")),
            PopoverContent(
                P("This appears to the right.", cls="text-sm"),
                side="right",
            ),
            id="position-right",
        ),
        cls="flex gap-4 flex-wrap"
    )


def example_alignment():
    return Div(
        Popover(
            PopoverTrigger(Button("Start", variant="outline")),
            PopoverContent(
                P("Aligned to the start.", cls="text-sm"),
                side="bottom",
                align="start",
            ),
            id="align-start",
        ),
        Popover(
            PopoverTrigger(Button("Center (default)", variant="outline")),
            PopoverContent(
                P("Aligned to the center.", cls="text-sm"),
                side="bottom",
                align="center",
            ),
            id="align-center",
        ),
        Popover(
            PopoverTrigger(Button("End", variant="outline")),
            PopoverContent(
                P("Aligned to the end.", cls="text-sm"),
                side="bottom",
                align="end",
            ),
            id="align-end",
        ),
        cls="flex gap-4 flex-wrap"
    )


def example_with_close_button():
    return Div(
        Popover(
            PopoverTrigger(Button("With Close Button", variant="outline")),
            PopoverContent(
                Div(
                    H4("Popover Title", cls="font-semibold"),
                    PopoverClose(LucideIcon("x", cls="h-4 w-4"), popover_id="close-popover", cls="absolute top-2 right-2 p-1 hover:bg-muted rounded"),
                    cls="relative"
                ),
                P("Click the X button or outside to close.", cls="text-sm text-muted-foreground mt-2"),
                cls="pr-8",
            ),
            id="close-popover",
        ),
        cls="flex gap-4"
    )


def example_rich_content():
    return Div(
        Popover(
            PopoverTrigger(Button(LucideIcon("settings", cls="mr-2 h-4 w-4"), "Settings", variant="outline")),
            PopoverContent(
                H4("Display Settings", cls="font-semibold mb-4"),
                Div(
                    Div(
                        Label("Width", cls="text-sm font-medium"),
                        Input(type="range", id="width", cls="w-full"),
                        cls="mb-3"
                    ),
                    Div(
                        Label("Height", cls="text-sm font-medium"),
                        Input(type="range", id="height", cls="w-full"),
                        cls="mb-3"
                    ),
                    Div(
                        Button(LucideIcon("rotate-ccw", cls="mr-2 h-4 w-4"), "Reset", variant="ghost", cls="w-full"),
                    ),
                ),
                cls="w-72",
            ),
            id="settings-popover",
        ),
        cls="flex gap-4"
    )


@router.get("/xtras/popover")
@template(title="Popover Component Documentation")
def popover_docs():
    return Div(
        H1("Popover Component"),
        P(
            "A positioned overlay container for additional content. Uses Datastar signals "
            "for state management and Basecoat CSS for styling. Supports various positions, "
            "alignments, and can contain any content including forms."
        ),
        Section(
            "Basic Popover",
            P("A simple popover with title and content:"),
            ComponentShowcase(example_basic),
        ),
        Section(
            "With Form Content",
            P("Popovers can contain interactive form elements:"),
            ComponentShowcase(example_with_form),
        ),
        Section(
            "Positioning",
            P("Control which side the popover appears on:"),
            ComponentShowcase(example_positioning),
        ),
        Section(
            "Alignment",
            P("Control horizontal/vertical alignment relative to the trigger:"),
            ComponentShowcase(example_alignment),
        ),
        Section(
            "With Close Button",
            P("Add a close button inside the popover:"),
            ComponentShowcase(example_with_close_button),
        ),
        Section(
            "Rich Content",
            P("Popovers can contain complex UI elements:"),
            ComponentShowcase(example_rich_content),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
# Popover - Container component
def Popover(
    *children,                   # PopoverTrigger and PopoverContent
    id: str = "",                # Unique identifier (auto-generated if not provided)
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString

# PopoverTrigger - Element that opens the popover (closure pattern)
def PopoverTrigger(
    *children,                   # Trigger content (typically a Button)
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> Callable

# PopoverContent - Content container (closure pattern)
def PopoverContent(
    *children,                   # Any content (text, forms, etc.)
    side: str = "bottom",        # Side: "bottom", "top", "left", "right"
    align: str = "center",       # Alignment: "start", "center", "end"
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> Callable

# PopoverClose - Close button
def PopoverClose(
    *children,                   # Button content
    popover_id: str,             # Required: ID of the parent Popover
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
                Li("Supports any content including forms and complex UI"),
            ),
        ),
        BackLink(),
    )
