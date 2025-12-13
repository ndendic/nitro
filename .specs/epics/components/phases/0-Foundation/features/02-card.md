# Feature: Card Component

**Status**: Pending  
**Phase**: 0 - Foundation  
**Priority**: High  

## Overview

Card container component with semantic HTML children. Uses Basecoat's context-based styling pattern.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/card.py`  
**CSS Reference**: `docs_app/static/css/basecoat/components/card.css`

### Basecoat Pattern

Uses semantic HTML children for styling:
- `.card` wrapper with `header`, `section`, `footer` children
- `header` contains `h2` (title) and `p` (description)
- `section` for main content
- `footer` for actions

### API

```python
def Card(*children, cls: str = "", **attrs) -> HtmlString:
def CardHeader(*children, cls: str = "", **attrs) -> HtmlString:
def CardTitle(*children, cls: str = "", **attrs) -> HtmlString:
def CardDescription(*children, cls: str = "", **attrs) -> HtmlString:
def CardContent(*children, cls: str = "", **attrs) -> HtmlString:
def CardFooter(*children, cls: str = "", **attrs) -> HtmlString:
```

### Usage Examples

```python
Card(
    CardHeader(
        CardTitle("My Card"),
        CardDescription("A description"),
    ),
    CardContent("Main content here"),
    CardFooter(Button("Action")),
)
```

## Documentation Page

**File**: `nitro/docs_app/pages/components/card.py`  
**Route**: `/components/card`

### Required Examples
- Basic card with all sections
- Card without footer
- Card with custom styling
- Multiple cards layout

## Acceptance Criteria

- [ ] Card outputs `.card` class
- [ ] Semantic children styled correctly
- [ ] CardHeader, CardContent, CardFooter work
- [ ] cls parameter allows overrides
- [ ] Documentation page renders
- [ ] Pyright passes

