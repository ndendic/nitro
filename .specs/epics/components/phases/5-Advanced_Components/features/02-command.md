# Feature: Command Palette

**Status**: Completed  
**Phase**: 5 - Advanced Components  
**Priority**: High  

## Overview

Command palette component for quick actions and search. Supports grouping and keyboard navigation.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/command.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/command.css`

### API

```python
def Command(
    *children,
    id: str = "command",
    placeholder: str = "Type a command or search...",
    cls: str = "",
    **attrs
) -> HtmlString:

def CommandGroup(
    *children,
    heading: str = "",
    cls: str = "",
    **attrs
) -> HtmlString:

def CommandItem(
    *children,
    on_select: str = "",
    shortcut: str = "",
    cls: str = "",
    **attrs
) -> HtmlString:

def CommandSeparator(cls: str = "", **attrs) -> HtmlString:
```

### Usage Examples

```python
Command(
    CommandGroup(
        CommandItem("New File", on_select="newFile()", shortcut="⌘N"),
        CommandItem("Open File", on_select="openFile()", shortcut="⌘O"),
        heading="File",
    ),
    CommandSeparator(),
    CommandGroup(
        CommandItem("Settings", on_select="openSettings()"),
        heading="Actions",
    ),
    id="cmd",
)
```

## Key Behaviors

- Type to filter commands
- Arrow keys to navigate
- Enter to select
- Groups organize commands

## Documentation Page

**File**: `nitro/docs_app/pages/components/command.py`  
**Route**: `/components/command`

### Required Examples
- Basic command palette
- With groups
- With shortcuts
- Filtering demo

## Acceptance Criteria

- [x] Typing filters commands
- [x] Arrow key navigation works
- [x] Enter selects command
- [x] Groups display correctly
- [x] Shortcuts shown
- [x] Documentation shows interaction
- [x] Visual test passes

