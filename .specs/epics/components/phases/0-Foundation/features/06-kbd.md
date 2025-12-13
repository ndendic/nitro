# Feature: Kbd Component

**Status**: Pending  
**Phase**: 0 - Foundation  
**Priority**: Low  

## Overview

Keyboard key component for displaying keyboard shortcuts.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/kbd.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/kbd.css`

### API

```python
def Kbd(*children, cls: str = "", **attrs) -> HtmlString:
```

### Usage Examples

```python
Kbd("⌘"), Kbd("K")          # For ⌘K shortcut
Kbd("Ctrl"), Kbd("+"), Kbd("C")  # For Ctrl+C
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/kbd.py`  
**Route**: `/components/kbd`

### Required Examples
- Single key
- Keyboard shortcuts
- In context (menu items, tooltips)

## Acceptance Criteria

- [ ] Kbd outputs `.kbd` class
- [ ] Styled correctly with Basecoat
- [ ] Documentation page renders
- [ ] Pyright passes

