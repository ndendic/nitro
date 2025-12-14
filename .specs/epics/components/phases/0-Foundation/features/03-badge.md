# Feature: Badge Component

**Status**: Pending  
**Phase**: 0 - Foundation  
**Priority**: High  

## Overview

Badge component for labels and status indicators using Basecoat variant suffix pattern.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/badge.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/badge.css`

### Basecoat Pattern

Variant suffix pattern:
- `.badge` or `.badge-primary` (default)
- `.badge-secondary`, `.badge-destructive`, `.badge-outline`

### API

```python
def Badge(
    *children,
    variant: str = "primary",  # primary, secondary, destructive, outline
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
Badge("New")                          # badge (primary)
Badge("Draft", variant="secondary")   # badge-secondary
Badge("Error", variant="destructive") # badge-destructive
Badge("v1.0", variant="outline")      # badge-outline
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/badge.py`  
**Route**: `/components/badge`

### Required Examples
- Basic badge
- All variants
- Badges in context (cards, lists)
- Custom styling with cls

## Acceptance Criteria

- [ ] Badge outputs correct Basecoat classes
- [ ] All variants render correctly
- [ ] cls parameter allows overrides
- [ ] Documentation page renders
- [ ] Visual test passes

