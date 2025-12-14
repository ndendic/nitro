# Feature: Table Component

**Status**: Completed  
**Phase**: 4 - Navigation & Display  
**Priority**: High  

## Overview

Table components with Basecoat styling and optional sortable headers.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/table.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/table.css`

### API

```python
def Table(*children, cls: str = "", **attrs) -> HtmlString:
def TableHeader(*children, cls: str = "", **attrs) -> HtmlString:
def TableBody(*children, cls: str = "", **attrs) -> HtmlString:
def TableRow(*children, cls: str = "", **attrs) -> HtmlString:
def TableHead(*children, sortable: bool = False, sort_direction: str = "", on_sort: str = "", cls: str = "", **attrs) -> HtmlString:
def TableCell(*children, cls: str = "", **attrs) -> HtmlString:
```

### Usage Examples

```python
Table(
    TableHeader(
        TableRow(
            TableHead("Name", sortable=True, on_sort="sortBy('name')"),
            TableHead("Email"),
            TableHead("Status"),
        ),
    ),
    TableBody(
        TableRow(
            TableCell("John Doe"),
            TableCell("john@example.com"),
            TableCell(Badge("Active")),
        ),
    ),
)
```

## Key Behaviors

- Semantic table structure
- Hover states on rows
- Sortable column indicators
- Responsive considerations

## Documentation Page

**File**: `nitro/docs_app/pages/components/table.py`  
**Route**: `/components/table`

### Required Examples
- Basic table
- With sortable columns
- With badges/actions
- Responsive table

## Acceptance Criteria

- [x] Table renders correctly
- [x] Basecoat styling applied
- [x] Sortable headers clickable
- [x] Row hover states work
- [x] Documentation shows data-driven example
- [x] Visual test passes

