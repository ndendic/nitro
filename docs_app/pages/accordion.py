"""Accordion component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.responses import HTMLResponse
from fastapi import APIRouter

from nitro.infrastructure.html.components.monsterui.all import H2
from nitro.infrastructure.html.components import Accordion, AccordionItem

router: APIRouter = APIRouter()


def example_1():
    return Accordion(
        AccordionItem(
            "What is RustyTags?",
            P(
                "RustyTags is a high-performance HTML generation library that combines Rust-powered performance with modern Python web development."
            ),
            P(
                "It provides 3-10x faster rendering than pure Python solutions.",
                cls="pb-4",
            ),
            cls="group border-b last:border-b-0"
        ),
        AccordionItem(
            "What are Xtras components?",
            P(
                "Xtras components focus on complex anatomical patterns that are genuinely difficult to implement correctly."
            ),
            P("We avoid wrapping simple HTML elements unnecessarily.", cls="pb-4"),
        ),
        AccordionItem(
            "Why use native HTML?",
            P(
                "Native HTML provides accessibility, performance, and simplicity out of the box.",
            ),
            P(
                "We only add complexity when it solves real structural problems.",
                cls="pb-4",
            ),
        ),
    )


def example_2():
    return Accordion(
        AccordionItem(
            "Performance Features",
            Ul(
                Li("Rust-powered HTML generation"),
                Li("Memory optimization and caching"),
                Li("Thread-local pools"),
                cls="pb-4",
            ),
            name="single-group",
        ),
        AccordionItem(
            "Developer Experience",
            Ul(
                Li("FastHTML-style syntax"),
                Li("Automatic type conversion"),
                Li("Smart attribute handling"),
                cls="pb-4",
            ),
            name="single-group",
        ),
        AccordionItem(
            "Framework Integration",
            Ul(
                Li("FastAPI support"),
                Li("Flask integration"),
                Li("Django compatibility"),
                cls="pb-4",
            ),
            name="single-group",
        ),
    )


@router.get("/xtras/accordion")
@template(title="Accordion Component Documentation")
def accordion_docs():
    return Div(
        H1("Accordion Component"),
        H2("Accordion Component documentation"),
        P(
            "The Accordion component uses native HTML details/summary elements with optional name-based grouping for accordion behavior."
        ),
        Section(
            "Design Philosophy",
            P("This component follows our 'less is more' principle:"),
            Ul(
                Li("🏗️ Uses native HTML details/summary elements"),
                Li("♿️ Built-in accessibility through semantic HTML"),
                Li("🔗 Name attribute for native accordion grouping behavior"),
                Li("🚀 No JavaScript required for basic functionality"),
                Li("✨ Simple, clean API that's easy to understand"),
            ),
        ),
        Section(
            "Key Insight",
            P(
                Strong(
                    "The name attribute on details elements automatically creates accordion behavior!"
                ),
                " When multiple details elements share the same name, only one can be open at a time. This is native HTML functionality.",
            ),
        ),
        Section(
            "Basic Usage Demo - Multiple Open",
            P("Multiple items can be open simultaneously (default behavior):"),
            ComponentShowcase(example_1),
        ),
        Section(
            "Single Open Demo - Name Grouping",
            P("Using the name attribute, only one item can be open at a time:"),
            ComponentShowcase(example_2),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
# Simple accordion container
def Accordion(
    *children,                              # AccordionItem components or raw HTML
    name: Optional[str] = None,             # Shared name for single-open behavior
    cls: str = "Tailwind default",          # CSS classes for root container
    **attrs: Any                            # Additional HTML attributes
) -> rt.HtmlString

# Individual accordion item using HTML details/summary
def AccordionItem(
    trigger_content,                        # Content for the accordion trigger
    *children,                              # Collapsible content
    open: bool = False,                     # Whether item starts open
    name: Optional[str] = None,             # Name for grouping (single-open behavior)
    cls: str = "Tailwind default",          # CSS classes for the details element
    summary_cls: str = "Tailwind default",  # CSS classes for the summary element
    hide_marker: bool = True,               # Whether to hide the marker icon
    **attrs: Any                            # Additional HTML attributes
) -> rt.HtmlString

# Trigger for accordion items - This a defult trigger for AccordionItem if you provide only string as trigger_content
def AccordionItemTrigger(
    title,                               # Content for the accordion trigger
    icon="chevron-down",                 # Icon to use for the trigger
    cls="Tailwind default classes",      # CSS classes for the trigger
    icon_cls="Tailwind default classes", # CSS classes for the icon
    **attrs: Any,                        # Additional HTML attributes
) -> rt.HtmlString:
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
    )
