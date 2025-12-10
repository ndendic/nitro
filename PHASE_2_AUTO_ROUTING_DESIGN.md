# Phase 2.1: Auto-Routing System - Design Document

**Date**: 2025-12-10
**Version**: 1.0
**Status**: DRAFT
**Author**: Session 26

---

## Executive Summary

This document specifies the design for Nitro's auto-routing system, which will eliminate the boilerplate of manually creating route handlers for entity methods. The goal is to reduce a typical Counter app from ~190 lines to < 50 lines while maintaining full framework compatibility.

**Key Innovation**: Entity methods decorated with `@action` automatically become HTTP endpoints, with routing, parameter extraction, and response handling managed by the framework.

---

## Current State Analysis

### Existing Counter App Pattern (190 lines)

```python
class Counter(Entity):
    count: int = 0

    async def increment(self):
        self.count += 1
        self.save()
        await emit_async("counter.incremented", sender=self)

# Manual route handlers (BOILERPLATE)
@app.post("/api/increment")
async def increment_counter():
    counter = Counter.get("demo")
    if not counter:
        return JSONResponse({"error": "Counter not found"}, status_code=404)
    await counter.increment()
    return JSONResponse({"count": counter.count, "status": "incremented"})

# Repeated for each method: decrement, reset, etc.
```

**Problems**:
1. **90+ lines of boilerplate** for route handlers
2. **Manual error handling** repeated in each endpoint
3. **No parameter extraction** - must parse request manually
4. **Framework-specific** code scattered everywhere
5. **Manual URL management** in frontend

---

## Target State: Auto-Routing

### Vision: Declarative Entity Methods (< 50 lines total)

```python
from nitro import Entity, action
from nitro.adapters.fastapi import configure_nitro

class Counter(Entity, table=True):
    count: int = 0

    @action(method="POST")
    async def increment(self, amount: int = 1):
        """Increment counter by amount."""
        self.count += amount
        self.save()
        return {"count": self.count}  # Auto-serialized

    @action(method="POST")
    async def reset(self):
        """Reset counter to zero."""
        self.count = 0
        self.save()

# In your FastAPI app:
app = FastAPI()
configure_nitro(app)  # Auto-registers all @action methods

# URLs auto-generated:
# POST /counter/{id}/increment?amount=5
# POST /counter/{id}/reset
```

**Benefits**:
- ✅ **50-60% code reduction** - No manual route handlers
- ✅ **Type-safe parameters** - Automatic validation from type hints
- ✅ **Framework-agnostic** - Same entity works with FastAPI, Flask, FastHTML
- ✅ **Automatic error handling** - 404 for missing entities, validation errors
- ✅ **URL generation** - `Counter.increment_url(id="demo", amount=5)`

---

## Design Decisions

### 1. Decorator Naming: `@action`

**Decision**: Use `@action` decorator
**Rationale**:
- `@event` - Conflicts with Blinker event system
- `@route` - Too generic, implies URL-centric thinking
- `@action` - Clear domain action, no conflicts

**Alternatives Considered**:
- `@endpoint` - Too HTTP-focused
- `@method` - Too generic
- `@command` - Implies CQRS pattern (Phase 3)

### 2. URL Generation Strategy

**Pattern**: `/{entity_name}/{id}/{method_name}`

**Examples**:
```python
Counter.increment() → POST /counter/{id}/increment
Product.restock()   → POST /product/{id}/restock
Order.place()       → POST /order/{id}/place
```

**Rationale**:
- RESTful resource-oriented
- Predictable and discoverable
- Supports both class-level and instance-level actions
- Compatible with OpenAPI/Swagger

**Special Cases**:
- `{id}` can be omitted for class methods: `Counter.create()` → `POST /counter/create`
- Custom URLs supported: `@action(path="/custom/path")`

### 3. HTTP Method Mapping

