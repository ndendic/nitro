"""Skeleton component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import Skeleton

router: APIRouter = APIRouter()


def example_text():
    return Div(
        Skeleton(cls="h-4 w-[250px]"),
        cls="space-y-2"
    )


def example_avatar():
    return Div(
        Skeleton(cls="h-12 w-12 rounded-full"),
    )


def example_card():
    return Div(
        Skeleton(cls="h-[125px] w-[250px] rounded-xl"),
    )


def example_text_block():
    return Div(
        Skeleton(cls="h-4 w-[350px]"),
        Skeleton(cls="h-4 w-[300px]"),
        Skeleton(cls="h-4 w-[250px]"),
        cls="space-y-3"
    )


def example_profile():
    return Div(
        Skeleton(cls="h-16 w-16 rounded-full"),
        Div(
            Skeleton(cls="h-4 w-[200px]"),
            Skeleton(cls="h-3 w-[150px]"),
            cls="space-y-2"
        ),
        cls="flex items-center gap-4"
    )


def example_card_layout():
    return Div(
        # Card header
        Div(
            Skeleton(cls="h-48 w-full rounded-t-xl"),
        ),
        # Card content
        Div(
            Div(
                Skeleton(cls="h-5 w-[60%]"),
                Skeleton(cls="h-4 w-[80%]"),
                Skeleton(cls="h-4 w-[70%]"),
                cls="space-y-3"
            ),
            cls="p-4"
        ),
        cls="w-[300px] border rounded-xl overflow-hidden"
    )


def example_table_rows():
    return Div(
        # Header row
        Div(
            Skeleton(cls="h-4 w-[80px]"),
            Skeleton(cls="h-4 w-[120px]"),
            Skeleton(cls="h-4 w-[100px]"),
            Skeleton(cls="h-4 w-[60px]"),
            cls="flex gap-4 pb-4 border-b"
        ),
        # Data rows
        Div(
            Skeleton(cls="h-4 w-[80px]"),
            Skeleton(cls="h-4 w-[120px]"),
            Skeleton(cls="h-4 w-[100px]"),
            Skeleton(cls="h-4 w-[60px]"),
            cls="flex gap-4 py-4"
        ),
        Div(
            Skeleton(cls="h-4 w-[80px]"),
            Skeleton(cls="h-4 w-[120px]"),
            Skeleton(cls="h-4 w-[100px]"),
            Skeleton(cls="h-4 w-[60px]"),
            cls="flex gap-4 py-4"
        ),
        Div(
            Skeleton(cls="h-4 w-[80px]"),
            Skeleton(cls="h-4 w-[120px]"),
            Skeleton(cls="h-4 w-[100px]"),
            Skeleton(cls="h-4 w-[60px]"),
            cls="flex gap-4 py-4"
        ),
        cls="space-y-0"
    )


page = Div(
        H1("Skeleton Component"),
        P(
            "A loading placeholder component using Tailwind's animate-pulse "
            "animation for a subtle pulsing effect."
        ),
        TitledSection(
            "Design Philosophy",
            P("The Skeleton component provides content placeholders during loading:"),
            Ul(
                Li("Uses Tailwind animate-pulse for the pulsing effect"),
                Li("Sizing is controlled via Tailwind classes (h-*, w-*)"),
                Li("Shapes via rounded-* classes (rounded, rounded-full, etc.)"),
                Li("bg-muted provides a neutral placeholder color"),
                Li("aria-hidden='true' since it's decorative content"),
            ),
        ),
        TitledSection(
            "Text Line",
            P("A simple text line placeholder:"),
            ComponentShowcase(example_text),
        ),
        TitledSection(
            "Avatar",
            P("A circular avatar placeholder:"),
            ComponentShowcase(example_avatar),
        ),
        TitledSection(
            "Card",
            P("A card-sized placeholder:"),
            ComponentShowcase(example_card),
        ),
        TitledSection(
            "Text Block",
            P("Multiple lines simulating a paragraph:"),
            ComponentShowcase(example_text_block),
        ),
        TitledSection(
            "Profile Layout",
            P("Avatar with text placeholders:"),
            ComponentShowcase(example_profile),
        ),
        TitledSection(
            "Card Layout",
            P("A full card skeleton with image and text:"),
            ComponentShowcase(example_card_layout),
        ),
        TitledSection(
            "Table Rows",
            P("Table loading state with header and rows:"),
            ComponentShowcase(example_table_rows),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
def Skeleton(
    cls: str = "",                          # Tailwind classes for sizing
                                            # Height: h-4, h-12, h-[125px]
                                            # Width: w-full, w-[250px]
                                            # Shape: rounded, rounded-full, rounded-xl
    **attrs                                 # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Accessibility",
            Ul(
                Li("aria-hidden='true' - Skeletons are decorative"),
                Li("Consider loading states in live regions for screen readers"),
                Li("Pair with visible loading indicators when appropriate"),
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/skeleton")
@template(title="Skeleton Component Documentation")
def skeleton_page():
    return page

@on("page.skeleton")
async def get_skeleton(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.skeleton")