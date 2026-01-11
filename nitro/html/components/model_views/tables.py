"""ModelTable component for generating data tables from BaseModel classes.

Provides automatic table generation with column headers, sorting, actions,
and cell formatting based on field metadata.
"""

from typing import Type, List, Dict, Any, Optional, Callable
from rusty_tags import Div, HtmlString, Span
from rusty_tags.datastar import Signals
from pydantic import BaseModel
from nitro.html.components import (
    Table,
    TableHeader,
    TableBody,
    TableRow,
    TableHead,
    TableCell,
    Button,
    Badge,
    Checkbox,
    DropdownMenu,
    DropdownTrigger,
    DropdownContent,
    DropdownItem,
)
from .fields import get_model_fields


def ModelTable(
    entity_class: Type[BaseModel],
    data: Optional[List[BaseModel]] = None,
    exclude_fields: Optional[List[str]] = None,
    sortable: bool = True,
    actions: bool = True,
    on_edit: Optional[str] = None,
    on_delete: Optional[str] = None,
    empty_message: str = "No items found",
    formatters: Optional[Dict[str, Callable]] = None,
    signals: Optional[Signals] = None,
    page_size: Optional[int] = None,
    server_side: bool = False,
    selectable: bool = False,
    bulk_actions: Optional[List[Dict[str, Any]]] = None,
    column_toggle: bool = False,
) -> HtmlString:
    """Generate a data table from BaseModel class with advanced features.

    Creates a complete table with headers and rows based on BaseModel field metadata.
    Supports sorting, pagination, row selection, bulk actions, column visibility,
    action buttons, custom formatters, and automatic data fetching.

    Args:
        entity_class: BaseModel class to generate table for
        data: List of entity instances (defaults to BaseModel.all() if None)
        exclude_fields: Field names to exclude from columns (default: ['id'])
        sortable: Enable sortable headers (default True)
        actions: Include Edit/Delete action buttons (default True)
        on_edit: Datastar expression for edit action (use {id} placeholder)
        on_delete: Datastar expression for delete action (use {id} placeholder)
        empty_message: Message to show when no data
        formatters: Dict of field_name -> formatter function
        signals: Optional Signals object for table state
        page_size: Number of rows per page (enables pagination)
        server_side: Use server-side pagination/sorting via BaseModel.filter()
        selectable: Add checkboxes for row selection
        bulk_actions: List of bulk action configs (requires selectable=True)
        column_toggle: Add dropdown to show/hide columns

    Returns:
        HtmlString: Complete table component with headers, rows, and controls

    Example:
        # Basic table
        ModelTable(User, data=users)

        # With pagination and sorting
        ModelTable(
            Product,
            page_size=10,
            sortable=True,
            exclude_fields=['id', 'created_at'],
        )

        # With row selection and bulk actions
        ModelTable(
            Order,
            selectable=True,
            bulk_actions=[
                {'label': 'Delete', 'action': '$bulkDelete', 'variant': 'destructive'},
            ],
            column_toggle=True,
        )

        # Server-side with all features
        ModelTable(
            User,
            server_side=True,
            page_size=20,
            sortable=True,
            selectable=True,
            bulk_actions=[{'label': 'Archive', 'action': '$bulkArchive'}],
        )
    """
    # Default exclusions
    if exclude_fields is None:
        exclude_fields = ['id']

    # Default formatters
    if formatters is None:
        formatters = {}

    # Create comprehensive signals for table state if not provided
    if signals is None:
        signals = Signals(
            sort_field='',
            sort_direction='',
            current_page=1,
            total_pages=1,
            selected_ids=[],
            visible_columns=None,  # None means all visible
        )

    # Get field metadata
    fields = get_model_fields(entity_class, exclude=exclude_fields)

    # Filter out hidden fields
    visible_fields = [
        f for f in fields.values()
        if not f.get('extra', {}).get('hidden_in_table', False)
    ]

    # Handle pagination and data fetching
    if page_size and server_side:
        # Server-side pagination: use BaseModel.filter
        # For server-side, we always fetch from the backend
        all_data = entity_class.all()
        total_count = len(all_data)
        total_pages = (total_count + page_size - 1) // page_size
        signals.total_pages = total_pages

        # Ensure current_page is an integer
        current_page = getattr(signals, 'current_page', 1)
        if not isinstance(current_page, int):
            current_page = 1
        offset = (current_page - 1) * page_size

        # Call filter with pagination and sorting params
        filter_kwargs = {
            'limit': page_size,
            'offset': offset,
        }

        sort_field = getattr(signals, 'sort_field', '')
        sort_direction = getattr(signals, 'sort_direction', 'asc')

        if sort_field:
            filter_kwargs['sorting_field'] = sort_field
            filter_kwargs['sort_direction'] = sort_direction

        # Always call filter for server-side mode
        data = entity_class.filter(**filter_kwargs)

    elif page_size:
        # Client-side pagination: slice data
        if data is None:
            data = entity_class.all()

        total_count = len(data)
        total_pages = (total_count + page_size - 1) // page_size
        signals.total_pages = total_pages

        # Ensure current_page is an integer
        current_page = getattr(signals, 'current_page', 1)
        if not isinstance(current_page, int):
            current_page = 1
        start = (current_page - 1) * page_size
        end = start + page_size
        data = data[start:end]

    else:
        # No pagination: fetch all data if not provided
        if data is None:
            data = entity_class.all()

    # Build headers
    headers = []

    # Add selection checkbox column header if selectable
    if selectable:
        headers.append(
            TableHead(
                Checkbox(
                    id="select-all",
                    on_change="$toggleSelectAll()",
                ),
                cls="w-12",
            )
        )

    for field in visible_fields:
        # Check if this field is sortable
        field_sortable = sortable and field.get('extra', {}).get('sortable', True)

        if field_sortable:
            # Generate sort expression for Datastar
            sort_expr = f"$sort_field='{field['name']}';$sort_direction=$sort_direction==='asc'?'desc':'asc'"

            headers.append(
                TableHead(
                    field['title'],
                    sortable=True,
                    sort_direction=f"$sort_field==='{field['name']}'?$sort_direction:''",
                    on_sort=sort_expr,
                )
            )
        else:
            headers.append(TableHead(field['title']))

    # Add actions header
    if actions:
        headers.append(TableHead("Actions", cls="text-right"))

    # Build rows
    rows = []
    for entity in data:
        cells = []

        # Add selection checkbox cell if selectable
        if selectable:
            entity_id = str(entity.id)
            # Pass datastar attribute for dynamic checked state via **attrs
            cells.append(
                TableCell(
                    Checkbox(
                        id=f"select-{entity_id}",
                        on_change=f"$toggleSelection('{entity_id}')",
                        **{"data-attr:checked": f"$selected_ids.includes('{entity_id}')"}
                    ),
                    cls="w-12",
                )
            )

        # Add data cells
        for field in visible_fields:
            value = getattr(entity, field['name'], None)

            # Apply custom formatter if available
            if field['name'] in formatters:
                cell_content = formatters[field['name']](value)
            else:
                cell_content = format_cell_value(value, field)

            cells.append(TableCell(cell_content))

        # Add action buttons
        if actions:
            action_buttons = []

            if on_edit:
                edit_action = on_edit.replace('{id}', str(entity.id))
                action_buttons.append(
                    Button("Edit", variant="outline", size="sm", on_click=edit_action)
                )
            else:
                action_buttons.append(
                    Button("Edit", variant="outline", size="sm")
                )

            if on_delete:
                delete_action = on_delete.replace('{id}', str(entity.id))
                action_buttons.append(
                    Button("Delete", variant="destructive", size="sm", on_click=delete_action)
                )
            else:
                action_buttons.append(
                    Button("Delete", variant="destructive", size="sm")
                )

            cells.append(
                TableCell(
                    Div(*action_buttons, cls="flex justify-end gap-2")
                )
            )

        rows.append(TableRow(*cells))

    # Handle empty state
    if not rows:
        col_span = len(visible_fields) + (1 if actions else 0) + (1 if selectable else 0)
        rows.append(
            TableRow(
                TableCell(
                    Div(empty_message, cls="text-center text-muted-foreground py-8"),
                    colspan=col_span,
                )
            )
        )

    # Build the table
    table = Table(
        TableHeader(TableRow(*headers)),
        TableBody(*rows),
        signals=signals,
    )

    # Build controls wrapper
    controls = []

    # Column visibility toggle
    if column_toggle:
        controls.append(_column_toggle(visible_fields, signals))

    # Bulk actions bar
    if bulk_actions and selectable:
        controls.append(_bulk_action_bar(bulk_actions, signals))

    # Pagination controls
    if page_size:
        controls.append(_table_pagination(signals))

    # Return table with controls if any, otherwise just table
    if controls:
        return Div(
            Div(*controls, cls="flex justify-between items-center mb-4"),
            table,
            cls="space-y-4",
        )
    else:
        return table


