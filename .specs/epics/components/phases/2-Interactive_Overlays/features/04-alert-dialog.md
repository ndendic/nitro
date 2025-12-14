# Feature: Alert Dialog Component

**Status**: Completed
**Phase**: 2 - Interactive Overlays
**Priority**: Medium  

## Overview

Alert dialog for confirmations using native HTML dialog element. Blocks background interaction.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/alert_dialog.py`  
**CSS**: Custom CSS file (no Basecoat equivalent)

### API

```python
def AlertDialog(*children, id: str, cls: str = "", **attrs) -> HtmlString:
def AlertDialogTrigger(*children, dialog_id: str, cls: str = "", **attrs) -> HtmlString:
def AlertDialogHeader(*children, cls: str = "", **attrs) -> HtmlString:
def AlertDialogTitle(*children, cls: str = "", **attrs) -> HtmlString:
def AlertDialogDescription(*children, cls: str = "", **attrs) -> HtmlString:
def AlertDialogFooter(*children, cls: str = "", **attrs) -> HtmlString:
def AlertDialogAction(*children, dialog_id: str, on_click: str = "", cls: str = "", **attrs) -> HtmlString:
def AlertDialogCancel(*children, dialog_id: str, cls: str = "", **attrs) -> HtmlString:
```

### Usage Examples

```python
AlertDialogTrigger("Delete Account", dialog_id="confirm-delete"),
AlertDialog(
    AlertDialogHeader(
        AlertDialogTitle("Are you sure?"),
        AlertDialogDescription("This action cannot be undone."),
    ),
    AlertDialogFooter(
        AlertDialogCancel("Cancel", dialog_id="confirm-delete"),
        AlertDialogAction("Delete", dialog_id="confirm-delete", on_click="deleteAccount()"),
    ),
    id="confirm-delete",
)
```

## Key Behaviors

- Uses native dialog.showModal()
- Background is blocked (modal)
- Focus trapped inside dialog
- Escape closes dialog

## Documentation Page

**File**: `nitro/docs_app/pages/components/alert-dialog.py`  
**Route**: `/components/alert-dialog`

### Required Examples
- Basic confirmation
- Destructive action
- With form submission

## Acceptance Criteria

- [x] Dialog opens/closes correctly
- [x] Background is blocked
- [x] Focus trapped inside
- [x] Action and Cancel buttons work
- [x] Escape key closes
- [x] Documentation shows usage
- [ ] Pyright passes

