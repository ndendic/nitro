# Route Prefixes and API Versioning Guide

## Overview

Nitro's auto-routing system supports route prefixes, enabling clean API versioning and logical route organization. This guide shows how to use prefixes effectively across all supported frameworks.

## Basic Usage

### FastAPI

```python
from fastapi import FastAPI
from nitro.adapters.fastapi import configure_nitro

app = FastAPI()

# Register routes under /api/v1 prefix
configure_nitro(
    app,
    prefix="/api/v1",
    auto_discover=True
)

# Routes become:
# POST /api/v1/counter/{id}/increment
# GET /api/v1/counter/{id}/status
```

### Flask

```python
from flask import Flask
from nitro.adapters.flask import configure_nitro

app = Flask(__name__)

# Register routes under /api/v1 prefix
configure_nitro(
    app,
    prefix="/api/v1",
    auto_discover=True
)

# Routes become:
# POST /api/v1/counter/<id>/increment
# GET /api/v1/counter/<id>/status
```

### FastHTML

```python
from fasthtml.common import fast_app
from nitro.adapters.fasthtml import configure_nitro

app, rt = fast_app()

# Register routes under /api/v1 prefix
configure_nitro(
    app,
    prefix="/api/v1",
    auto_discover=True
)

# Routes become:
# POST /api/v1/counter/{id}/increment
# GET /api/v1/counter/{id}/status
```

## API Versioning

### Multiple Versions on Same App (FastAPI & Flask)

FastAPI and Flask support multiple `configure_nitro` calls on the same app instance:

```python
from fastapi import FastAPI
from nitro import Entity, action
from nitro.adapters.fastapi import configure_nitro

# Define V1 entity
class CounterV1(Entity, table=True):
    __tablename__ = "counter_v1"
    count: int = 0

    @action()
    def increment(self, amount: int = 1):
        self.count += amount
        self.save()
        return {"count": self.count}

# Define V2 entity with enhanced features
class CounterV2(Entity, table=True):
    __tablename__ = "counter_v2"
    count: int = 0
    timestamp: str = ""

    @action()
    def increment(self, amount: int = 1):
        self.count += amount
        self.timestamp = datetime.now().isoformat()
        self.save()
        return {
            "count": self.count,
            "timestamp": self.timestamp
        }

app = FastAPI()

# Register V1
configure_nitro(app, entities=[CounterV1], prefix="/api/v1", auto_discover=False)

# Register V2
configure_nitro(app, entities=[CounterV2], prefix="/api/v2", auto_discover=False)

# Now both APIs work:
# POST /api/v1/counterv1/demo/increment  # Simple response
# POST /api/v2/counterv2/demo/increment  # Enhanced response
```

### Multiple Versions with Separate Apps (FastHTML)

FastHTML requires separate app instances for multiple versions:

```python
from fasthtml.common import fast_app
from nitro.adapters.fasthtml import configure_nitro

# V1 App
app_v1, rt_v1 = fast_app()
configure_nitro(app_v1, entities=[CounterV1], prefix="/api/v1", auto_discover=False)

# V2 App
app_v2, rt_v2 = fast_app()
configure_nitro(app_v2, entities=[CounterV2], prefix="/api/v2", auto_discover=False)

# Deploy both apps (e.g., with reverse proxy or separate ports)
```

## Prefix Patterns

### Nested Prefixes

Prefixes can be nested for complex organization:

```python
configure_nitro(
    app,
    prefix="/api/v1/admin/internal",
    entities=[AdminEntity]
)

# Routes become:
# POST /api/v1/admin/internal/user/{id}/activate
```

### Environment-Based Prefixes

Adjust prefixes based on environment:

```python
import os

prefix = os.getenv("API_PREFIX", "/api/v1")
configure_nitro(app, prefix=prefix)
```

### No Prefix

Empty string means no prefix (default behavior):

```python
configure_nitro(app, prefix="")

# Routes:
# POST /counter/{id}/increment (no prefix)
```

## Migration Strategy

### 1. Introduce V2 Alongside V1

