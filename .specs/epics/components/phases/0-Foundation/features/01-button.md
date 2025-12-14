# Feature: Button Component

**Status**: Pending  
**Phase**: 0 - Foundation  
**Priority**: High  

## Overview

Button component with Basecoat variant system. Pure styling, no Datastar reactivity needed.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/button.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/button.css`

### Basecoat Pattern

Combined class names: `btn-{size}-{variant}` or `btn-{variant}` for default size.

- **Sizes**: `sm`, default (no prefix), `lg`, `icon`
- **Variants**: `primary` (default), `secondary`, `outline`, `ghost`, `link`, `destructive`
- **Examples**: `btn`, `btn-secondary`, `btn-sm-outline`, `btn-lg-ghost`, `btn-icon-destructive`

### API

```python
def Button(
    *children,
    variant: str = "primary",  # primary, secondary, ghost, destructive, outline, link
    size: str = "md",          # sm, md, lg, icon
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
Button("Click me")                     # btn (primary, md)
Button("Small", size="sm")             # btn-sm
Button("Ghost", variant="ghost")       # btn-ghost
Button("Small Outline", size="sm", variant="outline")  # btn-sm-outline
Button(LucideIcon("settings"), size="icon")  # btn-icon
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/button.py`  
**Route**: `/components/button`

### Required Examples
- Basic variants (primary, secondary)
- All variants gallery
- Size options
- Disabled state
- Icon buttons

## Acceptance Criteria

- [ ] Component renders correct Basecoat classes
- [ ] All size/variant combinations work
- [ ] Disabled state applies correctly
- [ ] cls parameter appends Tailwind overrides
- [ ] Documentation page renders with examples
- [ ] Visual test passes

