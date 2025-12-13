# Feature: Tooltip Component

**Status**: Pending  
**Phase**: 2 - Interactive Overlays  
**Priority**: Medium  

## Overview

Pure CSS tooltip using Basecoat's data-tooltip pattern. No JavaScript/Datastar needed.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/tooltip.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/tooltip.css`

### Basecoat Pattern

Uses `data-tooltip` attribute with `data-side` and `data-align` for positioning.

### API

```python
def Tooltip(
    *children,
    content: str,
    side: str = "top",      # top, bottom, left, right
    align: str = "center",  # center, start, end
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
Tooltip(
    Button("Hover me"),
    content="This is a tooltip!",
    side="bottom",
)

Tooltip(
    LucideIcon("info"),
    content="More information",
    side="right",
)
```

## Key Behaviors

- Appears on hover (CSS only)
- Positioning via data attributes
- No JavaScript required

## Documentation Page

**File**: `nitro/docs_app/pages/components/tooltip.py`  
**Route**: `/components/tooltip`

### Required Examples
- Basic tooltip
- Different positions
- With icons
- On buttons

## Acceptance Criteria

- [ ] Tooltip appears on hover
- [ ] All positioning options work
- [ ] No JavaScript needed
- [ ] Works on any element
- [ ] Documentation shows all positions
- [ ] Pyright passes

