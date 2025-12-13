# Feature: Alert Component

**Status**: Pending  
**Phase**: 0 - Foundation  
**Priority**: Medium  

## Overview

Alert component for contextual messages using Basecoat variant suffix pattern.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/alert.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/alert.css`

### Basecoat Pattern

Variant suffix pattern with semantic children:
- `.alert` (default)
- `.alert-destructive`
- Uses `h2/h3` for title, `section` for description

### API

```python
def Alert(
    *children,
    variant: str = "default",  # default, destructive
    cls: str = "",
    **attrs
) -> HtmlString:

def AlertTitle(*children, cls: str = "", **attrs) -> HtmlString:
def AlertDescription(*children, cls: str = "", **attrs) -> HtmlString:
```

### Usage Examples

```python
Alert(
    LucideIcon("info"),
    AlertTitle("Heads up!"),
    AlertDescription("You can add components to your app."),
)

Alert(
    LucideIcon("alert-triangle"),
    AlertTitle("Error"),
    AlertDescription("Something went wrong."),
    variant="destructive",
)
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/alert.py`  
**Route**: `/components/alert`

### Required Examples
- Default alert with icon
- Destructive alert
- Alert without icon

## Acceptance Criteria

- [ ] Alert outputs correct Basecoat classes
- [ ] role="alert" is present
- [ ] AlertTitle and AlertDescription work
- [ ] Variants apply correctly
- [ ] Documentation page renders
- [ ] Pyright passes