**Default Behavior**:
- `@action()` → POST (safe default for state-changing operations)
- `@action(method="GET")` → GET (for read-only queries)
- `@action(method="PUT")` → PUT (for updates)
- `@action(method="DELETE")` → DELETE (for deletions)

**Rationale**:
- POST as default prevents accidental GET caching
- Explicit method declaration for semantic clarity
- Follows HTTP semantics (POST = action, GET = query)

### 4. Parameter Extraction

**Automatic Extraction Order**:
1. **Path parameters**: `{id}` from URL
2. **Query parameters**: `?amount=5` from query string
3. **Request body**: JSON payload for complex parameters
4. **Datastar signals**: Automatically extracted from SSE context

**Example**:
```python
@action(method="POST")
async def increment(self, amount: int = 1, notify: bool = False):
    # amount from: ?amount=5 OR {"amount": 5} in body
    # notify from: ?notify=true OR {"notify": true} in body
    ...

# Works with:
# POST /counter/demo/increment?amount=5&notify=true
# POST /counter/demo/increment with body: {"amount": 5, "notify": true}
```

**Type Validation**:
- Uses Pydantic validation from type hints
- Automatic 422 Unprocessable Entity for validation errors
- Descriptive error messages

### 5. Framework Adapter Interface

**Base Dispatcher** (framework-agnostic):
```python
class NitroDispatcher:
    """Base class for framework adapters."""

    def register_entity(self, entity_class: Type[Entity]):
        """Discover and register all @action methods."""
        ...

    def create_route_handler(self, entity_class, method_info):
        """Create framework-specific route handler."""
        ...

    def extract_parameters(self, request, method_signature):
        """Extract and validate parameters from request."""
        ...

    def format_response(self, result, method_info):
        """Format return value as HTTP response."""
        ...
```

**Framework-Specific Adapters**:
- `FastAPIDispatcher` - Uses FastAPI dependency injection
- `FlaskDispatcher` - Uses Flask request context
- `FastHTMLDispatcher` - Returns RustyTags components
- `StarletteDispatcher` - Uses Starlette routing

---

## API Specification

### 1. `@action` Decorator

```python
def action(
    method: str = "POST",
    path: Optional[str] = None,
    response_model: Optional[Type] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
):
    """
    Decorator to mark entity methods for auto-routing.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        path: Custom URL path (default: auto-generated)
        response_model: Pydantic model for response validation
        status_code: HTTP status code for successful response
        tags: OpenAPI tags for documentation
        summary: Short description for OpenAPI
        description: Long description for OpenAPI

    Returns:
        Decorated method with routing metadata
    """
```

**Usage Examples**:
```python
# Basic usage
@action()
async def increment(self):
    ...

# With HTTP method
@action(method="GET")
async def status(self):
    ...

# With custom path
@action(path="/api/v2/increment")
async def increment(self):
    ...

# With OpenAPI metadata
@action(
    method="POST",
    summary="Increment counter",
    description="Increments the counter by a specified amount",
    tags=["counters"],
    response_model=CounterResponse
)
async def increment(self, amount: int = 1):
    ...
```

### 2. `configure_nitro()` Function

```python
def configure_nitro(
    app,
    entities: Optional[List[Type[Entity]]] = None,
    prefix: str = "",
    include_schemas: bool = True,
    auto_discover: bool = True,
):
    """
    Configure Nitro auto-routing for a web application.

    Args:
        app: Web framework application instance (FastAPI, Flask, etc.)
        entities: List of entity classes to register (None = auto-discover)
        prefix: URL prefix for all routes (e.g., "/api/v1")
        include_schemas: Include OpenAPI schemas (FastAPI only)
        auto_discover: Automatically discover all Entity subclasses

    Returns:
        Configured application with auto-generated routes
    """
```

