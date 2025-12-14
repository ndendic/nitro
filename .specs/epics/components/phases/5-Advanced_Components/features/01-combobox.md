# Feature: Combobox Component

**Status**: Completed  
**Phase**: 5 - Advanced Components  
**Priority**: High  

## Overview

Combobox with search filtering. Combines input with dropdown list.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/combobox.py`  
**CSS**: Custom CSS file

### API

```python
def Combobox(
    *children,
    id: str = "",
    placeholder: str = "Search...",
    signal: str = "",
    items_signal: str = "",
    cls: str = "",
    **attrs
) -> HtmlString:

def ComboboxItem(
    *children,
    value: str,
    combobox_id: str,
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
Combobox(
    ComboboxItem("Apple", value="apple", combobox_id="fruits"),
    ComboboxItem("Banana", value="banana", combobox_id="fruits"),
    ComboboxItem("Orange", value="orange", combobox_id="fruits"),
    id="fruits",
    placeholder="Select a fruit...",
)
```

## Key Behaviors

- Type to filter options
- Click or keyboard to select
- Selected item shows in input
- Click outside closes

## Documentation Page

**File**: `nitro/docs_app/pages/components/combobox.py`  
**Route**: `/components/combobox`

### Required Examples
- Basic combobox
- With filtering demo
- Pre-selected value
- Disabled options

## Acceptance Criteria

- [x] Typing filters options
- [x] Selection updates signal
- [x] Input shows selected value
- [x] Click outside closes
- [x] Keyboard navigation works
- [x] Documentation shows filtering
- [x] Visual test passes

