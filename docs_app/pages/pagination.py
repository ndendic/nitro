"""Pagination component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from rusty_tags.datastar import Signal, Signals
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import (
    Pagination,
    PaginationContent,
    Card,
    CardHeader,
    CardTitle,
    CardContent,
)

router: APIRouter = APIRouter()


def example_basic():
    """Basic pagination with 10 pages."""
    return Div(
        Pagination(total_pages=10, current_page=1),
        cls="py-4",
    )


def example_with_content():
    """Pagination with changing content."""
    return Div(
        Div(
            Div(
                Span("Current page: ", cls="text-muted-foreground"),
                Span(text="$page", cls="font-bold"),
                cls="text-center mb-4",
            ),
            # Page content that changes based on signal
            Card(
                CardContent(
                    Div("This is the content for page 1", data_show="$page === 1"),
                    Div("This is the content for page 2", data_show="$page === 2"),
                    Div("This is the content for page 3", data_show="$page === 3"),
                    Div("This is the content for page 4", data_show="$page === 4"),
                    Div("This is the content for page 5", data_show="$page === 5"),
                    cls="min-h-[60px] flex items-center justify-center",
                ),
            ),
            cls="mb-4",
        ),
        Pagination(total_pages=5, current_page=1, signal_name="page"),
        signals=Signals(page=1),
    )


def example_many_pages():
    """Pagination with many pages (shows ellipsis)."""
    return Div(
        Pagination(total_pages=20, current_page=10),
        cls="py-4",
    )


def example_with_first_last():
    """Pagination with first/last buttons."""
    return Div(
        Pagination(total_pages=15, current_page=8, show_first_last=True),
        cls="py-4",
    )


def example_minimal():
    """Minimal pagination without prev/next text."""
    return Div(
        Pagination(total_pages=5, current_page=1, show_prev_next=True, siblings=0),
        cls="py-4",
    )


page = Div(
        H1("Pagination Component"),
        P(
            "A navigation component for paginated content. Uses Datastar signals "
            "for reactive page state management."
        ),
        TitledSection(
            "Design Philosophy",
            P("Pagination follows Basecoat patterns:"),
            Ul(
                Li("Uses semantic nav element with role='navigation'"),
                Li("aria-label='Pagination' for accessibility"),
                Li("Button utility classes for consistent styling"),
                Li("Ellipsis for large page counts"),
                Li("Datastar signals for reactive page state"),
            ),
        ),
        TitledSection(
            "Basic Usage",
            P("Simple pagination with 10 pages. Click to navigate:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "With Content Updates",
            P("Pagination that updates content reactively using Datastar signals:"),
            ComponentShowcase(example_with_content),
        ),
        TitledSection(
            "Many Pages (Ellipsis)",
            P("When there are many pages, ellipsis is shown for omitted pages:"),
            ComponentShowcase(example_many_pages),
        ),
        TitledSection(
            "With First/Last Buttons",
            P("Add first/last navigation buttons for jumping to boundaries:"),
            ComponentShowcase(example_with_first_last),
        ),
        TitledSection(
            "Minimal Style",
            P("Compact pagination with fewer sibling pages:"),
            ComponentShowcase(example_minimal),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
def Pagination(
    total_pages: int,                   # Total number of pages
    signal: Signal = None,              # Datastar Signal object (optional)
    signal_name: str = "page",          # Name for auto-created signal
    current_page: int = 1,              # Initial current page (1-indexed)
    show_prev_next: bool = True,        # Show Previous/Next buttons
    show_first_last: bool = False,      # Show First/Last buttons
    siblings: int = 1,                  # Number of siblings around current
    cls: str = "",                      # Additional CSS classes
    **attrs                             # Additional HTML attributes
) -> HtmlString

def PaginationContent(
    *pages,                             # Content for each page
    signal_name: str = "page",          # Name of the page signal
    cls: str = "",                      # Additional CSS classes
    **attrs                             # Additional HTML attributes
) -> HtmlString

# Usage examples
Pagination(total_pages=10)
Pagination(total_pages=20, show_first_last=True)
Pagination(total_pages=5, signal_name="products_page")
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Accessibility",
            Ul(
                Li("nav element with role='navigation'"),
                Li("aria-label='Pagination' for context"),
                Li("aria-current='page' on current page"),
                Li("aria-label on all buttons describing their action"),
                Li("Keyboard navigable via Tab"),
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/pagination")
@template(title="Pagination Component Documentation")
def pagination_page():
    return page

@on("page.pagination")
async def get_pagination(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.pagination")