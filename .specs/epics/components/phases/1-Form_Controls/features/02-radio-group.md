# Feature: Radio Group Component

**Status**: Pending  
**Phase**: 1 - Form Controls  
**Priority**: High  

## Overview

Radio group with compound component pattern. Uses closure to pass Signal from parent to children.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/radio.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/form/radio.css`

### Basecoat Pattern

Context-based: styled inside `.field` or with `.input[type='radio']`.

### API

```python
def RadioGroup(
    *children,
    bind: Signal,
    orientation: str = "vertical",  # vertical, horizontal
    cls: str = "",
    **attrs
) -> HtmlString:

def RadioItem(
    *children,
    value: str,
    id: str = "",
    disabled: bool = False,
    cls: str = "",
    **attrs
):
    # Returns closure that receives Signal from parent
```

### Usage Examples

```python
from nitro.infrastructure.html.datastar import Signals

form = Signals(size="md")

RadioGroup(
    RadioItem("Small", value="sm"),
    RadioItem("Medium", value="md"),
    RadioItem("Large", value="lg"),
    bind=form.size,
)
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/radio.py`  
**Route**: `/components/radio`

### Required Examples
- Vertical radio group
- Horizontal orientation
- Signal state visualization
- Pre-selected value

## Acceptance Criteria

- [ ] Only one option can be selected
- [ ] Datastar binding updates signal
- [ ] Orientation options work
- [ ] Compound pattern passes signal correctly
- [ ] Documentation shows signal changes
- [ ] Pyright passes

