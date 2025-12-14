# Feature: Label Component

**Status**: Pending  
**Phase**: 0 - Foundation  
**Priority**: Medium  

## Overview

Label component for form inputs. Context-based styling inside Field, explicit `.label` class for standalone use.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/label.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/form/label.css`

### Basecoat Pattern

Labels inside `.field` wrapper are auto-styled by Basecoat. Use `.label` class for standalone labels.

### API

```python
def Label(
    *children,
    for_id: str = "",
    required: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
Label("Email", for_id="email")
Label("Name", for_id="name", required=True)  # Shows * indicator
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/label.py`  
**Route**: `/components/label`

### Required Examples
- Basic label
- Label with required indicator
- Label with input

## Acceptance Criteria

- [ ] Label outputs correct class
- [ ] for_id creates htmlFor attribute
- [ ] required shows indicator
- [ ] Documentation page renders
- [ ] Visual test passes

