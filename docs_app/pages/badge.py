"""Badge component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter

from nitro.infrastructure.html.components import Badge
from nitro.infrastructure.events import on, emit_elements

router: APIRouter = APIRouter()


def example_variants():
    return Div(
        Badge("Default"),
        Badge("Primary", variant="primary"),
        Badge("Secondary", variant="secondary"),
        Badge("Destructive", variant="destructive"),
        Badge("Outline", variant="outline"),
        Badge("Success", variant="success"),
        Badge("Warning", variant="warning"),
        cls="flex flex-wrap gap-2"
    )


def example_sizes():
    return Div(
        Badge("Small", size="sm"),
        Badge("Medium", size="md"),
        Badge("Large", size="lg"),
        cls="flex flex-wrap items-center gap-2"
    )


def example_with_icons():
    return Div(
        Badge(LucideIcon("check", cls="size-3"), "Verified", variant="success"),
        Badge(LucideIcon("alert-triangle", cls="size-3"), "Warning", variant="warning"),
        Badge(LucideIcon("x", cls="size-3"), "Error", variant="destructive"),
        Badge(LucideIcon("info", cls="size-3"), "Info", variant="primary"),
        cls="flex flex-wrap gap-2"
    )


def example_status_indicators():
    return Div(
        Div(
            Span("User Status: "),
            Badge("Active", variant="success"),
            cls="flex items-center gap-2"
        ),
        Div(
            Span("Order Status: "),
            Badge("Pending", variant="warning"),
            cls="flex items-center gap-2"
        ),
        Div(
            Span("Subscription: "),
            Badge("Expired", variant="destructive"),
            cls="flex items-center gap-2"
        ),
        cls="space-y-2"
    )


def example_counts():
    return Div(
        Div(
            Span("Notifications"),
            Badge("99+", variant="destructive", size="sm"),
            cls="flex items-center gap-2"
        ),
        Div(
            Span("Messages"),
            Badge("5", variant="primary", size="sm"),
            cls="flex items-center gap-2"
        ),
        Div(
            Span("Updates"),
            Badge("New", variant="secondary", size="sm"),
            cls="flex items-center gap-2"
        ),
        cls="space-y-2"
    )


page = Div(
        H1("Badge Component"),
        P(
            "A small visual indicator used to highlight status, categories, "
            "or counts alongside other content."
        ),
        Section(
            "Design Philosophy",
            P("Badges are lightweight status indicators:"),
            Ul(
                Li("Use for status, labels, or counts"),
                Li("Keep text short and scannable"),
                Li("Choose variants that communicate meaning"),
                Li("Combine with icons for additional context"),
            ),
        ),
        Section(
            "Variants",
            P("Seven visual variants for different contexts:"),
            ComponentShowcase(example_variants),
        ),
        Section(
            "Sizes",
            P("Three sizes available:"),
            ComponentShowcase(example_sizes),
        ),
        Section(
            "With Icons",
            P("Badges can include icons for better visual communication:"),
            ComponentShowcase(example_with_icons),
        ),
        Section(
            "Status Indicators",
            P("Common pattern for showing status alongside text:"),
            ComponentShowcase(example_status_indicators),
        ),
        Section(
            "Count Badges",
            P("Show notification counts or 'new' indicators:"),
            ComponentShowcase(example_counts),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
def Badge(
    *children,                              # Badge content (text, icons, etc.)
    variant: str = "default",               # default, primary, secondary,
                                            # destructive, outline, success, warning
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

@router.get("/xtras/badge")
@template(title="Badge Component Documentation")
def badge_page():
    return page

@on("page.badge")
async def get_badge(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.badge")