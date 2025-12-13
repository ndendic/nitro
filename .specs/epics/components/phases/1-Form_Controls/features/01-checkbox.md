# Feature: Checkbox Component

**Status**: Pending  
**Phase**: 1 - Form Controls  
**Priority**: High  

## Overview

Checkbox input with Datastar two-way binding. Uses Basecoat's context-based styling inside Field.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/checkbox.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/form/checkbox.css`

### Basecoat Pattern

Context-based: styled inside `.field` or with `.input[type='checkbox']`.

### API

```python
def Checkbox(
    *children,
    id: str,
    bind: Signal = None,
    checked: bool = False,
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
from nitro.infrastructure.html.datastar import Signal, Signals

# With Signals object
form = Signals(accepted=False)
Field(
    Checkbox("Accept terms", id="terms", bind=form.accepted),
)

# With standalone Signal
accepted = Signal("accepted", False)
Checkbox("I agree", id="agree", bind=accepted)
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/checkbox.py`  
**Route**: `/components/checkbox`

### Required Examples
- Basic checkbox with label
- Checkbox with Datastar binding
- Signal state visualization
- Disabled state

## Acceptance Criteria

- [ ] Checkbox toggles correctly
- [ ] Datastar bind updates signal
- [ ] Label clicking toggles checkbox
- [ ] Disabled state works
- [ ] Documentation shows signal changes
- [ ] Pyright passes

