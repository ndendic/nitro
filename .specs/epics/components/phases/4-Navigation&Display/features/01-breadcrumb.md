# Feature: Breadcrumb Component

**Status**: Completed  
**Phase**: 4 - Navigation & Display  
**Priority**: Medium  

## Overview

Breadcrumb navigation component with separator and current page indication.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/breadcrumb.py`  
**CSS**: Custom CSS file (Tailwind utilities)

### API

```python
def Breadcrumb(*children, cls: str = "", **attrs) -> HtmlString:
def BreadcrumbItem(*children, href: str = "", current: bool = False, cls: str = "", **attrs) -> HtmlString:
def BreadcrumbSeparator(cls: str = "", **attrs) -> HtmlString:
```

### Usage Examples

```python
Breadcrumb(
    BreadcrumbItem("Home", href="/"),
    BreadcrumbSeparator(),
    BreadcrumbItem("Products", href="/products"),
    BreadcrumbSeparator(),
    BreadcrumbItem("Shoes", current=True),
)
```

## Key Behaviors

- Links for navigation (except current)
- aria-current="page" on current item
- aria-label="Breadcrumb" on nav

## Documentation Page

**File**: `nitro/docs_app/pages/components/breadcrumb.py`  
**Route**: `/components/breadcrumb`

### Required Examples
- Basic breadcrumb
- Custom separators
- With icons

## Acceptance Criteria

- [x] Navigation links work
- [x] Current page styled differently
- [x] ARIA attributes present
- [x] Separators render correctly
- [x] Documentation shows examples
- [x] Visual test passes