**Usage Examples**:
```python
# FastAPI - Auto-discover all entities
from fastapi import FastAPI
from nitro.adapters.fastapi import configure_nitro

app = FastAPI()
configure_nitro(app)

# Flask - Explicit entity list
from flask import Flask
from nitro.adapters.flask import configure_nitro

app = Flask(__name__)
configure_nitro(app, entities=[Counter, Product, Order])

# FastHTML - With URL prefix
from fasthtml.common import fast_app
from nitro.adapters.fasthtml import configure_nitro

app, rt = fast_app()
configure_nitro(app, prefix="/api")
```

### 3. URL Generation Helpers

```python
class Entity:
    @classmethod
    def action_url(cls, action_name: str, id: Optional[str] = None, **params) -> str:
        """
        Generate URL for an entity action.

        Args:
            action_name: Name of the @action method
            id: Entity ID (optional for class methods)
            **params: Query parameters

        Returns:
            Generated URL string
        """

# Usage in templates:
Button(
    "+1",
    onclick=f"fetch('{Counter.action_url('increment', id='demo', amount=1)}')"
)
```

---

## Implementation Plan

### Phase 2.1.1: Core Decorator (Week 1)

**Deliverables**:
1. `nitro/infrastructure/routing/` module
2. `@action` decorator implementation
3. `ActionMetadata` class for storing routing info
4. Method discovery logic
5. Unit tests

**Files to Create**:
- `nitro/infrastructure/routing/__init__.py`
- `nitro/infrastructure/routing/decorator.py`
- `nitro/infrastructure/routing/metadata.py`
- `tests/test_routing_decorator.py`

### Phase 2.1.2: Base Dispatcher (Week 1-2)

**Deliverables**:
1. `NitroDispatcher` base class
2. Entity discovery system
3. Parameter extraction logic
4. Response formatting
5. Error handling
6. Unit tests

**Files to Create**:
- `nitro/infrastructure/routing/dispatcher.py`
- `tests/test_routing_dispatcher.py`

### Phase 2.1.3: FastAPI Adapter (Week 2)

**Deliverables**:
1. `FastAPIDispatcher` implementation
2. `configure_nitro()` function
3. FastAPI-specific parameter extraction
4. OpenAPI schema generation
5. Integration tests with Counter example

**Files to Create**:
- `nitro/adapters/__init__.py`
- `nitro/adapters/fastapi.py`
- `tests/test_adapter_fastapi.py`
- `examples/counter_auto_routed.py`

### Phase 2.1.4: Flask & FastHTML Adapters (Week 3)

**Deliverables**:
1. `FlaskDispatcher` implementation
2. `FastHTMLDispatcher` implementation
3. Framework-specific adaptations
4. Integration tests
5. Examples for both frameworks

**Files to Create**:
- `nitro/adapters/flask.py`
- `nitro/adapters/fasthtml.py`
- `tests/test_adapter_flask.py`
- `tests/test_adapter_fasthtml.py`
- `examples/counter_flask_auto.py`
- `examples/counter_fasthtml_auto.py`

---

## Testing Strategy

### Unit Tests
```python
def test_action_decorator_stores_metadata():
    """Verify @action stores routing metadata."""

def test_action_decorator_preserves_function():
    """Verify decorated function still works normally."""

def test_dispatcher_discovers_actions():
    """Verify dispatcher finds all @action methods."""

def test_parameter_extraction_from_query():
    """Verify parameters extracted from query string."""

def test_parameter_extraction_from_body():
    """Verify parameters extracted from JSON body."""

def test_validation_errors_return_422():
    """Verify Pydantic validation errors."""
```

### Integration Tests
```python
def test_fastapi_counter_increment():
    """E2E test: Counter increment with FastAPI."""

def test_flask_counter_reset():
    """E2E test: Counter reset with Flask."""

def test_fasthtml_counter_ui():
    """E2E test: Counter UI with FastHTML."""

def test_auto_discovery_finds_all_entities():
    """Verify auto-discovery across modules."""
```

### Example Verification
- Counter app < 50 lines ✅
- Todo app < 80 lines ✅
- Works with FastAPI, Flask, FastHTML ✅
- Type validation working ✅
- Error handling correct ✅

