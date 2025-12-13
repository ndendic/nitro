# Feature: Phase 0 Documentation Pages

**Status**: Pending  
**Phase**: 0 - Foundation  
**Priority**: High  

## Overview

Create documentation pages for all Phase 0 components. Each page serves as both documentation and testing ground.

## Files to Create

- `nitro/docs_app/pages/components/button.py`
- `nitro/docs_app/pages/components/card.py`
- `nitro/docs_app/pages/components/badge.py`
- `nitro/docs_app/pages/components/label.py`
- `nitro/docs_app/pages/components/alert.py`
- `nitro/docs_app/pages/components/kbd.py`
- `nitro/docs_app/pages/components/spinner.py`
- `nitro/docs_app/pages/components/skeleton.py`

## Documentation Page Structure

Each page follows this pattern:

```python
"""Component documentation page"""

from ..templates.base import *  # noqa: F403
from fastapi import APIRouter
from nitro.infrastructure.html.components import ComponentName

router: APIRouter = APIRouter()

def example_basic():
    """Basic usage example."""
    return ComponentName(...)

def example_variants():
    """Show variant options."""
    return Div(...)

@router.get("/components/{name}")
@template(title="ComponentName Documentation")
def component_docs():
    return Div(
        H1("ComponentName"),
        P("Description"),
        Section("Basic Usage", ComponentShowcase(example_basic)),
        Section("Variants", ComponentShowcase(example_variants)),
        Section("API Reference", CodeBlock(...)),
        Section("Accessibility", Ul(...)),
        BackLink(),
    )
```

## Requirements

1. **Route**: `/components/{component-name}` (kebab-case)
2. **Minimum 2 examples** showing different use cases
3. **ComponentShowcase** wrapper for Preview/Code tabs
4. **API Reference** section with full function signature
5. **Accessibility** section documenting ARIA and keyboard support
6. **Register router** in `docs_app/main.py`

## Acceptance Criteria

- [ ] All 8 documentation pages created
- [ ] Each page has minimum 2 examples
- [ ] ComponentShowcase shows Preview/Code tabs
- [ ] API Reference section present
- [ ] Routers registered in main.py
- [ ] Pages render without errors

