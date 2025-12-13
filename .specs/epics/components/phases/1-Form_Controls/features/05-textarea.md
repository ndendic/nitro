# Feature: Textarea Component

**Status**: Pending  
**Phase**: 1 - Form Controls  
**Priority**: Medium  

## Overview

Textarea component with Datastar two-way binding. Uses Basecoat context-based styling.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/textarea.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/form/textarea.css`

### Basecoat Pattern

Context-based: styled inside `.field` or with `.input` class.

### API

```python
def Textarea(
    *children,
    id: str,
    bind: Signal = None,
    placeholder: str = "",
    rows: int = 3,
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
from nitro.infrastructure.html.datastar import Signals

form = Signals(bio="")

Field(
    Textarea(
        id="bio",
        bind=form.bio,
        placeholder="Tell us about yourself...",
        rows=5,
    ),
    label="Bio",
    label_for="bio",
)
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/textarea.py`  
**Route**: `/components/textarea`

### Required Examples
- Basic textarea
- Textarea with Datastar binding
- Character count visualization
- Different row sizes

## Acceptance Criteria

- [ ] Textarea renders correctly
- [ ] Datastar binding updates signal
- [ ] Rows attribute works
- [ ] Placeholder shows
- [ ] Documentation shows real-time signal updates
- [ ] Pyright passes

