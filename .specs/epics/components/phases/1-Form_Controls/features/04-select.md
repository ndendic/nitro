# Feature: Select Component

**Status**: Pending  
**Phase**: 1 - Form Controls  
**Priority**: High  

## Overview

Native select component with Datastar binding. Uses Basecoat context-based styling.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/select.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/form/select.css`

### Basecoat Pattern

Context-based: styled inside `.field` or with `.input` class.

### API

```python
def Select(
    *children,
    id: str,
    bind: Signal = None,
    placeholder: str = "Select...",
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:

def SelectOption(
    *children,
    value: str,
    disabled: bool = False,
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
from nitro.infrastructure.html.datastar import Signals

form = Signals(size="md")

Field(
    Select(
        SelectOption("Small", value="sm"),
        SelectOption("Medium", value="md"),
        SelectOption("Large", value="lg"),
        id="size",
        bind=form.size,
    ),
    label="Size",
    label_for="size",
)
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/select.py`  
**Route**: `/components/select`

### Required Examples
- Basic select with options
- Select with Datastar binding
- Placeholder option
- Disabled options

## Acceptance Criteria

- [ ] Select renders with options
- [ ] Datastar binding updates signal
- [ ] Placeholder shows correctly
- [ ] Disabled state works
- [ ] Documentation shows signal changes
- [ ] Pyright passes

