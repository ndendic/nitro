# Feature: Toast System

**Status**: Completed  
**Phase**: 3 - Feedback Components  
**Priority**: High  

## Overview

Toast notification system with provider pattern. Supports variants, auto-dismiss, and positioning.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/toast.py`  
**CSS**: Custom CSS file

### API

```python
def ToastProvider(
    *children,
    position: str = "bottom-right",  # top-left, top-center, top-right, bottom-left, bottom-center, bottom-right
    cls: str = "",
    **attrs
) -> HtmlString:

def Toast(
    *children,
    id: str,
    title: str = "",
    description: str = "",
    variant: str = "default",  # default, success, error, warning, info
    duration: int = 5000,      # 0 for no auto-dismiss
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
ToastProvider(
    # Your app content here
    Button("Show Toast", on_click=show_toast()),
    position="bottom-right",
)

Toast(
    id="success-toast",
    title="Success!",
    description="Your changes have been saved.",
    variant="success",
)
```

## Key Behaviors

- Auto-dismiss after duration
- Manual close button
- Stacking multiple toasts
- Entry/exit animations

## Documentation Page

**File**: `nitro/docs_app/pages/toast.py`
**Route**: `/xtras/toast`

### Required Examples
- Trigger toast button
- All variants
- Different positions
- Persistent toast (no auto-dismiss)

## Acceptance Criteria

- [x] Toast appears and auto-dismisses
- [x] Close button works
- [x] All variants styled correctly
- [x] Position options work
- [x] Toasts stack properly
- [x] Documentation has interactive trigger
- [x] Pyright passes