```python
# Keep V1 running
configure_nitro(app, entities=[OldEntity], prefix="/api/v1", auto_discover=False)

# Add V2 with new features
configure_nitro(app, entities=[NewEntity], prefix="/api/v2", auto_discover=False)
```

### 2. Communicate Changes

```python
@app.get("/api/v1/status")
def v1_status():
    return {
        "version": "1.0",
        "deprecated": True,
        "sunset_date": "2025-12-31",
        "migration_guide": "/docs/v2-migration"
    }
```

### 3. Monitor Usage

```python
from nitro import on, event

@on("api_call")
def track_api_version(version):
    # Log which version is being used
    logger.info(f"API {version} called")
```

### 4. Deprecate V1

After migration period, remove V1 configuration:

```python
# V1 removed
# configure_nitro(app, entities=[OldEntity], prefix="/api/v1")  # Removed

# V2 is now primary
configure_nitro(app, entities=[NewEntity], prefix="/api/v2")
```

## Testing with Prefixes

```python
import pytest
from fastapi.testclient import TestClient

def test_v1_api():
    app = FastAPI()
    configure_nitro(app, entities=[CounterV1], prefix="/api/v1")

    client = TestClient(app)
    response = client.post("/api/v1/counterv1/test/increment")
    assert response.status_code == 200

def test_v2_api():
    app = FastAPI()
    configure_nitro(app, entities=[CounterV2], prefix="/api/v2")

    client = TestClient(app)
    response = client.post("/api/v2/counterv2/test/increment")
    assert response.status_code == 200
    assert "timestamp" in response.json()  # V2 feature
```

## Examples

See `examples/versioned_api_demo.py` for a complete working example with:
- V1 and V2 APIs running simultaneously
- Different entity behaviors per version
- Interactive documentation
- Migration guide

Run the example:

```bash
cd nitro
uvicorn examples.versioned_api_demo:app --reload --port 8090
```

Then visit:
- http://localhost:8090/ - Interactive guide
- http://localhost:8090/docs - OpenAPI documentation
- http://localhost:8090/api/v1/counterv1/demo/status - V1 endpoint
- http://localhost:8090/api/v2/counterv2/demo/status - V2 endpoint

## Best Practices

### 1. Use Semantic Versioning in Prefixes

```python
prefix="/api/v1"  # Major version only
prefix="/api/v1.2"  # Major.minor if needed
```

### 2. Keep Versions Separate

Different entities for different versions:

```python
class UserV1(Entity, table=True):
    __tablename__ = "user_v1"
    ...

class UserV2(Entity, table=True):
    __tablename__ = "user_v2"
    ...
```

### 3. Document Breaking Changes

Clearly mark which endpoints changed between versions.

### 4. Provide Migration Tools

Offer tools or scripts to help users migrate data/code from V1 to V2.

### 5. Set Sunset Dates

Communicate when old versions will be removed:

```python
@app.get("/api/v1")
def v1_info():
    return {
        "version": "1.0",
        "status": "deprecated",
        "sunset_date": "2025-12-31",
        "current_version": "/api/v2"
    }
```

## Troubleshooting

### Routes Not Found

Ensure prefix matches your request:

```python
configure_nitro(app, prefix="/api/v1")

# Correct: /api/v1/counter/demo/increment
# Wrong: /counter/demo/increment
```

### Multiple Versions Conflict (Flask)

Flask may raise endpoint conflicts. Use unique endpoint names or separate apps.

### FastHTML Multiple Registrations

FastHTML doesn't support multiple `configure_nitro` calls on same app. Use separate app instances.

## Summary

Route prefixes enable:
- ✅ Clean API versioning
- ✅ Logical route organization
- ✅ Zero-downtime migrations
- ✅ Backward compatibility
- ✅ Gradual client migration

Supported frameworks:
- ✅ FastAPI (full support, multiple versions per app)
- ✅ Flask (full support, multiple versions per app)
- ✅ FastHTML (full support, requires separate apps for multiple versions)

For more information, see:
- `tests/test_routing_prefixes_clean.py` - Test suite
- `examples/versioned_api_demo.py` - Working example
- `PHASE_2_AUTO_ROUTING_DESIGN.md` - Technical design
