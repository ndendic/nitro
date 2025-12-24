# Flask Integration

Nitro provides comprehensive Flask support with automatic route registration, both sync and async method support, and JSON response handling.

## Quick Start

```python
from flask import Flask, jsonify
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.adapters.flask import configure_nitro
from nitro.infrastructure.routing import action

# Define entity
class Counter(Entity, table=True):
    count: int = 0

    @action(method="POST", summary="Increment counter")
    def increment(self, amount: int = 1):
        """Increment counter by specified amount."""
        self.count += amount
        self.save()
        return {"count": self.count, "id": self.id}

    @action(method="POST", summary="Decrement counter")
    def decrement(self, amount: int = 1):
        """Decrement counter by specified amount."""
        self.count -= amount
        self.save()
        return {"count": self.count, "id": self.id}

    @action(method="GET", summary="Get counter value")
    def value(self):
        """Get the current counter value."""
        return {"count": self.count, "id": self.id}

    @action(method="GET", summary="List all counters")
    @classmethod
    def list_all(cls):
        """Retrieve all counter instances."""
        return [c.model_dump() for c in cls.all()]

# Create Flask app
app = Flask(__name__)

# Initialize database
SQLModelRepository().init_db()

# Auto-register all routes
configure_nitro(app)

if __name__ == "__main__":
    app.run(debug=True)
```

**Generated Routes:**
- `POST /counter/{id}/increment` - Increment counter
- `POST /counter/{id}/decrement` - Decrement counter
- `GET /counter/{id}/value` - Get counter value
- `GET /counter/list_all` - List all counters

## configure_nitro() API

**Source:** `nitro/adapters/flask.py:167-204`

```python
def configure_nitro(
    app: Flask,
    entities: Optional[List[Type[Entity]]] = None,
    prefix: str = "",
    auto_discover: bool = True
) -> FlaskDispatcher:
    """
    Configure Nitro auto-routing for Flask application.

    Args:
        app: Flask application instance
        entities: Specific entities to register (None = all entities)
        prefix: URL prefix for all routes (e.g., "/api/v1")
        auto_discover: Auto-discover all Entity subclasses (default: True)

    Returns:
        FlaskDispatcher instance for advanced configuration

    Example:
        >>> app = Flask(__name__)
        >>> configure_nitro(app, prefix="/api/v1")
    """
```

### Basic Usage

```python
from flask import Flask
from nitro.adapters.flask import configure_nitro

app = Flask(__name__)
configure_nitro(app)  # Auto-discovers and registers all entities
```

### With URL Prefix

```python
# All routes will start with /api/v1
configure_nitro(app, prefix="/api/v1")

# Counter.increment() → POST /api/v1/counter/{id}/increment
```

### Manual Entity Registration

```python
from myapp.models import Counter, Todo, User

configure_nitro(
    app,
    entities=[Counter, Todo],
    auto_discover=False
)
```

## FlaskDispatcher Class

**Source:** `nitro/adapters/flask.py:41-165`

The `FlaskDispatcher` integrates Nitro's entity system with Flask's routing:

```python
from nitro.adapters.flask import FlaskDispatcher

dispatcher = FlaskDispatcher(app, prefix="/api")
dispatcher.configure(
    entity_base_class=Entity,
    auto_discover=True
)
```

### Features

- ✅ Automatic route registration
- ✅ Path, query, and body parameter extraction
- ✅ Sync and async method support
- ✅ JSON response handling
- ✅ Consistent error handling (404, 422, 500)
- ✅ Flask blueprint compatibility

## Parameter Handling

### Path Parameters

The entity `{id}` is automatically extracted from the URL:

```python
@action(method="GET")
def status(self):
    # 'self' is the loaded entity instance
    return {"id": self.id, "status": self.status}

# GET /order/<id>/status
# Note: Flask uses <id> instead of {id} in route definitions
# → Automatically loads Order with specified id
```

### Query Parameters (GET Requests)

```python
@action(method="GET")
def search(self, query: str, limit: int = 10):
    # Parameters extracted from query string
    results = self.filter(name__contains=query)
    return results[:limit]

# GET /product/p1/search?query=widget&limit=5
```

### Body Parameters (POST/PUT/PATCH)

