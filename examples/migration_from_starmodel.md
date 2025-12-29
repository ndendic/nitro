# Migration Guide: From StarModel to Nitro

This guide demonstrates how to migrate code from StarModel to Nitro Framework.

## Overview

Nitro Framework evolved from StarModel's proven patterns. The migration is straightforward:
- **Import changes**: `from starmodel import *` → `from nitro.domain.entities.base_entity import Entity`
- **Class rename**: `State` → `Entity`
- **Minimal code changes**: Most business logic stays identical

## Example: Counter App Migration

### Before: StarModel Code

```python
# StarModel version
from starmodel import *
from fasthtml.common import *

class Counter(State):
    count: int = 0
    update_count: int = 0

    @event
    def increment(self, amount: int = 1):
        self.count += amount
        self.update_count += 1

    @event
    def decrement(self, amount: int = 1):
        self.count -= amount
        self.update_count += 1

@rt
def index(req: Request):
    counter = Counter.get(req)
    return Main(
        counter,
        H1("Counter Demo"),
        Button("+", data_on_click=Counter.increment(1)),
        Span(data_text=Counter.Scount),
        Button("-", data_on_click=Counter.decrement(1)),
    )

states_rt.to_app(app)
```

### After: Nitro Code

```python
# Nitro version
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository
from fasthtml.common import *

class Counter(Entity, table=True):
    count: int = 0
    update_count: int = 0

    model_config = {"repository_class": MemoryRepository}

    def increment(self, amount: int = 1):
        self.count += amount
        self.update_count += 1
        self.save()

    def decrement(self, amount: int = 1):
        self.count -= amount
        self.update_count += 1
        self.save()

@rt
def index(session_id: str):
    counter = Counter.get(session_id) or Counter(id=session_id)
    return Main(
        H1("Counter Demo"),
        Button("+", hx_post=f"/counter/{session_id}/increment"),
        Span(str(counter.count)),
        Button("-", hx_post=f"/counter/{session_id}/decrement"),
    )

@rt("/counter/{session_id}/increment")
def increment_counter(session_id: str):
    counter = Counter.get(session_id)
    counter.increment(1)
    return str(counter.count)
```

## Key Changes

### 1. Import Statements

```python
# StarModel
from starmodel import *

# Nitro
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository
from nitro.infrastructure.repository.sql import SQLModelRepository
```

### 2. Class Definition

```python
# StarModel
class Counter(State):
    count: int = 0

# Nitro
class Counter(Entity, table=True):
    count: int = 0
    model_config = {"repository_class": MemoryRepository}
```

### 3. Persistence

```python
# StarModel - automatic persistence
@event
def increment(self):
    self.count += 1  # Automatically saved

# Nitro - explicit save (clearer intent)
def increment(self):
    self.count += 1
    self.save()  # Explicit save
```

### 4. Repository Selection

```python
# Nitro - Choose your backend
class Counter(Entity, table=True):
    # Option 1: In-memory (like StarModel sessions)
    model_config = {"repository_class": MemoryRepository}

    # Option 2: SQL database (persistent)
    model_config = {"repository_class": SQLModelRepository}
```

## Migration Checklist

- [ ] Replace `from starmodel import *` with Nitro imports
- [ ] Change `State` to `Entity`
- [ ] Add `table=True` to class definition
- [ ] Add `model_config` with repository selection
- [ ] Add explicit `.save()` calls after mutations
- [ ] Update routing if using `@event` decorator patterns
- [ ] Test all CRUD operations

## Benefits of Migration

1. **Framework Agnostic**: Works with FastAPI, Flask, Django, FastHTML
2. **Hybrid Persistence**: Mix Memory, SQL, Redis backends per entity
3. **Explicit Save**: Clearer intent with `.save()` vs automatic
4. **Production Ready**: Battle-tested patterns with comprehensive tests
5. **Type Safety**: Full Pydantic validation and IDE support

## Real-World Migration Example

See `examples/fastapi_todo_app.py` for a complete working application:
- 48 lines of code
- Full CRUD operations
- Works with both Memory and SQL backends
- FastAPI integration with type-safe endpoints

## Need Help?

Check the Nitro documentation:
- Entity API: `nitro/domain/entities/base_entity.py`
- Persistence: `nitro/infrastructure/repository/`
- Examples: `examples/`
