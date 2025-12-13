# Feature: Popover Component

**Status**: Completed  
**Phase**: 2 - Interactive Overlays  
**Priority**: High  

## Overview

Popover container for positioned overlays. Uses compound component pattern with Datastar signals.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/popover.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/popover.css`

### Basecoat Pattern

- `.popover` container
- `.popover-content` for content panel

### API

```python
def Popover(*children, id: str = "", cls: str = "", **attrs) -> HtmlString:
def PopoverTrigger(*children, cls: str = "", **attrs):  # Closure pattern
def PopoverContent(*children, side: str = "bottom", align: str = "center", cls: str = "", **attrs):  # Closure pattern
```

### Usage Examples

```python
Popover(
    PopoverTrigger(Button("Open Popover")),
    PopoverContent(
        H4("Settings"),
        P("Configure your preferences here."),
        side="bottom",
        align="start",
    ),
)
```

## Key Behaviors

- Opens on trigger click
- Closes on click outside
- Closes on Escape key
- Positioning via data attributes

## Documentation Page

**File**: `nitro/docs_app/pages/components/popover.py`  
**Route**: `/components/popover`

### Required Examples
- Basic popover
- Different positioning (top, bottom, left, right)
- With form content
- Custom alignment

## Acceptance Criteria

- [x] Opens/closes correctly
- [x] Click outside closes
- [x] Escape key closes
- [x] Positioning options work
- [x] ARIA attributes present
- [x] Documentation shows all positions
- [ ] Pyright passes

