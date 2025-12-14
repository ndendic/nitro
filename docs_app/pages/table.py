"""Table component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.responses import HTMLResponse
from fastapi import APIRouter

from nitro.infrastructure.html.components import (
    Table,
    TableHeader,
    TableBody,
    TableFooter,
    TableRow,
    TableHead,
    TableCell,
    TableCaption,
    Badge,
    Button,
    Avatar,
)

router: APIRouter = APIRouter()


def example_basic():
    """Basic table with simple data."""
    return Table(
        TableHeader(
            TableRow(
                TableHead("Name"),
                TableHead("Email"),
                TableHead("Role"),
            ),
        ),
        TableBody(
            TableRow(
                TableCell("John Doe"),
                TableCell("john@example.com"),
                TableCell("Developer"),
            ),
            TableRow(
                TableCell("Jane Smith"),
                TableCell("jane@example.com"),
                TableCell("Designer"),
            ),
            TableRow(
                TableCell("Bob Johnson"),
                TableCell("bob@example.com"),
                TableCell("Manager"),
            ),
        ),
    )


def example_with_badges():
    """Table with status badges in cells."""
    return Table(
        TableHeader(
            TableRow(
                TableHead("Invoice"),
                TableHead("Status"),
                TableHead("Amount"),
            ),
        ),
        TableBody(
            TableRow(
                TableCell("INV-001"),
                TableCell(Badge("Paid", variant="success")),
                TableCell("$250.00"),
            ),
            TableRow(
                TableCell("INV-002"),
                TableCell(Badge("Pending", variant="warning")),
                TableCell("$150.00"),
            ),
            TableRow(
                TableCell("INV-003"),
                TableCell(Badge("Overdue", variant="destructive")),
                TableCell("$350.00"),
            ),
        ),
    )


def example_with_actions():
    """Table with action buttons in cells."""
    return Table(
        TableHeader(
            TableRow(
                TableHead("User"),
                TableHead("Email"),
                TableHead("Actions", cls="text-right"),
            ),
        ),
        TableBody(
            TableRow(
                TableCell(
                    Div(
                        Avatar(alt="John Doe", size="sm"),
                        Span("John Doe", cls="ml-2"),
                        cls="flex items-center",
                    )
                ),
                TableCell("john@example.com"),
                TableCell(
                    Div(
                        Button("Edit", variant="outline", size="sm"),
                        Button("Delete", variant="destructive", size="sm", cls="ml-2"),
                        cls="flex justify-end",
                    )
                ),
            ),
            TableRow(
                TableCell(
                    Div(
                        Avatar(alt="Jane Smith", size="sm"),
                        Span("Jane Smith", cls="ml-2"),
                        cls="flex items-center",
                    )
                ),
                TableCell("jane@example.com"),
                TableCell(
                    Div(
                        Button("Edit", variant="outline", size="sm"),
                        Button("Delete", variant="destructive", size="sm", cls="ml-2"),
                        cls="flex justify-end",
                    )
                ),
            ),
        ),
    )


def example_sortable():
    """Table with sortable column headers."""
    return Table(
        TableHeader(
            TableRow(
                TableHead("Name", sortable=True, sort_direction="asc"),
                TableHead("Email", sortable=True),
                TableHead("Created", sortable=True, sort_direction="desc"),
            ),
        ),
        TableBody(
            TableRow(
                TableCell("Alice Brown"),
                TableCell("alice@example.com"),
                TableCell("2024-01-15"),
            ),
            TableRow(
                TableCell("Bob White"),
                TableCell("bob@example.com"),
                TableCell("2024-01-10"),
            ),
            TableRow(
                TableCell("Charlie Green"),
                TableCell("charlie@example.com"),
                TableCell("2024-01-05"),
            ),
        ),
    )


def example_with_footer():
    """Table with footer for totals."""
    return Table(
        TableHeader(
            TableRow(
                TableHead("Item"),
                TableHead("Quantity"),
                TableHead("Price", cls="text-right"),
            ),
        ),
        TableBody(
            TableRow(
                TableCell("Product A"),
                TableCell("2"),
                TableCell("$50.00", cls="text-right"),
            ),
            TableRow(
                TableCell("Product B"),
                TableCell("1"),
                TableCell("$75.00", cls="text-right"),
            ),
            TableRow(
                TableCell("Product C"),
                TableCell("3"),
                TableCell("$30.00", cls="text-right"),
            ),
        ),
        TableFooter(
            TableRow(
                TableCell("Total", colspan="2"),
                TableCell("$265.00", cls="text-right font-bold"),
            ),
        ),
    )


def example_with_caption():
    """Table with caption for accessibility."""
    return Table(
        TableCaption("A list of recent transactions"),
        TableHeader(
            TableRow(
                TableHead("Transaction"),
                TableHead("Date"),
                TableHead("Amount"),
            ),
        ),
        TableBody(
            TableRow(
                TableCell("Payment received"),
                TableCell("2024-01-15"),
                TableCell("+$500.00", cls="text-green-600"),
            ),
            TableRow(
                TableCell("Subscription renewal"),
                TableCell("2024-01-14"),
                TableCell("-$29.99", cls="text-red-600"),
            ),
            TableRow(
                TableCell("Refund processed"),
                TableCell("2024-01-12"),
                TableCell("+$15.00", cls="text-green-600"),
            ),
        ),
    )


@router.get("/xtras/table")
@template(title="Table Component Documentation")
def table_docs():
    return Div(
        H1("Table Component"),
        P(
            "A responsive table component with Basecoat styling, "
            "sortable headers, and support for rich cell content."
        ),
        TitledSection(
            "Design Philosophy",
            P("Table follows Basecoat and semantic HTML patterns:"),
            Ul(
                Li("Uses native table elements (table, thead, tbody, tr, th, td)"),
                Li("Basecoat `.table` class for consistent styling"),
                Li("Hover states on rows for better readability"),
                Li("Border separators between rows"),
                Li("Support for captions for accessibility"),
                Li("Sortable columns with visual indicators"),
            ),
        ),
        TitledSection(
            "Basic Usage",
            P("A simple table with header and data rows:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "With Status Badges",
            P("Tables can contain any components in cells, including badges:"),
            ComponentShowcase(example_with_badges),
        ),
        TitledSection(
            "With Actions",
            P("Add action buttons and avatars for interactive tables:"),
            ComponentShowcase(example_with_actions),
        ),
        TitledSection(
            "Sortable Columns",
            P("Headers can show sort direction indicators:"),
            ComponentShowcase(example_sortable),
        ),
        TitledSection(
            "With Footer",
            P("Use TableFooter for totals or summaries:"),
            ComponentShowcase(example_with_footer),
        ),
        TitledSection(
            "With Caption",
            P("Add captions for accessibility and context:"),
            ComponentShowcase(example_with_caption),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
def Table(*children, cls: str = "", **attrs) -> HtmlString
def TableHeader(*children, cls: str = "", **attrs) -> HtmlString
def TableBody(*children, cls: str = "", **attrs) -> HtmlString
def TableFooter(*children, cls: str = "", **attrs) -> HtmlString
def TableRow(*children, selected: bool = False, cls: str = "", **attrs) -> HtmlString
def TableHead(
    *children,
    sortable: bool = False,
    sort_direction: str = "",  # "asc", "desc", or ""
    on_sort: str = "",         # Datastar expression
    cls: str = "",
    **attrs
) -> HtmlString
def TableCell(*children, cls: str = "", **attrs) -> HtmlString
def TableCaption(*children, cls: str = "", **attrs) -> HtmlString

# Example with sorting
Table(
    TableHeader(
        TableRow(
            TableHead("Name", sortable=True, on_sort="$sortBy='name'"),
            TableHead("Email"),
        ),
    ),
    TableBody(
        TableRow(TableCell("John"), TableCell("john@example.com")),
    ),
)
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Accessibility",
            Ul(
                Li("Semantic table elements (table, thead, tbody, th, td)"),
                Li("aria-sort attribute on sortable columns"),
                Li("TableCaption for table descriptions"),
                Li("data-state='selected' on selected rows"),
                Li("Proper contrast and hover states"),
            ),
        ),
        BackLink(),
    )
