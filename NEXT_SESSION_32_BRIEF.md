# Session 32 Briefing - Phase 2.2 Custom Route Naming

**Previous Session**: 31 (Route prefixes & versioning complete)
**Current Phase**: Phase 2.2 - Priority 1 complete → Priority 2 next
**Next Goal**: Implement custom route naming

---

## Quick Status

✅ **Phase 2.2 Priority 1**: COMPLETE - Route prefixes & versioning (10 tests)
🎯 **Phase 2.2 Priority 2**: Not started - Custom route naming
📋 **Next**: Custom path patterns for entities and actions

---

## What's Done (Phase 2.2 Priority 1)

### ✅ Route Prefixes & API Versioning

**Tests**: 10/10 passing
- FastAPI: Single/multiple prefixes, versioning
- Flask: Single prefix support
- Edge cases: Nested, normalized, empty

**Example App**: `examples/versioned_api_demo.py`
- V1 and V2 APIs coexist
- Interactive documentation
- Migration guide

**Documentation**: `docs/route_prefixes_guide.md`
- Usage for all frameworks
- Best practices
- Troubleshooting

---

## Phase 2.2 Priority 2: Custom Route Naming

### Goal

Allow developers to customize:
1. Entity route names (e.g., "users" instead of "user")
2. Action paths (e.g., "/add" instead of "/increment")
3. Path templates with variables
4. Route organization patterns

### Current Behavior (Automatic)

```python
class Counter(Entity):
    @action()
    def increment(self, amount: int = 1):
        ...

# Generates: POST /counter/{id}/increment
```

### Desired Behavior (Customizable)

```python
class Counter(Entity):
    __route_name__ = "counters"  # Plural form

    @action(method="POST", path="/add")  # Custom path
    def increment(self, amount: int = 1):
        ...

# Generates: POST /counters/{id}/add
```

---

## Implementation Plan

### Step 1: Update ActionMetadata (30 min)

**File**: `nitro/infrastructure/routing/metadata.py`

Add `custom_path` parameter:

```python
@dataclass
class ActionMetadata:
    method: str
    path: Optional[str] = None  # NEW: Custom path
    status_code: int = 200
    summary: Optional[str] = None
    description: Optional[str] = None

    def generate_url_path(self, prefix: str = "", entity_name_override: Optional[str] = None) -> str:
        """Generate URL path with custom overrides."""
        entity_name = entity_name_override or self.entity_name.lower()

        if self.path:  # Use custom path if provided
            action_path = self.path
        else:  # Use method name
            action_path = self.method_name

        # Build path
        ...
```

### Step 2: Update @action Decorator (30 min)

**File**: `nitro/infrastructure/routing/decorator.py`

Add `path` parameter:

```python
def action(
    method: str = "POST",
    path: Optional[str] = None,  # NEW
    status_code: int = 200,
    summary: Optional[str] = None,
    description: Optional[str] = None
) -> Callable:
    """
    Decorator for entity methods to create auto-routed endpoints.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: Custom path override (e.g., "/add" instead of "/increment")
        status_code: HTTP status code for successful response
        summary: OpenAPI summary
        description: OpenAPI description
    """
    ...
```

### Step 3: Add Entity-Level Route Name (30 min)

**File**: `nitro/infrastructure/routing/discovery.py`

Check for `__route_name__` attribute:

```python
def discover_action_methods(entity_class: Type[Entity]) -> Dict[str, ActionMetadata]:
    """Find all @action methods, respecting __route_name__."""

    # Check for custom entity route name
    route_name = getattr(entity_class, '__route_name__', None)
    if not route_name:
        route_name = entity_class.__name__.lower()

    # Pass route_name to metadata generation
    ...
```

### Step 4: Create Tests (1 hour)

**File**: `tests/test_routing_custom_paths.py`

Test scenarios:
1. Custom action path (`@action(path="/add")`)
2. Custom entity name (`__route_name__ = "users"`)
3. Both custom entity and action paths
4. Path with leading slash normalized
5. Path without leading slash
6. Nested custom paths
7. Works across all adapters (FastAPI, Flask, FastHTML)

### Step 5: Update Adapters (30 min)

Ensure all adapters respect custom paths:
- `nitro/adapters/fastapi.py`
- `nitro/adapters/flask.py`
- `nitro/adapters/fasthtml.py`

(Should work automatically if metadata is correct)

### Step 6: Create Example (30 min)

**File**: `examples/custom_routes_demo.py`

Demonstrate:
- RESTful routes (users, posts, comments)
- Custom action names
- Clean URL structure
- Professional API design

### Step 7: Documentation (30 min)

**File**: `docs/custom_route_naming.md`

Cover:
- Basic usage
- Entity-level customization
- Action-level customization
- Path templates
- Best practices
- Examples

---

## Expected API

### Entity-Level Customization

```python
class User(Entity):
    __route_name__ = "users"  # Override default "user"

    @action()
    def activate(self):
        ...

# Routes: POST /users/{id}/activate
```

### Action-Level Customization

```python
class Counter(Entity):
    @action(path="/add")  # Override default "increment"
    def increment(self, amount: int = 1):
        ...

# Routes: POST /counter/{id}/add
```

### Combined Customization

```python
class BlogPost(Entity):
    __route_name__ = "posts"

    @action(method="POST", path="/publish")
    def make_public(self):
        ...

    @action(method="GET", path="/stats")
    def get_statistics(self):
        ...

# Routes:
# POST /posts/{id}/publish
# GET /posts/{id}/stats
```

