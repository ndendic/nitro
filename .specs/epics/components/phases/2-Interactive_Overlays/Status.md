# Phase 2: Interactive Overlays

## HOW TO USE THIS DOCUMENT - IMPORTANT!
This document should give you the overview of Phase implementation progress.
Select first Feature in status 'Active' or 'Pending' if there is not 'Active' Feature.
If you select 'Pending' Feature update it's status to 'Active'
You are only allowed to : 
 - Update Status attributes of Features in the table below
 - Mark passed tests in 'Mandatory Testing Success Criteria' section
 - Leave handover notes for the next developer in marked area when you're done - MANDATORY STEP

---
### Status Legend

- **Pending**: Not started
- **Active**: Currently in progress  
- **Completed**: Done and verified
- **On-Hold**: Blocked or deferred
---

## Overview

Dropdown, Popover, and Tooltip using Datastar signals for visibility and positioning. Uses compound component pattern with closure for signal passing.

## Features

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | [Dropdown Menu](features/01-dropdown-menu.md) | Dropdown menu with compound component pattern | Pending |
| 2 | [Popover](features/02-popover.md) | Positioned overlay container | Pending |
| 3 | [Tooltip](features/03-tooltip.md) | Pure CSS tooltip (no JavaScript) | Pending |
| 4 | [Alert Dialog](features/04-alert-dialog.md) | Confirmation dialog with native HTML dialog | Pending |
| 5 | [Documentation](features/05-documentation.md) | Documentation pages for all P2 components | Pending |

## Mandatory Testing Success Criteria

### Automated Verification
- [ ] Pyright passes for all interactive components
- [ ] No import errors
- [ ] Documentation pages render without errors

### Visual Verification using skill or MCP
- [ ] Dropdown opens/closes on trigger click
- [ ] Click outside closes dropdown/popover
- [ ] Escape key closes overlays
- [ ] Tooltip appears on hover with delay
- [ ] Alert dialog blocks background interaction
- [ ] Focus is trapped in alert dialog
- [ ] Documentation pages demonstrate all interaction patterns

## Dependencies

- Phase 1 completed (Button component for triggers)
- Datastar SDK (Signal for open/close state)
- Basecoat CSS for dropdown-menu, popover, tooltip

## Handover notes for next developer

------------------------------------
HANDOVER NOTES GO HERE! Summarize your handover notes and leave them!
------------------------------------
Remove resolved and obsolete comments and leave relevant instructions between markers! <--DO NOT DELETE THIS SENTANCE