# Feature: Switch Component

**Status**: Completed
**Phase**: 1 - Form Controls
**Priority**: High  

## Overview

Toggle switch component using native checkbox with role="switch" for Basecoat styling.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/switch.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/form/switch.css`

### Basecoat Pattern

Uses `input[type='checkbox'][role='switch']` pattern.

### API

```python
def Switch(
    *children,
    id: str,
    bind: Signal = None,
    checked: bool = False,
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
from nitro.infrastructure.html.datastar import Signals

settings = Signals(notifications=True, dark_mode=False)

Switch("Enable notifications", id="notifications", bind=settings.notifications)
Switch("Dark mode", id="dark", bind=settings.dark_mode)
```

## Documentation Page

**File**: `nitro/docs_app/pages/switch.py`
**Route**: `/xtras/switch`

### Required Examples
- Basic switch with label
- Switch with Datastar binding
- Multiple switches (settings panel)
- Disabled state

## Acceptance Criteria

- [x] Switch toggles smoothly
- [x] role="switch" attribute present
- [x] Datastar binding updates signal
- [x] CSS animation works
- [x] Documentation shows signal changes
- [ ] Visual test passes

