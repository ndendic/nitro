# Feature: Theme Switcher

**Status**: Completed  
**Phase**: 5 - Advanced Components  
**Priority**: Medium  

## Overview

Theme toggle component cycling through light, dark, and system themes.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/theme_switcher.py`  
**CSS**: Custom CSS file

### API

```python
def ThemeSwitcher(
    signal: str = "theme",
    default_theme: str = "system",  # light, dark, system
    cls: str = "",
    **attrs
) -> HtmlString:
```

### Usage Examples

```python
# Basic usage
ThemeSwitcher()

# Custom signal and default
ThemeSwitcher(signal="app_theme", default_theme="dark")
```

## Key Behaviors

- Cycles: light → dark → system → light
- Updates document.documentElement.dataset.theme
- Shows appropriate icon for current theme
- Optionally persists with data-persist

## Documentation Page

**File**: `nitro/docs_app/pages/components/theme-switcher.py`  
**Route**: `/components/theme-switcher`

### Required Examples
- Basic theme switcher
- Current theme indicator
- Persistence demo

## Acceptance Criteria

- [x] Cycles through themes
- [x] Icons change correctly
- [x] Theme applies to page
- [x] System theme detected
- [x] Documentation shows theme changes
- [x] Visual test passes

