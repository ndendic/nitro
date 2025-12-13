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
| 1 | [Dropdown Menu](features/01-dropdown-menu.md) | Dropdown menu with compound component pattern | Completed |
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
- [x] Dropdown opens/closes on trigger click
- [x] Click outside closes dropdown/popover
- [x] Escape key closes overlays
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
**Session completed: 2024-12-13**

### Completed this session:
- ✅ Implemented DropdownMenu component with compound component pattern (closure-based)
- ✅ Created documentation page at `/xtras/dropdown` with 6 examples
- ✅ Added Dropdown Menu link to index page Interactive Components section
- ✅ Verified dropdown opens/closes on trigger click
- ✅ Verified click outside closes dropdown
- ✅ Escape key closes overlays
- ✅ ARIA attributes present and working with Datastar dynamic updates

### Implementation notes:
- Component file: `nitro/infrastructure/html/components/dropdown.py`
- Documentation: `docs_app/pages/dropdown.py`
- Uses Basecoat CSS classes: `.dropdown-menu`, `[data-popover]`, `[role="menuitem"]`
- Uses Datastar signals for open/close state with `data-on-click--outside` and `data-on-keydown--escape`
- Fixed issue with `aria-hidden` needing both initial static value AND `data-attr-aria-hidden` for dynamic updates

### Next feature to implement:
- Feature 2: Popover component (similar pattern to dropdown but more general purpose)

### What to work on next:
1. Read `features/02-popover.md` for Popover requirements
2. Implement Popover component following same compound component pattern
3. Popover is more general purpose than dropdown (no menu semantics)
------------------------------------
Remove resolved and obsolete comments and leave relevant instructions between markers! <--DO NOT DELETE THIS SENTANCE