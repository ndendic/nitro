# FastAPI Integration

Nitro provides first-class FastAPI support with automatic route registration, OpenAPI documentation generation, and full async/await support.

## Quick Start

```python
from fastapi import FastAPI
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.adapters.fastapi import configure_nitro
from nitro.infrastructure.routing import action

# Define your entity
class Todo(Entity, table=True):
    title: str
    completed: bool = False

    @action(method="POST", summary="Mark todo as complete")
    def complete(self):
        """Mark this todo item as completed."""
        self.completed = True
        self.save()
        return self.model_dump()

    @action(method="GET", summary="Get todo status")
    def status(self):
        """Get the current status of this todo."""
        return {"id": self.id, "completed": self.completed}

    @action(method="GET", summary="List all todos")
    @classmethod
    def list_all(cls):
        """Retrieve all todo items."""
        return [t.model_dump() for t in cls.all()]

# Create FastAPI app
app = FastAPI(title="Todo API", version="1.0.0")

# Initialize database
SQLModelRepository().init_db()

# Auto-register all routes
configure_nitro(app)
```

**Generated Routes:**
- `POST /todo/{id}/complete` - Mark todo as complete
- `GET /todo/{id}/status` - Get todo status
- `GET /todo/list_all` - List all todos

Visit `/docs` to see the auto-generated OpenAPI documentation.

## configure_nitro() API

**Source:** `nitro/adapters/fastapi.py:242-279`

```python
def configure_nitro(
    app: FastAPI,
    entities: Optional[List[Type[Entity]]] = None,
    prefix: str = "",
    auto_discover: bool = True
) -> FastAPIDispatcher:
    """
    Configure Nitro auto-routing for FastAPI application.

    Args:
        app: FastAPI application instance
        entities: Specific entities to register (None = all entities)
        prefix: URL prefix for all routes (e.g., "/api/v1")
        auto_discover: Auto-discover all Entity subclasses (default: True)

    Returns:
        FastAPIDispatcher instance for advanced configuration

    Example:
        >>> app = FastAPI()
        >>> configure_nitro(app, prefix="/api/v1")
    """
```

### Basic Usage

```python
from fastapi import FastAPI
from nitro.adapters.fastapi import configure_nitro

app = FastAPI()
configure_nitro(app)  # Discovers and registers all entities
```

### With URL Prefix

```python
# All routes will start with /api/v1
configure_nitro(app, prefix="/api/v1")

# Todo.complete() → POST /api/v1/todo/{id}/complete
```

### Manual Entity Registration

```python
from myapp.models import Todo, User, Product

# Only register specific entities
configure_nitro(
    app,
    entities=[Todo, User],
    auto_discover=False
)
```

## FastAPIDispatcher Class

**Source:** `nitro/adapters/fastapi.py:43-240`

The `FastAPIDispatcher` handles the integration between Nitro's entity system and FastAPI's routing:

```python
from nitro.adapters.fastapi import FastAPIDispatcher

dispatcher = FastAPIDispatcher(app, prefix="/api")
dispatcher.configure(
    entity_base_class=Entity,
    auto_discover=True
)
```

### Features

- ✅ Automatic OpenAPI schema generation
- ✅ Path, query, and body parameter extraction
- ✅ Full async/await support
- ✅ Dependency injection compatibility
- ✅ Request/response validation
- ✅ Consistent error handling (404, 422, 500)

## OpenAPI Documentation

FastAPI's auto-generated documentation (`/docs`) includes full details for all Nitro routes.

### Customizing OpenAPI Metadata

```python
from nitro.infrastructure.routing import action

class Product(Entity, table=True):
    name: str
    price: float
    stock: int = 0

    @action(
        method="POST",
        summary="Restock product",
        description="Add inventory to product stock",
        tags=["inventory"],
        status_code=200
    )
    def restock(self, quantity: int):
        """
        Increase product stock by the specified quantity.

        This method is used by warehouse staff to update
        inventory levels after receiving shipments.
        """
        self.stock += quantity
        self.save()
        return {
            "id": self.id,
            "name": self.name,
            "stock": self.stock
        }
```

**OpenAPI Output:**
- **Summary:** "Restock product"
- **Description:** Full docstring text
- **Tags:** ["inventory"]
- **Parameters:** Automatically extracted from type hints

### Response Models

Specify a Pydantic model for response validation:

```python
from pydantic import BaseModel
from nitro.infrastructure.routing import action

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    in_stock: bool

class Product(Entity, table=True):
    name: str
    price: float
    stock: int = 0

    @action(
        method="GET",
        response_model=ProductResponse,
        summary="Get product details"
    )
    def details(self) -> ProductResponse:
        return ProductResponse(
            id=self.id,
            name=self.name,
            price=self.price,
            in_stock=self.stock > 0
        )
```

