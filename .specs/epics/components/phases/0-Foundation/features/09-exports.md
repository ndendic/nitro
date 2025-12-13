# Feature: Update Component Exports

**Status**: Pending  
**Phase**: 0 - Foundation  
**Priority**: High  

## Overview

Update the components `__init__.py` to export all new Phase 0 components.

## Implementation Details

**File**: `nitro/nitro/infrastructure/html/components/__init__.py`

### Changes Required

Add new exports:

```python
from .button import Button
from .card import Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
from .badge import Badge
from .label import Label
from .alert import Alert, AlertTitle, AlertDescription
from .kbd import Kbd
from .spinner import Spinner
from .skeleton import Skeleton
```

## Acceptance Criteria

- [ ] All Phase 0 components importable from main package
- [ ] No import errors: `python -c "from nitro.infrastructure.html.components import Button, Card, Badge"`
- [ ] Pyright passes for __init__.py

