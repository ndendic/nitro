# Feature: Pagination Component

**Status**: Pending  
**Phase**: 4 - Navigation & Display  
**Priority**: Medium  

## Overview

Pagination component with Datastar signal for page state.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/pagination.py`  
**CSS**: Custom CSS file

### API

```python
def Pagination(
    total_pages: int,
    signal: str = "page",
    current_page: int = 1,
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
# Basic pagination
Pagination(total_pages=10, current_page=1)

# With custom signal name
Pagination(total_pages=20, signal="products_page")
```

## Key Behaviors

- Previous/Next buttons
- Page number display
- Disabled at boundaries
- Signal updates on navigation

## Documentation Page

**File**: `nitro/docs_app/pages/components/pagination.py`  
**Route**: `/components/pagination`

### Required Examples
- Basic pagination
- With page content changing
- Edge cases (first/last page)

## Acceptance Criteria

- [ ] Previous/Next buttons work
- [ ] Page signal updates
- [ ] Buttons disabled at boundaries
- [ ] ARIA labels present
- [ ] Documentation shows signal changes
- [ ] Pyright passes

