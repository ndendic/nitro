# Session 31 Briefing - Phase 2.2 Advanced Routing Features

**Previous Session**: 30 (FastHTML adapter complete)
**Current Phase**: Phase 2.1.4 Complete → Ready for Phase 2.2
**Next Goal**: Implement advanced routing features

---

## Quick Status

✅ **Phase 2.1.4**: COMPLETE - All 3 framework adapters working (119 tests)
🎯 **Phase 2.2**: Not started - Advanced routing features
📋 **Next**: Advanced routing patterns and features

---

## What's Done (Phase 2.1)

### ✅ Phase 2.1.1-2.1.4: Complete Auto-Routing System

**Base Infrastructure:**
- `nitro/infrastructure/routing/dispatcher.py` - NitroDispatcher base class
- `nitro/infrastructure/routing/decorator.py` - @action decorator
- `nitro/infrastructure/routing/discovery.py` - Entity/action discovery
- `nitro/infrastructure/routing/metadata.py` - ActionMetadata dataclass

**Framework Adapters:**
1. **FastAPI** (`nitro/adapters/fastapi.py`) - 85 tests passing ✓
2. **Flask** (`nitro/adapters/flask.py`) - 17 tests passing ✓
3. **FastHTML** (`nitro/adapters/fasthtml.py`) - 17 tests passing ✓

**Total**: 119 tests passing for auto-routing system

---

## Phase 2.2 Goals

Implement advanced routing features that enhance the base auto-routing system:

### Priority 1: Route Prefixes & Versioning

**Goal**: Allow grouping routes under prefixes for API versioning

```python
# Example usage
configure_nitro(app, prefix="/api/v1")
# Routes become: /api/v1/counter/{id}/increment

configure_nitro(app, prefix="/api/v2")
# Routes become: /api/v2/counter/{id}/increment
```

**Implementation:**
- Already partially supported in adapters
- Need to add prefix inheritance in ActionMetadata
- Add tests for prefix handling

**Estimated Time**: 1-2 hours

### Priority 2: Custom Route Naming

**Goal**: Allow customizing route paths per entity or action

```python
class Counter(Entity, table=True):
    __route_name__ = "counters"  # Override default lowercase name

    @action(method="POST", path="/add")  # Custom path
    def increment(self, amount: int = 1):
        ...
```

**Implementation:**
- Add `path` parameter to @action decorator
- Add `__route_name__` class attribute support
- Update URL path generation in ActionMetadata

**Estimated Time**: 2-3 hours

### Priority 3: Route Grouping

**Goal**: Group related actions under common paths

```python
@action_group("/admin")
class Counter(Entity):
    @action()  # becomes /admin/counter/{id}/increment
    def increment(self): ...
```

**Implementation:**
- Create @action_group decorator
- Store group metadata on entity class
- Combine group path + entity path + action path

**Estimated Time**: 2-3 hours

### Priority 4: Middleware Integration

**Goal**: Allow per-action middleware/hooks

```python
@action(method="POST", middleware=[auth_required, rate_limit])
def increment(self, amount: int = 1):
    ...
```

**Implementation:**
- Add `middleware` parameter to @action
- Store middleware list in ActionMetadata
- Framework adapters apply middleware in route registration

**Estimated Time**: 3-4 hours

---

## Recommended Starting Point

**Start with Priority 1: Route Prefixes & Versioning**

This is the most straightforward and immediately useful feature.

### Step 1: Add Prefix Tests (30 min)

Create `tests/test_routing_prefixes.py`:

```python
def test_fastapi_with_prefix():
    """Routes include prefix."""
    app = FastAPI()
    configure_nitro(app, prefix="/api/v1", entities=[Counter])

    client = TestClient(app)
    response = client.post("/api/v1/counter/test1/increment")
    assert response.status_code == 200

def test_multiple_prefixes():
    """Can register same entity under different prefixes."""
    app = FastAPI()
    configure_nitro(app, prefix="/api/v1", entities=[Counter])
    configure_nitro(app, prefix="/api/v2", entities=[Counter])

    # Both should work
    client = TestClient(app)
    assert client.post("/api/v1/counter/test1/increment").status_code == 200
    assert client.post("/api/v2/counter/test1/increment").status_code == 200
```

### Step 2: Verify Current Behavior (15 min)

Test that prefixes already work (they should based on adapter code).

### Step 3: Add Documentation (30 min)

Document prefix usage in:
- README.md
- API reference
- Examples

### Step 4: Add Examples (30 min)

Create `examples/versioned_api_demo.py`:
- Shows v1 and v2 of same API
- Different behavior in each version
- Migration guide

---

## Alternative: Additional Framework Adapters

If Phase 2.2 advanced features aren't desired yet, could implement:

### Option A: Django Adapter

**Pros:**
- Large Django community
- Popular enterprise framework
- Pattern already proven with 3 adapters

**Cons:**
- Django has different routing philosophy
- More complex integration
- May require Django-specific features

**Estimated Time**: 4-6 hours

### Option B: Sanic Adapter

**Pros:**
- Async-first like FastAPI
- Easy integration (similar to FastAPI)
- Fast growing adoption

**Cons:**
- Smaller community than Django
- Less critical for Phase 2 goals

**Estimated Time**: 2-3 hours

### Option C: Starlette Adapter

**Pros:**
- Foundation for FastAPI and FastHTML
- Direct control over ASGI
- Lightweight and fast

**Cons:**
- Less commonly used directly
- FastAPI already covers most use cases

**Estimated Time**: 2-3 hours

---

## Recommendation

**Proceed with Phase 2.2 Priority 1: Route Prefixes & Versioning**

**Rationale:**
1. Immediately useful for all 3 existing adapters
2. Foundation for other advanced features
3. Quick win (1-2 hours)
4. Validates architecture for advanced features

**After that**, continue with Priority 2 (Custom Route Naming) or assess if additional framework adapters are needed based on user feedback.

---

## Testing Strategy

For Phase 2.2 features:

1. **Unit tests**: Test each feature in isolation
2. **Integration tests**: Test with all 3 adapters (FastAPI, Flask, FastHTML)
3. **Example apps**: Create working examples for each feature
4. **Documentation**: Update docs with usage patterns

**Test Coverage Goal**: 90%+ for new features

---

## Files to Review Before Starting

1. `nitro/infrastructure/routing/decorator.py` - @action implementation
2. `nitro/infrastructure/routing/metadata.py` - ActionMetadata class
3. `nitro/adapters/fastapi.py` - Reference adapter implementation
4. `SESSION_30_SUMMARY.md` - Recent changes and patterns

---

## Success Criteria for Priority 1

- [ ] Route prefixes work with all 3 adapters
- [ ] Can register same entity under multiple prefixes
- [ ] Tests passing for prefix scenarios
- [ ] Documentation updated
- [ ] Example app demonstrating versioned API
- [ ] No regression in existing 119 tests

**Expected Time**: 1-2 hours for Phase 2.2 Priority 1

---

## Quick Start Commands

```bash
# Navigate to project
cd /home/ndendic/Projects/auto-nitro/nitro

# Create test file
touch tests/test_routing_prefixes.py

# Run existing tests to verify clean state
uv run pytest tests/test_adapter_*.py -v

# Create example
touch examples/versioned_api_demo.py

# Run tests after implementation
uv run pytest tests/test_routing_prefixes.py -v
```

---

## Notes

- All 171 original features still passing ✓
- Auto-routing system working perfectly ✓
- Clean architecture makes advanced features straightforward
- Consider user feedback to prioritize features

---

*Prepared by Session 30 Agent*
*Ready for Session 31*
