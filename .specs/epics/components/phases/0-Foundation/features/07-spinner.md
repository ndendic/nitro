# Feature: Spinner Component

**Status**: Pending  
**Phase**: 0 - Foundation  
**Priority**: Medium  

## Overview

Loading spinner component using Lucide loader icon with Tailwind animate-spin.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/spinner.py`  
**CSS**: Uses Tailwind's built-in `animate-spin` (no custom CSS)

### API

```python
def Spinner(
    size: str = "md",  # sm (16px), md (24px), lg (32px)
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
Spinner()
Spinner(size="lg", cls="text-primary")
Spinner(size="sm", cls="text-muted-foreground")
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/spinner.py`  
**Route**: `/components/spinner`

### Required Examples
- Default spinner
- Size variations
- Custom colors

## Acceptance Criteria

- [ ] Spinner renders with animation
- [ ] Size classes apply correctly
- [ ] Accessible with role="status" and aria-label
- [ ] Documentation page renders
- [ ] Visual test passes