```python
from typing import List

@action(method="POST")
def update(self, name: str, price: float, tags: List[str] = []):
    # Parameters extracted from JSON request body
    self.name = name
    self.price = price
    self.tags = tags
    self.save()
    return self.model_dump()

# POST /product/p1/update
# Content-Type: application/json
# Body: {"name": "Widget", "price": 9.99, "tags": ["electronics"]}
```

### Pydantic Models as Parameters

```python
from pydantic import BaseModel

class ProductUpdate(BaseModel):
    name: str
    price: float
    description: str

@action(method="PUT")
def update_details(self, data: ProductUpdate):
    # 'data' is automatically validated
    self.name = data.name
    self.price = data.price
    self.description = data.description
    self.save()
    return self.model_dump()

# PUT /product/p1/update_details
# Body: {"name": "Widget", "price": 9.99, "description": "A useful widget"}
```

## Async/Await Support

Nitro supports async entity methods with Flask:

```python
import httpx
from nitro.infrastructure.routing import action

class Product(Entity, table=True):
    name: str
    external_id: str

    @action(method="POST")
    async def sync_with_external(self):
        """Sync product data with external API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.example.com/products/{self.external_id}"
            )
            data = response.json()
            self.name = data["name"]
            self.save()
            return {"synced": True, "name": self.name}

# The Flask adapter will run async methods using asyncio.run()
```

**Note:** Flask's native support for async is limited. Nitro's Flask adapter uses `asyncio.run()` to execute async methods, which works but may not be as efficient as FastAPI's native async support for high-concurrency scenarios.

## Error Handling

Flask adapter provides consistent error responses:

### 404 - Entity Not Found

```python
GET /counter/nonexistent/value

# Response (404)
{
    "detail": "Counter with id 'nonexistent' not found"
}
```

### 422 - Validation Error

```python
POST /product/p1/update
{"price": "not_a_number"}

# Response (422)
{
    "detail": "Validation error: price must be a float"
}
```

### 500 - Internal Server Error

```python
@action()
def risky_operation(self):
    raise ValueError("Something went wrong")

POST /product/p1/risky_operation

# Response (500)
{
    "detail": "Something went wrong"
}
```

## Mixing Flask Routes and Nitro Actions

You can freely mix traditional Flask routes with Nitro auto-routes:

```python
from flask import Flask, render_template, request
from nitro.adapters.flask import configure_nitro
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.routing import action

app = Flask(__name__)

# --- Traditional Flask Routes ---

@app.route("/")
def index():
    """Homepage with template."""
    products = Product.all()
    return render_template("index.html", products=products)

@app.route("/about")
def about():
    """About page."""
    return render_template("about.html")

# --- Nitro Auto-Routes ---

class Product(Entity, table=True):
    name: str
    price: float
    stock: int = 0

    @action(method="POST")
    def restock(self, quantity: int):
        """Restock product (auto-route)."""
        self.stock += quantity
        self.save()
        return {
            "id": self.id,
            "name": self.name,
            "stock": self.stock
        }

    @action(method="GET")
    @classmethod
    def in_stock(cls):
        """Get all products in stock (auto-route)."""
        return [
            p.model_dump()
            for p in cls.all()
            if p.stock > 0
        ]

# Configure Nitro
configure_nitro(app, prefix="/api")

if __name__ == "__main__":
    app.run(debug=True)
```

**Routes:**
- `GET /` - Flask route (HTML)
- `GET /about` - Flask route (HTML)
- `POST /api/product/{id}/restock` - Nitro auto-route (JSON)
- `GET /api/product/in_stock` - Nitro auto-route (JSON)

## Using with Flask Blueprints

Nitro works alongside Flask blueprints:

```python
from flask import Flask, Blueprint
from nitro.adapters.flask import configure_nitro

# Create blueprint for admin routes
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
def dashboard():
    return {"message": "Admin Dashboard"}

# Create Flask app
app = Flask(__name__)
app.register_blueprint(admin_bp)

# Configure Nitro (separate from blueprints)
configure_nitro(app, prefix="/api")

# Routes:
# GET /admin/dashboard - Blueprint route
# POST /api/product/{id}/update - Nitro auto-route
```