def format_cell_value(value: Any, field: Dict[str, Any]) -> Any:
    """Format cell value based on field type.

    Args:
        value: The field value to format
        field: Field metadata dict from get_model_fields()

    Returns:
        Formatted value (str, Badge, or other component)

    Example:
        # Boolean -> Badge
        format_cell_value(True, {'type': 'boolean'})  # Badge("Yes")

        # Date -> formatted string
        format_cell_value(date(2024, 1, 15), {'format': 'date'})  # "2024-01-15"

        # None -> dash
        format_cell_value(None, {})  # "-"
    """
    if value is None:
        return "-"

    field_type = field.get('type')
    field_format = field.get('format')

    # Boolean formatting
    if field_type == 'boolean':
        if value:
            return Badge("Yes", variant="secondary")
        else:
            return Badge("No", variant="outline")

    # Date formatting
    if field_format == 'date':
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)

    # DateTime formatting
    if field_format == 'date-time':
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M')
        return str(value)

    # Default: string conversion
    return str(value)


def _column_toggle(fields: List[Dict[str, Any]], signals: Signals) -> HtmlString:
    """Column visibility toggle dropdown.

    Args:
        fields: List of field metadata dicts
        signals: Signals object containing visible_columns

    Returns:
        HtmlString: DropdownMenu with column checkboxes
    """
    return DropdownMenu(
        DropdownTrigger(
            Button(
                "Columns",
                variant="outline",
                size="sm",
            ),
        ),
        DropdownContent(
            *[
                DropdownItem(
                    Checkbox(
                        f['title'],
                        id=f"col-{f['name']}",
                        # Use data-attr for dynamic checked state
                        **{"data-attr:checked": f"$visible_columns === null || $visible_columns.includes('{f['name']}')"},
                        on_change=f"$toggleColumn('{f['name']}')",
                    ),
                )
                for f in fields
            ],
            cls="w-48",
        ),
    )