---

## Edge Cases & Error Handling

### 1. Entity Not Found
**Scenario**: Route called with non-existent entity ID
**Handling**: Return 404 with descriptive message
```json
{"error": "Counter with id 'nonexistent' not found"}
```

### 2. Validation Errors
**Scenario**: Invalid parameter types or values
**Handling**: Return 422 with Pydantic error details
```json
{
  "error": "Validation error",
  "details": [
    {"field": "amount", "message": "value is not a valid integer"}
  ]
}
```

### 3. Method Name Conflicts
**Scenario**: Two entities have same method name
**Handling**: No conflict - URLs are entity-scoped
- `Counter.increment()` → `/counter/{id}/increment`
- `Product.increment()` → `/product/{id}/increment`

### 4. Reserved Method Names
**Scenario**: Method named `save`, `delete`, `get` (Entity built-ins)
**Handling**: Allow decoration - user intent is clear
```python
@action()  # Explicitly marked for routing
def save(self, data: dict):
    # Custom save logic, not the Entity.save()
    ...
```

### 5. Async/Sync Method Mixing
**Scenario**: Entity has both sync and async @action methods
**Handling**: Dispatcher handles both correctly
- FastAPI: Native async support
- Flask: Run async methods in thread pool

### 6. Return Value Handling
**Scenario**: What if method returns None, dict, Entity, or Exception?
**Handling**:
- `None` → 204 No Content
- `dict` → JSON response
- `Entity` → Serialize via Pydantic
- `Exception` → 500 with error message (logged)

---

## Migration Path

### Backward Compatibility

**Existing code continues to work** - no breaking changes.

**Before** (manual routing - still works):
```python
@app.post("/api/increment")
async def increment_counter():
    counter = Counter.get("demo")
    await counter.increment()
    return {"count": counter.count}
```

**After** (auto-routing - new option):
```python
class Counter(Entity):
    @action()
    async def increment(self):
        ...

configure_nitro(app)  # Auto-generates routes
```

**Both work simultaneously** - gradual migration possible.

---

## Performance Considerations

### Startup Time
- Entity discovery runs once at startup
- Minimal overhead: ~1-5ms per entity class
- Acceptable for typical apps (< 100 entities)

### Runtime Overhead
- Parameter extraction: ~0.1-0.5ms per request
- No measurable impact on response times
- Same path as manual route handlers

### Memory Usage
- Metadata stored once per method
- Negligible: ~1KB per @action method
- No runtime memory growth

---

## Documentation Requirements

### User Guide
1. **Quickstart** - Convert Counter example
2. **Decorator Reference** - All @action parameters
3. **URL Patterns** - How URLs are generated
4. **Framework Adapters** - Using with FastAPI/Flask/FastHTML
5. **Parameter Extraction** - Query vs body vs path
6. **Error Handling** - Standard error responses
7. **Advanced Topics** - Custom paths, response models

### API Reference
- `@action` decorator
- `configure_nitro()` function
- `Entity.action_url()` method
- Adapter classes (FastAPIDispatcher, etc.)

### Examples
- Counter (basic)
- Todo (with validation)
- Blog (with authentication)
- E-commerce (complex parameters)

---

## Success Criteria

### Functional
- ✅ Counter app < 50 lines (currently 190)
- ✅ Works with FastAPI, Flask, FastHTML
- ✅ Type validation from type hints
- ✅ Automatic error handling (404, 422, 500)
- ✅ URL generation helpers work
- ✅ OpenAPI schemas generated (FastAPI)

### Performance
- ✅ Startup time < 5ms per entity
- ✅ Runtime overhead < 0.5ms per request
- ✅ Memory usage < 1KB per method

### Developer Experience
- ✅ Code reduction: 50-70%
- ✅ No breaking changes to existing code
- ✅ Clear error messages
- ✅ Works without configuration (auto-discovery)
- ✅ Gradual migration path