## Complete Example

A complete Flask + Nitro application:

```python
from flask import Flask, jsonify, render_template_string
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.adapters.flask import configure_nitro
from nitro.infrastructure.routing import action

# --- Entities ---

class Task(Entity, table=True):
    title: str
    completed: bool = False
    priority: int = 0

    @action(method="POST")
    def complete(self):
        """Mark task as completed."""
        self.completed = True
        self.save()
        return self.model_dump()

    @action(method="POST")
    def set_priority(self, priority: int):
        """Update task priority."""
        if priority < 0 or priority > 10:
            raise ValueError("Priority must be between 0 and 10")
        self.priority = priority
        self.save()
        return self.model_dump()

    @action(method="GET")
    @classmethod
    def high_priority(cls, min_priority: int = 7):
        """Get high-priority tasks."""
        tasks = cls.all()
        return [
            t.model_dump()
            for t in tasks
            if t.priority >= min_priority and not t.completed
        ]

    @action(method="POST")
    @classmethod
    def create_task(cls, title: str, priority: int = 0):
        """Create a new task."""
        task = cls(title=title, priority=priority)
        task.save()
        return task.model_dump()

# --- Flask Application ---

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Initialize database
repo = SQLModelRepository()
repo.init_db()

# Traditional Flask routes
@app.route("/")
def index():
    """Simple HTML homepage."""
    html = """
    <h1>Task Manager API</h1>
    <p>API endpoints:</p>
    <ul>
        <li>POST /api/task/create_task - Create new task</li>
        <li>POST /api/task/{id}/complete - Mark task complete</li>
        <li>POST /api/task/{id}/set_priority - Set task priority</li>
        <li>GET /api/task/high_priority - Get high-priority tasks</li>
    </ul>
    """
    return render_template_string(html)

@app.route("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}

# Configure Nitro auto-routing
configure_nitro(app, prefix="/api")

if __name__ == "__main__":
    # Create some sample data
    if not Task.all():
        Task(title="Fix critical bug", priority=10).save()
        Task(title="Write documentation", priority=5).save()
        Task(title="Review PR", priority=8).save()

    app.run(debug=True, host="0.0.0.0", port=5000)
```

**Generated Routes:**
- `POST /api/task/create_task`
- `POST /api/task/{id}/complete`
- `POST /api/task/{id}/set_priority`
- `GET /api/task/high_priority`

## Testing

Test your Flask + Nitro application using Flask's test client:

```python
import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_create_task(client):
    response = client.post(
        "/api/task/create_task",
        json={"title": "Test task", "priority": 5}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Test task"
    assert data["priority"] == 5

def test_complete_task(client):
    # Create task first
    create_response = client.post(
        "/api/task/create_task",
        json={"title": "Test task"}
    )
    task_id = create_response.get_json()["id"]

    # Complete the task
    response = client.post(f"/api/task/{task_id}/complete")
    assert response.status_code == 200
    data = response.get_json()
    assert data["completed"] is True
```

## Flask vs FastAPI

| Feature | Flask | FastAPI |
|---------|-------|---------|
| Async support | Via `asyncio.run()` | Native async |
| OpenAPI docs | Not included | Auto-generated |
| Parameter validation | Manual | Automatic via Pydantic |
| Performance | Good for sync workloads | Better for high concurrency |
| Maturity | Very mature | Modern, growing |

**Use Flask when:**
- You prefer Flask's simplicity and ecosystem
- Your app is primarily synchronous
- You don't need auto-generated API documentation

**Use FastAPI when:**
- You need high-performance async endpoints
- You want automatic OpenAPI documentation
- You prefer strong typing and validation

Both work seamlessly with Nitro entities!

## Next Steps

- **[Framework Overview](./overview.md)** - Framework-agnostic design
- **[Entity Active Record](../entity/active-record.md)** - Entity methods
- **[Backend Events](../events/backend-events.md)** - Event-driven patterns

## Related Frameworks

- **[FastAPI Integration](./fastapi.md)** - For async APIs with OpenAPI
- **[FastHTML Integration](./fasthtml.md)** - For HTML-first applications
- **[Starlette Integration](./starlette.md)** - SSE event helpers
