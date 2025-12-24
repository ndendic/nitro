---
title: Framework Overview
category: Frameworks
order: 1
---

# Framework Integration Overview

Nitro is **framework-agnostic by design**. Your entity logic, business rules, and domain models are completely independent of the web framework you choose. This means you can:

- Start with one framework and switch to another without rewriting your entities
- Use the same entities across multiple applications built with different frameworks
- Focus on business logic first, choose your delivery mechanism later

## The @action Decorator

The `@action` decorator marks entity methods as HTTP endpoints that should be automatically routed. This is the bridge between your framework-independent business logic and your web framework's routing system.

```python
from nitro.infrastructure.routing import action
from nitro.domain.entities.base_entity import Entity

class Counter(Entity, table=True):
    count: int = 0

    @action(method="POST", summary="Increment counter")
    async def increment(self, amount: int = 1):
        """Increment counter by specified amount."""
        self.count += amount
        self.save()
        return {"count": self.count}

    @action(method="GET")
    def status(self):
        """Get current counter value."""
        return {"count": self.count, "id": self.id}
```

**Source:** `nitro/infrastructure/routing/decorator.py:19-132`

### @action Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `method` | str | "POST" | HTTP method (GET, POST, PUT, DELETE, PATCH) |
| `path` | str \| None | None | Custom URL path (auto-generated if None) |
| `response_model` | Type \| None | None | Pydantic model for response validation |
| `status_code` | int | 200 | HTTP status code for successful responses |
| `tags` | List[str] \| None | None | Tags for OpenAPI documentation |
| `summary` | str \| None | None | Short description for API docs |
| `description` | str \| None | None | Long description (uses docstring if None) |

### Auto-Generated Routes

Routes are automatically generated based on your entity class name and method name:

```python
# Instance methods (require entity ID)
Counter.increment() → POST /counter/{id}/increment
Counter.status() → GET /counter/{id}/status

# Class methods (no entity ID required)
@classmethod
@action(method="GET")
def list_all(cls):
    return [c.model_dump() for c in cls.all()]

Counter.list_all() → GET /counter/list_all
```

## The NitroDispatcher Pattern

Each framework adapter extends the `NitroDispatcher` base class, which handles:

1. **Discovery** - Finding all entities and their @action methods
2. **Routing** - Generating URL patterns and registering routes
3. **Dispatching** - Extracting parameters and calling entity methods
4. **Error handling** - Consistent 404, 422, and 500 responses

**Source:** `nitro/infrastructure/routing/dispatcher.py:22-260`

The framework adapter only needs to implement framework-specific route registration.

## Same Entity, Different Frameworks

Here's the same `Counter` entity integrated with three different frameworks:

### FastAPI
```python
from fastapi import FastAPI
from nitro.adapters.fastapi import configure_nitro

app = FastAPI()
configure_nitro(app)  # Auto-registers all routes
```

### Flask
```python
from flask import Flask
from nitro.adapters.flask import configure_nitro

app = Flask(__name__)
configure_nitro(app)  # Auto-registers all routes
```

### FastHTML
```python
from fasthtml.common import *
from nitro.adapters.fasthtml import configure_nitro

app, rt = fast_app()
configure_nitro(rt)  # Auto-registers all routes
```

The entity code remains **identical** across all three frameworks.

## configure_nitro() Function

Every framework adapter provides a `configure_nitro()` function as the main entry point:

```python
def configure_nitro(
    app,                                    # Framework application instance
    entities: Optional[List[Type]] = None,  # Specific entities to register
    prefix: str = "",                       # URL prefix (e.g., "/api/v1")
    auto_discover: bool = True              # Auto-discover all entities
):
    """Configure Nitro auto-routing for the framework."""
```

### Auto-Discovery

By default, `configure_nitro()` automatically discovers all `Entity` subclasses in your application:

```python
# Automatically finds and registers all entities
configure_nitro(app)
```

### Manual Registration

You can explicitly specify which entities to register:

```python
from myapp.models import Counter, Todo, User

configure_nitro(
    app,
    entities=[Counter, Todo],  # Only register these
    auto_discover=False
)
```

### URL Prefixes

Add a prefix to all generated routes:

```python
# All routes will start with /api/v1
configure_nitro(app, prefix="/api/v1")

# Counter.increment() → POST /api/v1/counter/{id}/increment
```

## Supported Frameworks

| Framework | Status | Adapter | Notes |
|-----------|--------|---------|-------|
| **FastAPI** | ✅ Full support | `nitro.adapters.fastapi` | OpenAPI docs, dependency injection |
| **FastHTML** | ✅ Full support | `nitro.adapters.fasthtml` | Native RustyTags integration |
| **Flask** | ✅ Full support | `nitro.adapters.flask` | Sync/async support |
| **Starlette** | ⚠️ Event system only | `nitro.infrastructure.events.starlette` | SSE helpers, no auto-routing |
| **Django** | 📋 Planned | - | Coming in future release |
| **Sanic** | 🧪 Experimental | - | Code in `xPlay/` directory |

## Parameter Extraction

The dispatcher automatically extracts parameters from different sources based on the HTTP method:

### POST/PUT/PATCH Requests
```python
@action(method="POST")
def update(self, name: str, price: float):
    # Parameters from request body (JSON)
    self.name = name
    self.price = price
    self.save()
```

Request:
```bash
POST /product/{id}/update
Content-Type: application/json

{"name": "Widget", "price": 9.99}
```

### GET Requests
```python
@action(method="GET")
def search(self, query: str, limit: int = 10):
    # Parameters from query string
    return self.filter(name__contains=query)[:limit]
```

Request:
```bash
GET /product/{id}/search?query=widget&limit=5
```

### Type Validation

Parameter types are automatically validated based on type hints:

```python
@action(method="POST")
def adjust(self, amount: int, reason: str):
    # 'amount' must be an integer
    # 'reason' must be a string
    # Framework returns 422 if validation fails
```

## Error Handling

All framework adapters provide consistent error handling:

### 404 Not Found
Entity doesn't exist:
```python
GET /counter/nonexistent/status
→ 404 {"detail": "Counter with id 'nonexistent' not found"}
```

### 422 Validation Error
Invalid parameter types or missing required parameters:
```python
POST /counter/c1/increment
{"amount": "not_a_number"}
→ 422 {"detail": "Validation error..."}
```

### 500 Internal Server Error
Exceptions in entity methods:
```python
@action()
def risky_operation(self):
    raise ValueError("Something went wrong")

→ 500 {"detail": "Something went wrong"}
```

## Next Steps

Choose your framework and see the detailed integration guide:

- **[FastAPI Integration](./fastapi.md)** - Full guide with OpenAPI documentation
- **[FastHTML Integration](./fasthtml.md)** - RustyTags and reactive components
- **[Flask Integration](./flask.md)** - Traditional Flask applications
- **[Starlette Integration](./starlette.md)** - SSE event helpers

## Related Documentation

- [Entity Overview](../entity/overview.md) - Understanding Nitro entities
- [Active Record Patterns](../entity/active-record.md) - Entity methods
- [Backend Events](../events/backend-events.md) - Event-driven architecture