---

## Open Questions

### 1. Authentication/Authorization
**Question**: How to handle per-action auth requirements?
**Proposal**: Add `@action(requires_auth=True)` parameter
**Decision**: DEFER to Phase 2.2 (after base system stable)

### 2. Rate Limiting
**Question**: Per-action rate limits?
**Proposal**: `@action(rate_limit="10/minute")`
**Decision**: DEFER to Phase 2.3 (use framework middleware for now)

### 3. Caching
**Question**: Should GET actions auto-cache?
**Proposal**: `@action(method="GET", cache_ttl=300)`
**Decision**: DEFER to Phase 2.4 (manual caching for now)

### 4. WebSocket Support
**Question**: Support `@action` for WebSocket endpoints?
**Proposal**: `@action(protocol="ws")`
**Decision**: DEFER to Phase 3 (after CQRS implementation)

---

## Risk Assessment

### High Risk
**None identified** - Design follows proven patterns (Rails, Django, FastAPI)

### Medium Risk
1. **Framework Compatibility** - Untested frameworks may need custom adapters
   - *Mitigation*: Document adapter interface, provide template
2. **Complex Parameter Extraction** - Nested Pydantic models
   - *Mitigation*: Use FastAPI's existing parameter system

### Low Risk
1. **Performance** - Overhead concerns
   - *Mitigation*: Benchmark early, optimize if needed
2. **URL Conflicts** - Custom paths colliding
   - *Mitigation*: Validation at registration time

---

## Appendix A: Comparison to Other Frameworks

### Django
```python
# Django - model methods not auto-routed
class Counter(models.Model):
    count = models.IntegerField()

    def increment(self):
        self.count += 1
        self.save()

# Still need manual URLconf and views
```

### Rails
```ruby
# Rails - controller actions auto-routed
class CountersController < ApplicationController
  def increment
    @counter.increment!
  end
end

# Routes: resources :counters do
#   member { post :increment }
# end
```

**Nitro Advantage**: Business logic in domain entities, not controllers.

### FastHTML
```python
# FastHTML - decorator-based routing
@rt("/increment")
def increment():
    counter.increment()
    return Div(...)
```

**Nitro Advantage**: Routes auto-generated from entity structure.

---

## Appendix B: Example Code Reduction

### Before (190 lines)
```python
# Entity definition: 50 lines
class Counter(Entity):
    ...

# Route handlers: 90 lines (boilerplate)
@app.post("/api/increment")
async def increment_counter():
    counter = Counter.get("demo")
    if not counter:
        return JSONResponse({"error": "Counter not found"}, status_code=404)
    await counter.increment()
    return JSONResponse({"count": counter.count})

# Repeated for decrement, reset, status (3 more times)

# Frontend: 50 lines
@app.get("/")
async def homepage():
    ...
```

### After (48 lines)
```python
# Entity with auto-routing: 20 lines
class Counter(Entity, table=True):
    count: int = 0

    @action()
    async def increment(self, amount: int = 1):
        self.count += amount
        self.save()

    @action()
    async def decrement(self, amount: int = 1):
        self.count -= amount
        self.save()

    @action()
    async def reset(self):
        self.count = 0
        self.save()

# Configuration: 3 lines
app = FastAPI()
configure_nitro(app)

# Frontend: 25 lines (same)
@app.get("/")
async def homepage():
    ...
```

**Result**: 75% reduction in boilerplate, same functionality.

---

## Next Steps

1. **Review this document** with team/users (if available)
2. **Finalize decorator name** (@action confirmed)
3. **Implement Phase 2.1.1** (Core decorator)
4. **Create proof-of-concept** (Counter with auto-routing)
5. **Iterate based on feedback**

---

**Document Status**: READY FOR IMPLEMENTATION
**Est. Implementation Time**: 3-4 weeks
**Target Completion**: End of Q1 2025

---

*Design Document Version 1.0 - Session 26*
