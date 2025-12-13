# Phase 1: Form Controls (Two-way Binding)

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

Form input components using Datastar's `data_bind` for two-way binding. All form components use Basecoat's context-based styling (inputs inside `.field` are auto-styled).

## Features

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | [Checkbox](features/01-checkbox.md) | Checkbox input with Datastar binding | Pending |
| 2 | [Radio Group](features/02-radio-group.md) | Radio group with compound component pattern | Pending |
| 3 | [Switch](features/03-switch.md) | Toggle switch using checkbox with role="switch" | Pending |
| 4 | [Select](features/04-select.md) | Native select with Datastar binding | Pending |
| 5 | [Textarea](features/05-textarea.md) | Textarea with two-way binding | Pending |
| 6 | [Field](features/06-field.md) | Form field wrapper with label, description, error | Pending |
| 7 | [Input Group](features/07-input-group.md) | Input with prefix/suffix elements | Pending |
| 8 | [Documentation](features/08-documentation.md) | Documentation pages for all P1 components | Pending |

## Mandatory Testing Success Criteria

### Automated Verification
- [ ] Pyright passes for all form components
- [ ] Components import without errors
- [ ] Documentation pages render without errors

### Visual Verification using skill or MCP
- [ ] Checkbox toggles and signal updates
- [ ] Radio group only allows one selection
- [ ] Switch animates smoothly
- [ ] Select dropdown works with Datastar binding
- [ ] Field shows error state correctly
- [ ] Keyboard navigation works (Tab, Space, Enter)
- [ ] Documentation pages show signal state changes in Preview

## Dependencies

- Phase 0 completed (Label component)
- Datastar SDK (Signal, Signals)
- Basecoat form CSS files in `basecoat/components/form/`

## Handover notes for next developer

------------------------------------
HANDOVER NOTES GO HERE! Summarize your handover notes and leave them!
------------------------------------
Remove resolved and obsolete comments and leave relevant instructions between markers! <--DO NOT DELETE THIS SENTANCE
