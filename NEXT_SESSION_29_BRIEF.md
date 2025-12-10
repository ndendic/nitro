# Session 29 Briefing - Implement Flask Adapter (Phase 2.1.4)

**Previous Session**: 28 (FastAPI adapter complete)
**Current Phase**: Phase 2.1.4 - Flask Adapter (not started)
**Next Goal**: Complete Flask adapter implementation and testing

---

## Quick Status

✅ **Phase 2.1.3**: COMPLETE - FastAPI adapter (85/85 tests passing)
⏳ **Phase 2.1.4**: Not started - Flask & FastHTML adapters
📋 **Next**: Implement Flask adapter (~2-3 hours)

---

## What's Done (Phase 2.1.3)

### ✅ FastAPI Adapter (100%)
- `nitro/adapters/fastapi.py` (249 lines) - Fully working
- 20/20 integration tests passing
- Counter example app tested end-to-end
- All parameter extraction working (path, query, body)
- Error handling working (404, 422, 500)
- OpenAPI schema generation working

### ✅ Base Infrastructure (100%)
- `nitro/infrastructure/routing/dispatcher.py` - Framework-agnostic base
- `nitro/infrastructure/routing/decorator.py` - @action decorator
- `nitro/infrastructure/routing/discovery.py` - Entity/action discovery
- `nitro/infrastructure/routing/metadata.py` - ActionMetadata dataclass

---

## Phase 2.1.4 Goal

Implement Flask and FastHTML adapters following the FastAPI pattern.

### Deliverables

1. **Flask Adapter**
   - `nitro/adapters/flask.py` - FlaskDispatcher class
   - `tests/test_adapter_flask.py` - Integration tests (20 tests)
   - `examples/flask_counter_auto_routed.py` - Example app
   - Estimated: 2-3 hours

2. **FastHTML Adapter**
   - `nitro/adapters/fasthtml.py` - FastHTMLDispatcher class
   - `tests/test_adapter_fasthtml.py` - Integration tests (20 tests)
   - `examples/fasthtml_counter_auto_routed.py` - Example app
   - Estimated: 2-3 hours

---

## Implementation Plan for Flask Adapter

### Step 1: Create FlaskDispatcher (45 min)

Reference: `nitro/adapters/fastapi.py`

Key differences from FastAPI:
- Flask uses `@app.route()` instead of `app.add_api_route()`
- Flask request handling: `from flask import request, jsonify`
- Parameter extraction: `request.args` (query), `request.json` (body), `request.view_args` (path)
- No built-in OpenAPI support

```python
# nitro/adapters/flask.py
from flask import Flask, request, jsonify
from typing import Type, Callable, Optional
from ..infrastructure.routing import NitroDispatcher, ActionMetadata
from ..domain.entities.base_entity import Entity

class FlaskDispatcher(NitroDispatcher):
    """Flask adapter for auto-routing."""

    def __init__(self, app: Flask, prefix: str = ""):
        super().__init__(prefix)
        self.app = app

    def register_route(
        self,
        entity_class: Type[Entity],
        method: Callable,
        metadata: ActionMetadata
    ) -> None:
        """Register route with Flask."""
        url_path = metadata.generate_url_path(self.prefix)

        # Flask route handler
        def route_handler(**path_params):
            # Extract parameters from Flask request
            request_data = {
                "path": path_params,
                "query": dict(request.args),
                "body": request.json if request.is_json else {}
            }

            # Dispatch (sync wrapper for async dispatch)
            if metadata.is_async:
                import asyncio
                result = asyncio.run(
                    self.dispatch(entity_class, method, metadata, request_data)
                )
            else:
                result = self.dispatch(entity_class, method, metadata, request_data)

            # Handle errors
            if isinstance(result, dict) and "error" in result:
                error_status = result["error"].get("status_code", 500)
                return jsonify(result), error_status

            # Success response
            response_data = self.format_response(result, metadata)
            return jsonify(response_data), metadata.status_code

        # Set unique endpoint name (required by Flask)
        endpoint_name = f"{entity_class.__name__}_{metadata.function_name}"

        # Register with Flask
        self.app.add_url_rule(
            url_path,
            endpoint=endpoint_name,
            view_func=route_handler,
            methods=[metadata.method]
        )

def configure_nitro(
    app: Flask,
    entity_base_class: Type[Entity] = None,
    entities: Optional[List[Type[Entity]]] = None,
    auto_discover: bool = True,
    prefix: str = ""
) -> FlaskDispatcher:
    """Configure Nitro auto-routing for Flask."""
    from ..domain.entities.base_entity import Entity as DefaultEntity

    if entity_base_class is None:
        entity_base_class = DefaultEntity

    dispatcher = FlaskDispatcher(app, prefix)
    dispatcher.configure(entity_base_class, entities, auto_discover)
    return dispatcher
```

### Step 2: Create Flask Tests (30 min)

