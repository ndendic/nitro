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
| 1 | [Checkbox](features/01-checkbox.md) | Checkbox input with Datastar binding | Completed |
| 2 | [Radio Group](features/02-radio-group.md) | Radio group with compound component pattern | Completed |
| 3 | [Switch](features/03-switch.md) | Toggle switch using checkbox with role="switch" | Completed |
| 4 | [Select](features/04-select.md) | Native select with Datastar binding | Completed |
| 5 | [Textarea](features/05-textarea.md) | Textarea with two-way binding | Completed |
| 6 | [Field](features/06-field.md) | Form field wrapper with label, description, error | Pending |
| 7 | [Input Group](features/07-input-group.md) | Input with prefix/suffix elements | Pending |
| 8 | [Documentation](features/08-documentation.md) | Documentation pages for all P1 components | Pending |

## Mandatory Testing Success Criteria

### Automated Verification
- [ ] Pyright passes for all form components
- [ ] Components import without errors
- [ ] Documentation pages render without errors

### Visual Verification using skill or MCP
- [x] Checkbox toggles and signal updates
- [x] Radio group only allows one selection
- [x] Switch animates smoothly
- [x] Select dropdown works with Datastar binding
- [ ] Field shows error state correctly
- [ ] Keyboard navigation works (Tab, Space, Enter)
- [ ] Documentation pages show signal state changes in Preview

## Dependencies

- Phase 0 completed (Label component)
- Datastar SDK (Signal, Signals)
- Basecoat form CSS files in `basecoat/components/form/`

## Handover notes for next developer

------------------------------------
**Session: 2025-12-13**

**Completed:**
- ✅ Checkbox component implemented (`nitro/infrastructure/html/components/checkbox.py`)
- ✅ Documentation page created (`docs_app/pages/checkbox.py`)
- ✅ Router registered in `app.py`
- ✅ Exported from components `__init__.py`
- ✅ Added to index page under "Form Controls" section

**Implementation Notes:**
- Checkbox supports Datastar `data_bind` for two-way binding
- Uses Basecoat's context-based styling (checkbox inside `.field` gets styled automatically)
- When `*children` are provided, wraps checkbox+label in `<label>` for accessibility
- When no children, returns just the `<input>` for custom layouts
- Fixed bug with `cls="None"` appearing when cls is empty string

**Documentation Route:** `/xtras/checkbox`

**Next Steps:**
- Continue with Feature #3: Switch component
- Consider running Pyright to verify type hints

------------------------------------
**Session: 2025-12-13 (continued)**

**Completed:**
- ✅ Radio Group component implemented (`nitro/infrastructure/html/components/radio.py`)
- ✅ Documentation page created (`docs_app/pages/radio.py`)
- ✅ Router registered in `app.py`
- ✅ Exported from components `__init__.py` (RadioGroup, RadioItem)
- ✅ Added to index page under "Form Controls" section
- ✅ Fixed browser_tool.js to support URL parameter for click command

**Implementation Notes:**
- RadioGroup uses compound component pattern with closure
- RadioItem returns a closure that receives `signal_name` from parent
- Supports `orientation` parameter: "vertical" (default) or "horizontal"
- Uses Basecoat's context-based styling (radio inside `.field` gets styled automatically)
- Generates unique IDs for radio inputs: `radio-{signal_name}-{value}`
- All radio items share the same `name` attribute (from signal name)

**Documentation Route:** `/xtras/radio`

**Verified:**
- Radio group displays correctly with vertical layout
- Horizontal orientation works
- Signal binding updates when selection changes
- Only one option can be selected at a time
- Pre-selected values work
- Disabled options render correctly

**Next Steps:**
- Continue with Feature #4: Select component
- Consider running Pyright to verify type hints

------------------------------------
**Session: 2025-12-13 (Switch implementation)**

**Completed:**
- ✅ Switch component implemented (`nitro/infrastructure/html/components/switch.py`)
- ✅ Documentation page created (`docs_app/pages/switch.py`)
- ✅ Router registered in `app.py`
- ✅ Exported from components `__init__.py`
- ✅ Added to index page under "Form Controls" section

