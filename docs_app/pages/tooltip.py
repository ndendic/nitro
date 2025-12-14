"""Tooltip component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.responses import HTMLResponse
from fastapi import APIRouter

from nitro.infrastructure.html.components import Tooltip, Button

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Tooltip(
            Button("Hover me"),
            content="This is a tooltip!",
        ),
        cls="flex gap-4"
    )


def example_positions():
    return Div(
        Tooltip(
            Button("Top"),
            content="Tooltip on top",
            side="top",
        ),
        Tooltip(
            Button("Bottom"),
            content="Tooltip on bottom",
            side="bottom",
        ),
        Tooltip(
            Button("Left"),
            content="Tooltip on left",
            side="left",
        ),
        Tooltip(
            Button("Right"),
            content="Tooltip on right",
            side="right",
        ),
        cls="flex flex-wrap gap-4 py-8"
    )


def example_alignment():
    return Div(
        Tooltip(
            Button("Start"),
            content="Aligned to start",
            side="bottom",
            align="start",
        ),
        Tooltip(
            Button("Center"),
            content="Aligned to center",
            side="bottom",
            align="center",
        ),
        Tooltip(
            Button("End"),
            content="Aligned to end",
            side="bottom",
            align="end",
        ),
        cls="flex flex-wrap gap-4 py-4"
    )


def example_with_icons():
    return Div(
        Tooltip(
            LucideIcon("info", cls="size-5"),
            content="More information about this feature",
            side="right",
        ),
        Tooltip(
            LucideIcon("help-circle", cls="size-5"),
            content="Need help? Click for documentation",
            side="right",
        ),
        Tooltip(
            LucideIcon("settings", cls="size-5"),
            content="Open settings",
            side="bottom",
        ),
        cls="flex gap-4 items-center"
    )


def example_on_buttons():
    return Div(
        Tooltip(
            Button("Save", variant="primary"),
            content="Save your changes (Ctrl+S)",
        ),
        Tooltip(
            Button("Delete", variant="destructive"),
            content="Permanently delete this item",
            side="bottom",
        ),
        Tooltip(
            Button(LucideIcon("copy", cls="size-4"), variant="outline"),
            content="Copy to clipboard",
            side="right",
        ),
        cls="flex flex-wrap gap-4 py-4"
    )


def example_with_text():
    return P(
        "This is a paragraph with an ",
        Tooltip(
            Span("underlined term", cls="underline decoration-dotted cursor-help"),
            content="A definition or explanation of this term",
        ),
        " that shows a tooltip on hover.",
        cls="text-base"
    )


@router.get("/xtras/tooltip")
@template(title="Tooltip Component Documentation")
def tooltip_docs():
    return Div(
        H1("Tooltip Component"),
        P(
            "A simple tooltip that appears on hover. Uses pure CSS via Basecoat's "
            "data-tooltip pattern - no JavaScript required."
        ),
        Section(
            "Design Philosophy",
            P("Tooltips are lightweight hover hints:"),
            Ul(
                Li("Pure CSS implementation - no JavaScript needed"),
                Li("Smooth fade-in animation on hover"),
                Li("Flexible positioning with side and alignment options"),
                Li("Works on any element (buttons, icons, text, etc.)"),
            ),
        ),
        Section(
            "Basic Tooltip",
            P("Wrap any element with Tooltip and provide content:"),
            ComponentShowcase(example_basic),
        ),
        Section(
            "Positioning",
            P("Control which side the tooltip appears on:"),
            ComponentShowcase(example_positions),
        ),
        Section(
            "Alignment",
            P("Control horizontal/vertical alignment relative to the trigger:"),
            ComponentShowcase(example_alignment),
        ),
        Section(
            "With Icons",
            P("Tooltips work great with icon buttons:"),
            ComponentShowcase(example_with_icons),
        ),
        Section(
            "On Buttons",
            P("Add helpful hints to buttons:"),
            ComponentShowcase(example_on_buttons),
        ),
        Section(
            "Inline with Text",
            P("Use tooltips for inline definitions or explanations:"),
            ComponentShowcase(example_with_text),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
def Tooltip(
    *children,                   # Element(s) to attach tooltip to
    content: str,                # Tooltip text to display
    side: str = "top",           # top, bottom, left, right
    align: str = "center",       # start, center, end
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Key Features",
            Ul(
                Li("Appears on hover with smooth animation"),
                Li("CSS-based positioning via Basecoat styles"),
                Li("Supports 4 sides and 3 alignments"),
                Li("ARIA attributes for accessibility"),
                Li("No JavaScript or Datastar required"),
            ),
        ),
        BackLink(),
    )
