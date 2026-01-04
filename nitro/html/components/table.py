"""Table component with Basecoat styling and optional sortable headers."""

from typing import Any, Literal, Optional
from rusty_tags import (
    Table as HTMLTable,
    Thead,
    Tbody,
    Tfoot,
    Tr,
    Th,
    Td,
    Caption,
    Div,
    Span,
    HtmlString,
)
from .utils import cn
from .icons import LucideIcon


SortDirection = Literal["asc", "desc", ""]


def Table(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Table container with Basecoat styling.

    A styled table component that applies Basecoat's table design patterns
    including hover states, borders, and consistent spacing.

    Args:
        *children: Table sections (TableHeader, TableBody, TableFooter, TableCaption)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered table element

    Example:
        Table(
            TableHeader(
                TableRow(
                    TableHead("Name"),
                    TableHead("Email"),
                ),
            ),
            TableBody(
                TableRow(
                    TableCell("John Doe"),
                    TableCell("john@example.com"),
                ),
            ),
        )
    """
    return HTMLTable(
        *children,
        cls=cn("table", cls),
        **attrs,
    )


def TableHeader(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Table header section (thead).

    Container for header rows that define column labels.

    Args:
        *children: TableRow components with TableHead cells
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered thead element
    """
    return Thead(
        *children,
        cls=cn(cls) if cls else None,
        **attrs,
    )


def TableBody(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Table body section (tbody).

    Container for data rows.

    Args:
        *children: TableRow components with TableCell cells
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered tbody element
    """
    return Tbody(
        *children,
        cls=cn(cls) if cls else None,
        **attrs,
    )


def TableFooter(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Table footer section (tfoot).

    Container for footer rows, typically used for totals or summaries.

    Args:
        *children: TableRow components
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered tfoot element
    """
    return Tfoot(
        *children,
        cls=cn(cls) if cls else None,
        **attrs,
    )


def TableRow(
    *children: Any,
    cls: str = "",
    selected: bool = False,
    **attrs: Any,
) -> HtmlString:
    """Table row (tr).

    A single row in the table, used in header, body, or footer.

    Args:
        *children: TableHead or TableCell components
        cls: Additional CSS classes
        selected: Whether the row is selected (adds visual indicator)
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered tr element
    """
    row_cls = cn(
        {"bg-muted": selected},
        cls,
    )
    return Tr(
        *children,
        cls=row_cls if row_cls.strip() else None,
        data_state="selected" if selected else None,
        **attrs,
    )


def TableHead(
    *children: Any,
    sortable: bool = False,
    sort_direction: SortDirection = "",
    on_sort: Optional[str] = None,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Table header cell (th).

    A header cell with optional sorting capability.

    Args:
        *children: Header content (text, icons, etc.)
        sortable: Whether this column is sortable
        sort_direction: Current sort direction ("asc", "desc", or "")
        on_sort: Datastar expression for sort action (e.g., "$sortBy='name'")
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered th element

    Example:
        # Non-sortable header
        TableHead("Email")

        # Sortable header
        TableHead("Name", sortable=True, on_sort="$sortColumn='name'")

        # Currently sorted header
        TableHead("Date", sortable=True, sort_direction="desc")
    """
    if sortable:
        # Build sortable header with icon
        sort_icon = ""
        if sort_direction == "asc":
            sort_icon = LucideIcon("chevron-up", cls="size-4 ml-1")
        elif sort_direction == "desc":
            sort_icon = LucideIcon("chevron-down", cls="size-4 ml-1")
        else:
            sort_icon = LucideIcon("chevrons-up-down", cls="size-4 ml-1 opacity-50")

        content = Div(
            Span(*children),
            sort_icon,
            cls="flex items-center cursor-pointer select-none hover:text-foreground",
            on_click=on_sort if on_sort else None,
        )

        return Th(
            content,
            cls=cn(cls),
            aria_sort="ascending" if sort_direction == "asc" else "descending" if sort_direction == "desc" else None,
            **attrs,
        )

    return Th(
        *children,
        cls=cn(cls) if cls else None,
        **attrs,
    )


def TableCell(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Table data cell (td).

    A single data cell in a table row.

    Args:
        *children: Cell content (text, badges, buttons, etc.)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered td element

    Example:
        TableCell("John Doe")
        TableCell(Badge("Active", variant="success"))
        TableCell(Button("Edit", size="sm"))
    """
    return Td(
        *children,
        cls=cn(cls) if cls else None,
        **attrs,
    )


def TableCaption(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Table caption.

    Provides a description or title for the table.

    Args:
        *children: Caption text
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered caption element
    """
    return Caption(
        *children,
        cls=cn(cls) if cls else None,
        **attrs,
    )
