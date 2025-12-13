# Feature: Avatar Component

**Status**: Pending  
**Phase**: 4 - Navigation & Display  
**Priority**: Low  

## Overview

Avatar component with image and fallback initials support.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/avatar.py`  
**CSS**: Custom CSS file

### API

```python
def Avatar(
    src: str = "",
    alt: str = "",
    fallback: str = "",
    size: str = "md",  # xs, sm, md, lg, xl
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
# With image
Avatar(src="/user.jpg", alt="John Doe", size="md")

# With fallback initials
Avatar(alt="John Doe", size="lg")  # Shows "JO"

# Explicit fallback
Avatar(fallback="AB", size="sm")
```

## Key Behaviors

- Shows image if src provided
- Falls back to initials (first 2 chars of alt or fallback)
- Multiple size options

## Documentation Page

**File**: `nitro/docs_app/pages/components/avatar.py`  
**Route**: `/components/avatar`

### Required Examples
- With image
- With fallback initials
- All sizes
- Avatar group

## Acceptance Criteria

- [ ] Image displays correctly
- [ ] Fallback initials work
- [ ] All sizes render correctly
- [ ] Proper alt text
- [ ] Documentation shows examples
- [ ] Pyright passes