def _bulk_action_bar(actions: List[Dict[str, Any]], signals: Signals) -> HtmlString:
    """Bulk action buttons that operate on selected rows.

    Args:
        actions: List of action configs with 'label', 'action', and optional 'variant'
        signals: Signals object containing selected_ids

    Returns:
        HtmlString: Div containing selection count and action buttons

    Example action config:
        [
            {'label': 'Delete', 'action': '$bulkDelete', 'variant': 'destructive'},
            {'label': 'Archive', 'action': '$bulkArchive', 'variant': 'outline'},
        ]
    """
    return Div(
        Span(
            "$selected_ids.length",
            " selected",
            cls="text-sm text-muted-foreground mr-4",
            data_show="$selected_ids.length > 0",
        ),
        *[
            Button(
                action['label'],
                variant=action.get('variant', 'outline'),
                size="sm",
                on_click=f"{action['action']}($selected_ids)",
                disabled="$selected_ids.length === 0",
            )
            for action in actions
        ],
        cls="flex items-center gap-2",
    )


def _table_pagination(signals: Signals) -> HtmlString:
    """Pagination controls for table.

    Args:
        signals: Signals object with current_page and total_pages

    Returns:
        HtmlString: Div with page info and navigation buttons
    """
    return Div(
        # Info text
        Span(
            "Page ",
            Span("$current_page"),
            " of ",
            Span("$total_pages"),
            cls="text-sm text-muted-foreground",
        ),
        # Navigation buttons
        Div(
            Button(
                "Previous",
                variant="outline",
                size="sm",
                on_click="$current_page = Math.max(1, $current_page - 1)",
                disabled="$current_page <= 1",
            ),
            Button(
                "Next",
                variant="outline",
                size="sm",
                on_click="$current_page = Math.min($total_pages, $current_page + 1)",
                disabled="$current_page >= $total_pages",
            ),
            cls="flex gap-2",
        ),
        cls="flex justify-between items-center",
    )
