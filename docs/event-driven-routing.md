# Event-Driven Action System

> Replaces the old REST-style route-per-method system with a unified event-driven architecture.
> Built on branch `feat/event-driven-routing` — 11 commits, 66 tests.

## Architecture Overview

**Before:** Each entity method got its own HTTP route via `NitroDispatcher` discovery. Routes like `POST /counter/{id}/increment`.

**After:** Decorators register Blinker event handlers. Framework adapters register 5 catch-all endpoints (`/get/<action>`, `/post/<action>`, etc.) that parse action strings and dispatch to the event system.

```
@post() decorator
       │
       ├── Standalone function → registers Blinker handler immediately
       └── Entity method → stamps metadata only (deferred)
                │
                └── Entity.__init_subclass__ → scans methods, registers Blinker handlers
                        │
                        └── action() helper → generates Datastar action strings
                                │
                                └── Sanic catch-all → parses URL, dispatches to Blinker
```

## Action String Format

```
Entity:id.method    → instance method  (Counter:abc123.increment)
Entity.method       → class method     (Counter.list_all)
prefix.function     → prefixed standalone (auth.register_user)
function            → bare standalone  (health_check)
```

## Usage

### Define Entity with Decorated Methods

```python
from nitro import Entity, get, post, delete, action
from sqlmodel import Field

class Todo(Entity, table=True):
    __tablename__ = "todo"
    id: str = Field(primary_key=True)
    title: str = ""
    done: bool = False

    @post()
    async def toggle(self):
        self.done = not self.done
        self.save()

    @delete()
    async def remove(self):
        self.delete()

    @get()
    @classmethod
    def list_all(cls):
        return [t.model_dump() for t in cls.all()]
```

Events are auto-registered via `__init_subclass__`: `Todo.toggle`, `Todo.remove`, `Todo.list_all`.

### Standalone Functions

```python
@post(prefix="auth")
def login(username: str = "", password: str = ""): ...

@get()
def health_check(): ...
```

Events registered immediately at decoration time: `auth.login`, `health_check`.

### Generate Datastar Action Strings

```python
# Instance method — pass id explicitly or use bound method
action(Todo.toggle, id="abc123")        # @post('/post/Todo:abc123.toggle')
action(Todo.toggle, id="$selected_id")  # @post('/post/Todo:$selected_id.toggle')

# Bound method — id auto-injected
todo = Todo.get("abc123")
action(todo.toggle)                     # @post('/post/Todo:abc123.toggle')

# Class method
action(Todo.list_all)                   # @get('/get/Todo.list_all')

# Standalone
action(login, username="$user")         # @post('/post/auth.login')

# GET with query params
action(health_check)                    # @get('/get/health_check')

# POST with literal values (signal assignments)
action(todo.toggle)                     # @post('/post/Todo:abc123.toggle')
action(login, username="admin")         # $username = 'admin'; @post('/post/auth.login')
```

### In HTML (RustyTags + Datastar)

```python
Button("Toggle", on_click=action(todo.toggle))
# <button data-on:click="@post('/post/Todo:abc123.toggle')">Toggle</button>

Button("Add", on_click=action(Todo.toggle, id="$new_id"))
# <button data-on:click="@post('/post/Todo:$new_id.toggle')">Add</button>
```

### Sanic Setup

```python
from sanic import Sanic
from nitro.adapters.sanic_adapter import configure_nitro

app = Sanic("MyApp")
configure_nitro(app)  # Registers 5 catch-all routes
```

That's it. No discovery step, no dispatcher configuration. Entity actions register themselves.

### Sender Identification

Client identity is extracted from the request (not the URL):
1. `user_id` cookie
2. `x-client-id` header
3. Falls back to `"anonymous"`

## New Files

| File | Purpose |
|------|---------|
| `nitro/routing/actions.py` | `ActionRef` dataclass + `parse_action()` |
| `nitro/routing/action_helper.py` | `action()` helper — generates Datastar strings |
| `nitro/routing/registration.py` | `register_entity_actions()` called by `__init_subclass__` |
| `nitro/adapters/catch_all.py` | `dispatch_action()` — framework-agnostic dispatch |

## Modified Files

| File | Changes |
|------|---------|
| `nitro/routing/metadata.py` | Added `event_name`, `prefix` fields; removed `generate_url_path()` |
| `nitro/routing/decorator.py` | Full rewrite — event registration for standalone, classmethod support |
| `nitro/routing/__init__.py` | Updated exports |
| `nitro/__init__.py` | Exports `action` helper + `NotFoundError` |
| `nitro/domain/entities/base_entity.py` | Added `__init_subclass__` for auto-registration |
| `nitro/adapters/sanic_adapter.py` | Full rewrite — 5 catch-all endpoints |

## Removed

| File | Replaced By |
|------|-------------|
| `nitro/routing/discovery.py` | `Entity.__init_subclass__` |
| `nitro/routing/dispatcher.py` | `nitro/adapters/catch_all.py` |
| FastAPI/Flask/FastHTML adapters | Stubbed with deprecation warnings |

## Tests

66 tests across 7 test files:

| Test File | Count | Covers |
|-----------|-------|--------|
| `test_actions.py` | 13 | ActionRef, parse_action |
| `test_metadata.py` | 12 | ActionMetadata fields, helpers |
| `test_decorator_events.py` | 14 | Decorator metadata, event registration, deferral |
| `test_entity_registration.py` | 5 | __init_subclass__, route name override |
| `test_action_helper.py` | 12 | action() for standalone, entity, bound methods |
| `test_catch_all.py` | 4 | dispatch_action with various action types |
| `test_integration_events.py` | 6 | Full end-to-end flow |

## Design Doc

Full design rationale: `docs/plans/2026-03-09-smart-routing-design.md`
Implementation plan: `docs/plans/2026-03-09-smart-routing-implementation.md`
