# Feature: Input Group Component

**Status**: Completed  
**Phase**: 1 - Form Controls  
**Priority**: Low  

## Overview

Container for input with prefix/suffix elements. Uses Tailwind utility classes.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/input_group.py`  
**CSS**: Uses Tailwind utility classes (no custom CSS)

### API

```python
def InputGroup(*children, cls: str = "", **attrs) -> HtmlString:
def InputPrefix(*children, cls: str = "", **attrs) -> HtmlString:
def InputSuffix(*children, cls: str = "", **attrs) -> HtmlString:
```

### Usage Examples

```python
InputGroup(
    InputPrefix("$"),
    Input(type="number", id="price"),
    InputSuffix(".00"),
)

InputGroup(
    InputPrefix(LucideIcon("search")),
    Input(type="text", id="search", placeholder="Search..."),
)

InputGroup(
    Input(type="text", id="website"),
    InputSuffix(".com"),
)
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/input-group.py`  
**Route**: `/components/input-group`

### Required Examples
- Prefix with text
- Suffix with text
- Prefix with icon
- Both prefix and suffix

## Acceptance Criteria

- [x] Prefix/suffix render correctly
- [x] Border radius handled at edges
- [x] Input fills available space
- [x] Icons render in prefix/suffix
- [x] Documentation shows examples
- [x] Pyright passes (components import without errors)