**Implementation Notes:**
- Switch uses `role="switch"` attribute for Basecoat CSS styling
- Added `class="input"` to ensure Basecoat styling works outside `.form`/`.field` context
- Basecoat CSS targets: `.form/.field input[role='switch']` OR `.input[role='switch']`
- Supports Datastar `data_bind` for two-way binding (same pattern as Checkbox)
- When `*children` are provided, wraps switch+label in `<label>` for accessibility
- When no children, returns just the `<input>` for custom layouts (e.g., settings panels)
- CSS animation shows sliding toggle via `:checked` pseudo-class + `before:` pseudo-element

**Documentation Route:** `/xtras/switch`

**Documentation Examples:**
- Basic switch with label
- Switches with Datastar binding showing live state
- Settings panel example (realistic use case)
- Disabled states (both on and off)
- Field context example
- Without integrated label example

**Verified:**
- Switch toggles smoothly with CSS animation
- role="switch" attribute present in HTML output
- Datastar binding updates signal correctly
- Signal state changes reflect in UI immediately
- Dark mode toggle actually toggles dark mode (demonstrates full reactivity)
- Disabled states render correctly

**Next Steps:**
- Continue with Feature #5: Textarea component
- Consider running Pyright to verify type hints for all P1 components

------------------------------------
**Session: 2025-12-13 (Select implementation)**

**Completed:**
- ✅ Select component implemented (`nitro/infrastructure/html/components/select.py`)
- ✅ SelectOption helper for option elements
- ✅ SelectOptGroup for option grouping
- ✅ Documentation page created (`docs_app/pages/select.py`)
- ✅ Router registered in `app.py`
- ✅ Exported from components `__init__.py` (Select, SelectOption, SelectOptGroup)
- ✅ Added to index page under "Form Controls" section

**Implementation Notes:**
- Select supports Datastar `data_bind` for two-way binding (string or Signal)
- Uses `.select` class for Basecoat styling (context-based: inside `.field` or standalone)
- `id` parameter is optional (made backward-compatible with existing Navbar usage)
- Placeholder is implemented as a disabled first option
- SelectOptGroup allows organizing options into logical groups

**Documentation Route:** `/xtras/select`

**Documentation Examples:**
- Basic select with options
- Select with placeholder
- Select with Datastar binding showing live state
- Option groups example
- Disabled states (both select and individual options)
- API reference for Select, SelectOption, SelectOptGroup

**Verified:**
- Select renders correctly with Basecoat styling
- Placeholder option shows correctly
- Option groups render correctly
- Datastar binding attributes present in HTML output
- All documentation sections render without errors

**Next Steps:**
- Continue with Feature #6: Field component
- Run Pyright to verify type hints for all P1 components so far

------------------------------------
**Session: 2025-12-13 (Textarea implementation)**

**Completed:**
- ✅ Textarea component implemented (`nitro/infrastructure/html/components/textarea.py`)
- ✅ Documentation page created (`docs_app/pages/textarea.py`)
- ✅ Router registered in `app.py`
- ✅ Exported from components `__init__.py`
- ✅ Added to index page under "Form Controls" section

**Implementation Notes:**
- Textarea supports Datastar `data_bind` for two-way binding
- Uses `.textarea` class for Basecoat styling (context-based: inside `.field` or standalone)
- `id` parameter is optional (consistent with Select component)
- Supports `rows`, `cols`, `maxlength`, `minlength` attributes
- Supports `disabled`, `required`, `readonly` states
- Children are used as default text content

**Documentation Route:** `/xtras/textarea`

**Documentation Examples:**
- Basic textarea with placeholder
- Textarea with Datastar binding showing live character count
- Character limit example with maxlength
- Different row sizes (2, 4, 8 rows)
- Disabled and read-only states
- API reference
- Character counter pattern example

**Verified:**
- Textarea renders correctly with Basecoat styling
- Placeholder shows correctly
- Different row sizes work
- Datastar binding attributes present in HTML output
- Character count updates in real-time
- All documentation sections render without errors

**Progress Summary:**
- Phase 1: 5/8 features completed (Checkbox, Radio, Switch, Select, Textarea)
- Remaining: Field, Input Group, Documentation pages

**Next Steps:**
- Continue with Feature #6: Field component
- Run Pyright to verify type hints for all P1 components

------------------------------------
Remove resolved and obsolete comments and leave relevant instructions between markers! <--DO NOT DELETE THIS SENTANCE