Copy structure from `tests/test_adapter_fastapi.py`:

```python
# tests/test_adapter_flask.py
import pytest
from flask import Flask
from flask.testing import FlaskClient

from nitro import Entity, action
from nitro.adapters.flask import configure_nitro
from nitro.infrastructure.repository.sql import SQLModelRepository

@pytest.fixture
def app():
    """Create Flask app with Nitro configured."""
    app = Flask(__name__)

    # Initialize entities
    TestCounter.repository().init_db()

    # Configure Nitro
    configure_nitro(app, entities=[TestCounter], auto_discover=False)

    return app

@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()

class TestFlaskConfiguration:
    def test_configure_nitro_discovers_entities(self, client):
        """Routes are registered."""
        response = client.post("/testcounter/test1/increment")
        assert response.status_code in [200, 404]  # Either works or entity missing

    # ... more tests
```

### Step 3: Create Flask Example (15 min)

```python
# examples/flask_counter_auto_routed.py
from flask import Flask
from nitro import Entity, action
from nitro.adapters.flask import configure_nitro
from nitro.infrastructure.repository.sql import SQLModelRepository

class Counter(Entity, table=True):
    count: int = 0
    name: str = "Counter"

    model_config = {"repository_class": SQLModelRepository}

    @action(method="POST")
    def increment(self, amount: int = 1):
        self.count += amount
        self.save()
        return {"count": self.count, "message": f"Incremented by {amount}"}

    # ... more actions

if __name__ == "__main__":
    # Initialize
    Counter.repository().init_db()
    Counter(id="demo", count=0).save()

    # Create Flask app
    app = Flask(__name__)
    configure_nitro(app)

    print("Routes:", [str(rule) for rule in app.url_map.iter_rules()])

    # Run
    app.run(host="0.0.0.0", port=8091, debug=False)
```

### Step 4: Test & Fix (30 min)

1. Run tests: `pytest tests/test_adapter_flask.py -v`
2. Fix any issues (likely async/sync handling)
3. Test example app manually
4. Commit when all passing

---

## Key Differences: FastAPI vs Flask

| Aspect | FastAPI | Flask |
|--------|---------|-------|
| Route registration | `app.add_api_route()` | `app.add_url_rule()` |
| Request object | `Request` from Starlette | `request` from Flask globals |
| Query params | `request.query_params` | `request.args` |
| JSON body | `await request.json()` | `request.json` (sync) |
| Path params | Function parameter | `**path_params` in view func |
| Response | `JSONResponse(content, status_code)` | `jsonify(data), status_code` |
| Async support | Native async/await | Requires `asyncio.run()` wrapper |
| OpenAPI | Built-in | None (need flask-restx) |
| Endpoint naming | Auto-generated | Must be unique string |

---

## Pitfalls to Avoid

1. **Flask endpoint names must be unique** - Use `f"{entity}_{action}"` pattern
2. **Flask request is a global** - Must be accessed inside route handler
3. **Flask doesn't support async natively** - Wrap async dispatch with `asyncio.run()`
4. **Flask test client returns response objects** - Use `response.get_json()` not `response.json()`
5. **Flask view function signature** - Path params come as `**kwargs`

---

## Testing Strategy

1. Create minimal Flask app with one entity
2. Test route registration works
3. Test parameter extraction (query, JSON body, path)
4. Test error handling (404, 422, 500)
5. Test async action support
6. Test multiple entities
7. Test persistence across requests

---

## Success Criteria

- [ ] All 20 Flask adapter tests passing
- [ ] Flask counter app works end-to-end
- [ ] No console errors
- [ ] Documentation updated
- [ ] Commit made with summary

**Expected Time**: 2 hours for Flask adapter

---

## After Flask is Done

Move to FastHTML adapter (similar process, ~2 hours).

Then Phase 2.1.4 is complete and we can move to Phase 2.2 (advanced features).

---

## Quick Start Commands

```bash
# Navigate to project
cd /home/ndendic/Projects/auto-nitro/nitro

# Create Flask adapter
touch nitro/adapters/flask.py
# (Implement FlaskDispatcher)

# Create tests
touch tests/test_adapter_flask.py
# (Copy/adapt from test_adapter_fastapi.py)

# Create example
touch examples/flask_counter_auto_routed.py
# (Copy/adapt from counter_auto_routed.py)

# Run tests
pytest tests/test_adapter_flask.py -v

# Test example
PYTHONPATH=/home/ndendic/Projects/auto-nitro/nitro:$PYTHONPATH python3 examples/flask_counter_auto_routed.py
```

---

## Reference Files

- `nitro/adapters/fastapi.py` - Reference implementation
- `tests/test_adapter_fastapi.py` - Test pattern
- `examples/counter_auto_routed.py` - Example pattern
- `nitro/infrastructure/routing/dispatcher.py` - Base class

---

*Prepared by Session 28 Agent*
*Ready for Session 29*
