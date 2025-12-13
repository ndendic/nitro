# Feature: Field Component

**Status**: Completed  
**Phase**: 1 - Form Controls  
**Priority**: High  

## Overview

Form field wrapper providing Basecoat context styling. All inputs inside Field are automatically styled.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/field.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/field.css`

### Basecoat Pattern

`.field` class provides context-based styling. Uses semantic children:
- `h2/h3` for title
- `p` for description
- `[role="alert"]` for errors

### API

```python
def Field(
    *children,
    label: str = "",
    label_for: str = "",
    error: str = "",
    description: str = "",
    orientation: str = "vertical",  # vertical, horizontal
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
from nitro.infrastructure.html.datastar import Signals

form = Signals(email="")

Field(
    Input(type="email", id="email", bind=form.email),
    label="Email",
    label_for="email",
    description="We'll never share your email.",
)

Field(
    Input(type="text", id="name", bind=form.name),
    label="Name",
    label_for="name",
    error="Name is required",  # Shows error state
)
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/field.py`  
**Route**: `/components/field`

### Required Examples
- Basic field with input
- Field with description
- Field with error state
- Horizontal orientation
- Complete form example

## Acceptance Criteria

- [x] Field outputs `.field` class
- [x] Label renders correctly
- [x] Description shows below label
- [x] Error shows with alert role
- [x] data-invalid attribute set on error
- [x] Orientation option works
- [x] Documentation shows all states
- [x] Pyright passes (components import without errors)

