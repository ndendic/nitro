"""Spinner component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import Spinner, Button

router: APIRouter = APIRouter()


def example_default():
    return Div(
        Spinner(),
        cls="flex items-center justify-center p-8 border rounded"
    )


def example_sizes():
    return Div(
        Div(
            Spinner(size="sm"),
            P("Small (16px)", cls="text-sm text-muted-foreground"),
            cls="flex flex-col items-center gap-2"
        ),
        Div(
            Spinner(size="md"),
            P("Medium (24px)", cls="text-sm text-muted-foreground"),
            cls="flex flex-col items-center gap-2"
        ),
        Div(
            Spinner(size="lg"),
            P("Large (32px)", cls="text-sm text-muted-foreground"),
            cls="flex flex-col items-center gap-2"
        ),
        cls="flex items-end gap-8"
    )


def example_colors():
    return Div(
        Div(
            Spinner(cls="text-primary"),
            P("Primary", cls="text-sm"),
            cls="flex flex-col items-center gap-2"
        ),
        Div(
            Spinner(cls="text-secondary"),
            P("Secondary", cls="text-sm"),
            cls="flex flex-col items-center gap-2"
        ),
        Div(
            Spinner(cls="text-destructive"),
            P("Destructive", cls="text-sm"),
            cls="flex flex-col items-center gap-2"
        ),
        Div(
            Spinner(cls="text-muted-foreground"),
            P("Muted", cls="text-sm"),
            cls="flex flex-col items-center gap-2"
        ),
        cls="flex items-center gap-8"
    )


def example_with_button():
    return Div(
        Button(
            Spinner(size="sm", cls="mr-2"),
            "Loading...",
            disabled=True
        ),
        Button(
            Spinner(size="sm", cls="mr-2"),
            "Processing",
            variant="primary",
            disabled=True
        ),
        cls="flex items-center gap-4"
    )


page = Div(
        H1("Spinner Component"),
        P(
            "A loading indicator component using the Lucide loader-2 icon with "
            "Tailwind's animate-spin animation."
        ),
        Section(
            "Design Philosophy",
            P("The Spinner component provides visual feedback for loading states:"),
            Ul(
                Li("Uses Lucide loader-2 icon for consistent look"),
                Li("Tailwind animate-spin handles the rotation"),
                Li("Three size presets for different contexts"),
                Li("Color via text-* classes for theming flexibility"),
                Li("Accessible with role='status' and aria-label"),
            ),
        ),
        Section(
            "Default Spinner",
            P("The default spinner with medium size:"),
            ComponentShowcase(example_default),
        ),
        Section(
            "Sizes",
            P("Three sizes are available for different use cases:"),
            ComponentShowcase(example_sizes),
        ),
        Section(
            "Colors",
            P("Use Tailwind text-* classes for different colors:"),
            ComponentShowcase(example_colors),
        ),
        Section(
            "With Buttons",
            P("Spinners work well inside disabled buttons for loading states:"),
            ComponentShowcase(example_with_button),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
def Spinner(
    size: str = "md",                       # sm (16px), md (24px), lg (32px)
    cls: str = "",                          # Additional CSS classes (for color)
    **attrs                                 # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Accessibility",
            Ul(
                Li("role='status' - Indicates a live region for updates"),
                Li("aria-label='Loading' - Provides screen reader context"),
                Li("Consider adding visually-hidden text for complex UIs"),
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/spinner")
@template(title="Spinner Component Documentation")
def spinner_page():
    return page

@on("page.spinner")
async def get_spinner(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.spinner")