"""
Versioned API Demo - Route Prefixes for API Versioning

This example demonstrates how to use route prefixes to implement
API versioning with Nitro's auto-routing system.

Features:
- Multiple API versions (v1, v2) on the same app
- Different behavior per version
- Backward compatibility
- Clean migration path

Run:
    uvicorn examples.versioned_api_demo:app --reload --port 8090

Test:
    # V1 API (simple increment)
    curl -X POST http://localhost:8090/api/v1/counter/demo/increment

    # V2 API (enhanced increment with timestamp)
    curl -X POST http://localhost:8090/api/v2/counter/demo/increment

    # Both versions work independently
    curl http://localhost:8090/api/v1/counter/demo/status
    curl http://localhost:8090/api/v2/counter/demo/status
"""

from datetime import datetime
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from nitro import Entity, action
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.adapters.fastapi import configure_nitro


# ============================================================================
# V1 ENTITIES (Original API)
# ============================================================================

class CounterV1(Entity, table=True):
    """Version 1 of Counter API - Simple counter."""
    __tablename__ = "counter_v1"

    count: int = 0
    name: str = "Counter"

    model_config = {
        "repository_class": SQLModelRepository
    }

    @action(method="POST", summary="Increment counter (v1)")
    def increment(self, amount: int = 1):
        """Simple increment - returns just the count."""
        self.count += amount
        self.save()
        return {"count": self.count}

    @action(method="POST", summary="Reset counter (v1)")
    def reset(self):
        """Reset to zero."""
        self.count = 0
        self.save()
        return {"count": 0, "message": "reset"}

    @action(method="GET", summary="Get status (v1)")
    def status(self):
        """Get current count - simple response."""
        return {
            "count": self.count,
            "name": self.name
        }


# ============================================================================
# V2 ENTITIES (Enhanced API)
# ============================================================================

class CounterV2(Entity, table=True):
    """Version 2 of Counter API - Enhanced with metadata."""
    __tablename__ = "counter_v2"

    count: int = 0
    name: str = "Counter"
    last_modified: Optional[str] = None
    total_operations: int = 0

    model_config = {
        "repository_class": SQLModelRepository
    }

    @action(method="POST", summary="Increment counter (v2 - enhanced)")
    def increment(self, amount: int = 1):
        """Enhanced increment - tracks metadata."""
        self.count += amount
        self.total_operations += 1
        self.last_modified = datetime.now().isoformat()
        self.save()
        return {
            "count": self.count,
            "amount": amount,
            "timestamp": self.last_modified,
            "total_operations": self.total_operations
        }

    @action(method="POST", summary="Decrement counter (v2 - new feature)")
    def decrement(self, amount: int = 1):
        """New feature in v2 - decrement counter."""
        self.count -= amount
        self.total_operations += 1
        self.last_modified = datetime.now().isoformat()
        self.save()
        return {
            "count": self.count,
            "amount": -amount,
            "timestamp": self.last_modified,
            "total_operations": self.total_operations
        }

    @action(method="POST", summary="Reset counter (v2)")
    def reset(self):
        """Reset with enhanced response."""
        old_count = self.count
        self.count = 0
        self.total_operations += 1
        self.last_modified = datetime.now().isoformat()
        self.save()
        return {
            "count": 0,
            "previous_count": old_count,
            "message": "reset",
            "timestamp": self.last_modified
        }

    @action(method="GET", summary="Get status (v2 - enhanced)")
    def status(self):
        """Enhanced status with metadata."""
        return {
            "count": self.count,
            "name": self.name,
            "last_modified": self.last_modified,
            "total_operations": self.total_operations,
            "version": "2.0"
        }


# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="Versioned API Demo",
    description="Demonstrates API versioning using route prefixes",
    version="2.0.0"
)


# Register V1 API
configure_nitro(
    app,
    entities=[CounterV1],
    prefix="/api/v1",
    auto_discover=False
)

# Register V2 API
configure_nitro(
    app,
    entities=[CounterV2],
    prefix="/api/v2",
    auto_discover=False
)


# Initialize database tables
CounterV1.repository().init_db()
CounterV2.repository().init_db()


# ============================================================================
# DOCUMENTATION ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
def home():
    """Home page with API documentation."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Versioned API Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            h2 { color: #666; margin-top: 30px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }
            .method {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
                margin-right: 10px;
            }
            .post { background: #28a745; color: white; }
            .get { background: #17a2b8; color: white; }
            code { background: #eee; padding: 2px 6px; border-radius: 3px; }
            .example { background: #fff3cd; padding: 10px; margin-top: 10px; border-radius: 4px; }
            .version { display: inline-block; background: #007bff; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
        </style>
    </head>
    <body>
        <h1>🚀 Versioned API Demo</h1>
        <p>This demo shows how to implement API versioning using Nitro's route prefix feature.</p>

        <h2>API V1 <span class="version">Legacy</span></h2>
        <p>Simple counter API with basic functionality</p>

        <div class="endpoint">
            <span class="method post">POST</span>
            <code>/api/v1/counterv1/{id}/increment</code>
            <p>Increment counter by amount (default: 1)</p>
            <div class="example">
                <strong>Example:</strong><br>
                curl -X POST "http://localhost:8090/api/v1/counterv1/demo/increment?amount=5"
            </div>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/v1/counterv1/{id}/status</code>
            <p>Get current counter status</p>
            <div class="example">
                <strong>Example:</strong><br>
                curl http://localhost:8090/api/v1/counterv1/demo/status
            </div>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span>
            <code>/api/v1/counterv1/{id}/reset</code>
            <p>Reset counter to zero</p>
        </div>

        <h2>API V2 <span class="version">Current</span></h2>
        <p>Enhanced counter API with metadata tracking and new features</p>

        <div class="endpoint">
            <span class="method post">POST</span>
            <code>/api/v2/counterv2/{id}/increment</code>
            <p>Enhanced increment with timestamp and operation tracking</p>
            <div class="example">
                <strong>Example:</strong><br>
                curl -X POST "http://localhost:8090/api/v2/counterv2/demo/increment?amount=5"<br>
                <strong>Response includes:</strong> count, timestamp, total_operations
            </div>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span>
            <code>/api/v2/counterv2/{id}/decrement</code>
            <p><strong>NEW:</strong> Decrement counter (not available in v1)</p>
            <div class="example">
                <strong>Example:</strong><br>
                curl -X POST "http://localhost:8090/api/v2/counterv2/demo/decrement?amount=3"
            </div>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/v2/counterv2/{id}/status</code>
            <p>Enhanced status with last_modified and total_operations</p>
            <div class="example">
                <strong>Example:</strong><br>
                curl http://localhost:8090/api/v2/counterv2/demo/status
            </div>
        </div>

        <h2>Migration Guide</h2>
        <p>When migrating from V1 to V2:</p>
        <ul>
            <li>Both APIs run simultaneously - no downtime</li>
            <li>V1 clients continue to work unchanged</li>
            <li>V2 clients get enhanced features</li>
            <li>Entities are separate (different tables)</li>
            <li>Gradually migrate clients to V2</li>
            <li>Deprecate V1 when all clients migrated</li>
        </ul>

        <h2>Interactive API Docs</h2>
        <p><a href="/docs">OpenAPI Documentation (Swagger UI)</a></p>
        <p><a href="/redoc">ReDoc Documentation</a></p>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
