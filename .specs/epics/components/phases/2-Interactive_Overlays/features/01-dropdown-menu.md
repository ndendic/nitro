# Feature: Dropdown Menu Component

**Status**: Completed  
**Phase**: 2 - Interactive Overlays  
**Priority**: High  

## Overview

Dropdown menu with compound component pattern. Uses Datastar signals for visibility, Basecoat CSS for styling.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/dropdown.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/dropdown-menu.css`

### Basecoat Pattern

- `.dropdown-menu` container
- `[role='menuitem']` for items

### API

```python
def DropdownMenu(*children, id: str = "", cls: str = "", **attrs) -> HtmlString:
def DropdownTrigger(*children, cls: str = "", **attrs):  # Closure pattern
def DropdownContent(*children, align: str = "start", cls: str = "", **attrs):  # Closure pattern
def DropdownItem(*children, on_click=None, disabled: bool = False, cls: str = "", **attrs) -> HtmlString:
def DropdownSeparator(cls: str = "", **attrs) -> HtmlString:
```

### Usage Examples

```python
DropdownMenu(
    DropdownTrigger(Button("Options", variant="outline")),
    DropdownContent(
        DropdownItem("Edit", on_click=handle_edit),
        DropdownSeparator(),
        DropdownItem("Delete", on_click=handle_delete),
    ),
)
```

## Key Behaviors

- Opens on trigger click
- Closes on click outside
- Closes on Escape key
- ARIA attributes for accessibility

## Documentation Page

**File**: `nitro/docs_app/pages/components/dropdown.py`  
**Route**: `/components/dropdown`

### Required Examples
- Basic dropdown
- With icons
- With separators
- Alignment options

## Acceptance Criteria

- [x] Opens/closes on trigger click
- [x] Click outside closes menu
- [x] Escape key closes menu
- [x] ARIA attributes present
- [ ] Keyboard navigation works
- [x] Documentation shows interaction
- [x] Visual test passes