---

## Success Criteria

- [ ] `path` parameter works in @action decorator
- [ ] `__route_name__` class attribute works
- [ ] Paths are normalized (leading slash handling)
- [ ] Works with all 3 adapters
- [ ] 10+ tests passing
- [ ] Example app demonstrates patterns
- [ ] Documentation complete
- [ ] No regressions in existing 483 tests

---

## Current Test Status

```
Total pytest: 483 passing
- Phase 1: 360 tests
- Phase 2.1: 106 tests (auto-routing)
- Phase 2.2 Priority 1: 10 tests (prefixes)
- Phase 2.2 Priority 2: 0 tests (not started)

Feature tests: 171/171 passing
```

---

## Files to Modify

1. `nitro/infrastructure/routing/metadata.py` - Add `path` parameter
2. `nitro/infrastructure/routing/decorator.py` - Support `path` arg
3. `nitro/infrastructure/routing/discovery.py` - Check `__route_name__`
4. `tests/test_routing_custom_paths.py` - NEW: Test suite
5. `examples/custom_routes_demo.py` - NEW: Example app
6. `docs/custom_route_naming.md` - NEW: Documentation

---

## Potential Challenges

### 1. Path Normalization

Handle various path formats:
- `/add` - Leading slash
- `add` - No leading slash
- `/admin/add` - Nested path
- `add/` - Trailing slash

**Solution**: Normalize in `ActionMetadata.generate_url_path()`

### 2. Conflicts with Entity ID

Ensure custom paths don't conflict with `{id}` parameter:

```python
# Bad: /user/all (conflicts with /user/{id})
# Good: /users (entity level) or /user/{id}/list
```

**Solution**: Document best practices, validate at registration time

### 3. OpenAPI Schema

Custom paths should appear correctly in OpenAPI docs.

**Solution**: Test with FastAPI's `/docs` endpoint

---

## Testing Strategy

### Unit Tests

Test metadata generation:
```python
def test_custom_path_in_metadata():
    """@action(path="/add") sets correct path in metadata."""
    ...
```

### Integration Tests

Test with all adapters:
```python
def test_custom_path_works_with_fastapi():
    """Custom path generates correct FastAPI route."""
    ...
```

### Functional Tests

Test actual HTTP requests:
```python
def test_custom_path_responds():
    """Request to custom path returns correct response."""
    ...
```

---

## Example Implementation Snippets

### metadata.py Changes

```python
@dataclass
class ActionMetadata:
    # ... existing fields ...
    path: Optional[str] = None  # NEW

    def generate_url_path(
        self,
        prefix: str = "",
        entity_name_override: Optional[str] = None
    ) -> str:
        """Generate URL with custom overrides."""
        entity_name = entity_name_override or self.entity_name.lower()

        # Use custom path if provided
        if self.path:
            action_segment = self.path.lstrip('/')
        else:
            action_segment = self.method_name

        # Build final path
        if prefix:
            return f"{prefix}/{entity_name}/{{id}}/{action_segment}"
        return f"/{entity_name}/{{id}}/{action_segment}"
```

### decorator.py Changes

```python
def action(
    method: str = "POST",
    path: Optional[str] = None,  # NEW
    status_code: int = 200,
    summary: Optional[str] = None,
    description: Optional[str] = None
) -> Callable:
    def decorator(func: Callable) -> Callable:
        metadata = ActionMetadata(
            method=method,
            path=path,  # Store custom path
            status_code=status_code,
            summary=summary or func.__doc__,
            description=description,
            entity_name=...,
            method_name=func.__name__,
            requires_id=...,
            parameters=...
        )
        ...
```

---

## Time Estimate

- Step 1: Metadata updates (30 min)
- Step 2: Decorator updates (30 min)
- Step 3: Discovery updates (30 min)
- Step 4: Tests (1 hour)
- Step 5: Adapter verification (30 min)
- Step 6: Example app (30 min)
- Step 7: Documentation (30 min)

**Total: ~4 hours**

---

## Alternative: If Time is Limited

**Minimum Viable Implementation** (2 hours):
1. Add `path` parameter to @action only
2. Basic tests (5 tests)
3. Simple example
4. Brief documentation

**Skip for now**:
- `__route_name__` entity-level override (do in next session)
- Complex path templates
- Advanced patterns

---

## Running Tests After Implementation

```bash
# All tests
uv run pytest tests/ -v

# Just new tests
uv run pytest tests/test_routing_custom_paths.py -v

# Verify no regressions
uv run pytest tests/test_routing_decorator.py -v
uv run pytest tests/test_routing_prefixes_clean.py -v
```

---

## Documentation to Reference

1. `PHASE_2_AUTO_ROUTING_DESIGN.md` - Original design
2. `nitro/infrastructure/routing/metadata.py` - Current metadata class
3. `nitro/infrastructure/routing/decorator.py` - Current decorator
4. `tests/test_routing_decorator.py` - Existing decorator tests
5. `SESSION_31_SUMMARY.md` - Previous session summary

---

## Success Metrics

- **Tests**: 10+ new tests, all passing
- **Code Quality**: Clean, documented, follows patterns
- **No Regressions**: All 483 existing tests still pass
- **Example Works**: Demo app runs and shows custom routes
- **Docs Complete**: Guide explains all features with examples

---

**Prepared by**: Session 31 Agent
**Ready for**: Session 32 (Phase 2.2 Priority 2 - Custom Route Naming)
