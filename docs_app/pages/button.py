"""Button component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import *
from fastapi import Request
from nitro.infrastructure.html.components import Button, ButtonGroup

router: APIRouter = APIRouter()


def example_variants():
    return Div(
        Button("Primary/Default", variant="primary", on_keys_enter="console.log('Primary/Default')"),
        Button("Secondary", variant="secondary"),
        Button("Ghost", variant="ghost"),
        Button("Destructive", variant="destructive"),
        Button("Outline", variant="outline"),
        Button("Link", variant="link"),
        cls="flex flex-wrap gap-2"
    )


def example_sizes():
    return Div(
        Button("Small", variant="sm"),
        Button("Default"),
        Button("Large", variant="lg"),
        Button(LucideIcon("plus")," Icon", variant="icon"),
        cls="flex flex-wrap items-center gap-2"
    )


def example_with_icons():
    return Div(
        Button(LucideIcon("mail"), "Login with Email", variant="primary"),
        Button(LucideIcon("loader-2", cls="animate-spin"), "Loading...", disabled=True),
        Button("Next", LucideIcon("arrow-right"), variant="outline"),
        cls="flex flex-wrap gap-2"
    )


def example_button_group():
    return Div(
        ButtonGroup(
            Button("Left", variant="outline"),
            Button("Center", variant="outline"),
            Button("Right", variant="outline"),
        ),
        ButtonGroup(
            Button("Top", variant="outline"),
            Button("Middle", variant="outline"),
            Button("Bottom", variant="outline"),
            orientation="vertical",
        ),
        cls="flex flex-wrap gap-2"
    )


def example_disabled():
    return Div(
        Button("Disabled Default", disabled=True),
        Button("Disabled Primary", variant="primary", disabled=True),
        Button("Disabled Destructive", variant="destructive", disabled=True),
        cls="flex flex-wrap gap-2"
    )

page = Div(
        H1("Button Component"),
        P(
            "A versatile button component with multiple variants and sizes. "
            "Uses semantic class names with data attributes for styling."
        ),
        TitledSection(
            "Design Philosophy",
            P("The Button component follows Nitro conventions:"),
            Ul(
                Li("Semantic class names (btn, btn-primary, etc.)"),
                Li("Data attributes for variants (data-variant, data-size)"),
                Li("cls parameter merges with base classes"),
                Li("**attrs pass-through for any HTML attribute"),
            ),
        ),
        TitledSection(
            "Variants",
            P("Seven visual variants are available for different use cases:"),
            ComponentShowcase(example_variants),
        ),
        TitledSection(
            "Sizes",
            P("Four sizes including an icon-only option:"),
            ComponentShowcase(example_sizes),
        ),
        TitledSection(
            "With Icons",
            P("Buttons can include icons before or after text:"),
            ComponentShowcase(example_with_icons),
        ),
        TitledSection(
            "Button Group",
            P("Group related buttons together:"),
            ComponentShowcase(example_button_group),
        ),
        TitledSection(
            "Disabled State",
            P("Buttons can be disabled:"),
            ComponentShowcase(example_disabled),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
def Button(
    *children,                              # Button content (text, icons, etc.)
    variant: str = "default",               # default, primary, secondary, ghost,
                                            # destructive, outline, link
    size: str = "md",                       # sm, md, lg, icon
    disabled: bool = False,                 # Whether button is disabled
    cls: str = "",                          # Additional CSS classes
    **attrs                                 # Additional HTML attributes
) -> HtmlString

def ButtonGroup(
    *children,                              # Button components to group
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
@router.get("/xtras/button")
@template(title="Button Component Documentation")
def button_docs():
    return page

@on("page.button")
async def get_button(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.button")