## Parameter Handling

### Path Parameters

The entity `{id}` is automatically extracted from the URL path:

```python
@action(method="GET")
def status(self):
    # 'self' is the loaded entity instance
    return {"id": self.id, "status": self.status}

# GET /order/order-123/status
# → Automatically loads Order with id="order-123"
```

### Query Parameters (GET Requests)

```python
@action(method="GET")
def search(self, query: str, limit: int = 10, active: bool = True):
    # Parameters extracted from query string
    results = self.filter(name__contains=query, active=active)
    return results[:limit]

# GET /product/p1/search?query=widget&limit=5&active=true
```

### Body Parameters (POST/PUT/PATCH)

```python
@action(method="POST")
def update(self, name: str, price: float, tags: List[str] = []):
    # Parameters extracted from JSON request body
    self.name = name
    self.price = price
    self.tags = tags
    self.save()
    return self.model_dump()

# POST /product/p1/update
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

Nitro fully supports async entity methods with FastAPI:

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
```

## Error Handling

FastAPI adapter provides consistent error responses:

### 404 - Entity Not Found

```python
GET /todo/nonexistent/status

# Response (404)
{
    "detail": "Todo with id 'nonexistent' not found"
}
```

### 422 - Validation Error

```python
POST /product/p1/update
{"price": "not_a_number"}

# Response (422)
{
    "detail": [
        {
            "loc": ["body", "price"],
            "msg": "value is not a valid float",
            "type": "type_error.float"
        }
    ]
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

## Complete Example

Here's a complete FastAPI application with multiple entities:

```python
from fastapi import FastAPI
from typing import List
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.adapters.fastapi import configure_nitro
from nitro.infrastructure.routing import action

# --- Entities ---

class Customer(Entity, table=True):
    name: str
    email: str
    active: bool = True

    @action(method="POST", summary="Create new customer")
    @classmethod
    def create(cls, name: str, email: str):
        customer = cls(name=name, email=email)
        customer.save()
        return customer.model_dump()

    @action(method="GET", summary="List all customers")
    @classmethod
    def list_all(cls, active_only: bool = True):
        customers = cls.all()
        if active_only:
            customers = [c for c in customers if c.active]
        return [c.model_dump() for c in customers]


class Order(Entity, table=True):
    customer_id: str
    total: float = 0.0
    status: str = "pending"

    @action(method="POST", summary="Place order")
    def place(self):
        if self.total == 0:
            raise ValueError("Cannot place order with zero total")
        self.status = "placed"
        self.save()
        return {"id": self.id, "status": self.status}

    @action(method="POST", summary="Cancel order")
    def cancel(self):
        if self.status == "shipped":
            raise ValueError("Cannot cancel shipped order")
        self.status = "cancelled"
        self.save()
        return {"id": self.id, "status": self.status}

    @action(method="GET", summary="Get order status")
    def get_status(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "total": self.total,
            "status": self.status
        }

# --- Application ---

app = FastAPI(
    title="E-Commerce API",
    description="Order management system built with Nitro",
    version="1.0.0"
)

# Initialize database
repo = SQLModelRepository()
repo.init_db()

# Configure Nitro routing
configure_nitro(app, prefix="/api/v1")

# Optional: Add custom routes
@app.get("/")
def root():
    return {"message": "E-Commerce API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Generated Routes:**
- `POST /api/v1/customer/create`
- `GET /api/v1/customer/list_all`
- `POST /api/v1/order/{id}/place`
- `POST /api/v1/order/{id}/cancel`
- `GET /api/v1/order/{id}/get_status`

Visit `http://localhost:8000/docs` for interactive API documentation.

## Testing

Test your FastAPI + Nitro application using FastAPI's `TestClient`:

```python
from fastapi.testclient import TestClient

def test_create_customer():
    client = TestClient(app)
    response = client.post(
        "/api/v1/customer/create",
        json={"name": "John Doe", "email": "john@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
```

## Next Steps

- **[Framework Overview](./overview.md)** - Understanding framework-agnostic design
- **[Entity Active Record](../entity/active-record.md)** - Entity methods and persistence
- **[Backend Events](../events/backend-events.md)** - Event-driven patterns

## Related Frameworks

- **[FastHTML Integration](./fasthtml.md)** - For HTML-first applications
- **[Flask Integration](./flask.md)** - Traditional Python web framework
- **[Starlette Integration](./starlette.md)** - SSE event helpers
