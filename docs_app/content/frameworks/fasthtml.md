# FastHTML Integration

Nitro integrates seamlessly with FastHTML, providing auto-routing for entity methods alongside FastHTML's traditional routing. This is ideal for building reactive, HTML-first applications with RustyTags and Datastar.

## Quick Start

```python
from fasthtml.common import *
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.adapters.fasthtml import configure_nitro
from nitro.infrastructure.routing import action
from rusty_tags import Div, H1, Button, Form, Input, Ul, Li

# Define entity with actions
class Todo(Entity, table=True):
    title: str
    completed: bool = False

    @action(method="POST")
    def toggle(self):
        """Toggle todo completion status."""
        self.completed = not self.completed
        self.save()
        return todo_item(self)

    @action(method="DELETE")
    def remove(self):
        """Delete this todo item."""
        self.delete()
        return ""

# Create FastHTML app
app, rt = fast_app()

# Initialize database
SQLModelRepository().init_db()

# UI Components
def todo_item(todo):
    """Render a single todo item."""
    return Li(
        f"{'✓' if todo.completed else '○'} {todo.title}",
        Button(
            "Toggle",
            hx_post=f"/todo/{todo.id}/toggle",
            hx_swap="outerHTML",
            hx_target="closest li"
        ),
        Button(
            "Delete",
            hx_delete=f"/todo/{todo.id}/remove",
            hx_swap="outerHTML",
            hx_target="closest li"
        ),
        id=f"todo-{todo.id}",
        cls="completed" if todo.completed else ""
    )

# Traditional FastHTML route
@rt("/")
def homepage():
    todos = Todo.all()
    return Div(
        H1("Todo App"),
        Form(
            Input(name="title", placeholder="New todo..."),
            Button("Add", type="submit"),
            hx_post="/add-todo",
            hx_target="#todo-list",
            hx_swap="beforeend"
        ),
        Ul(*[todo_item(t) for t in todos], id="todo-list")
    )

@rt("/add-todo")
def add_todo(title: str):
    todo = Todo(title=title)
    todo.save()
    return todo_item(todo)

# Auto-register entity action routes
configure_nitro(rt)

serve()
```

**Generated Routes:**
- `POST /todo/{id}/toggle` - Toggle completion (Nitro auto-route)
- `DELETE /todo/{id}/remove` - Delete todo (Nitro auto-route)
- `GET /` - Homepage (FastHTML route)
- `POST /add-todo` - Add new todo (FastHTML route)

## configure_nitro() API

**Source:** `nitro/adapters/fasthtml.py:167-204`

```python
def configure_nitro(
    rt,  # FastHTML route decorator from fast_app()
    entities: Optional[List[Type[Entity]]] = None,
    prefix: str = "",
    auto_discover: bool = True
) -> FastHTMLDispatcher:
    """
    Configure Nitro auto-routing for FastHTML application.

    Args:
        rt: FastHTML route decorator (from fast_app())
        entities: Specific entities to register (None = all entities)
        prefix: URL prefix for all routes (e.g., "/api")
        auto_discover: Auto-discover all Entity subclasses (default: True)

    Returns:
        FastHTMLDispatcher instance

    Example:
        >>> app, rt = fast_app()
        >>> configure_nitro(rt)
    """
```

### Basic Usage

```python
from fasthtml.common import *
from nitro.adapters.fasthtml import configure_nitro

app, rt = fast_app()
configure_nitro(rt)  # Auto-discovers and registers all entities
```

### With URL Prefix

```python
# Entity routes will start with /api
configure_nitro(rt, prefix="/api")

# Todo.toggle() → POST /api/todo/{id}/toggle
```

### Manual Entity Registration

```python
from myapp.models import Todo, Note

configure_nitro(
    rt,
    entities=[Todo, Note],
    auto_discover=False
)
```

## FastHTMLDispatcher Class

**Source:** `nitro/adapters/fasthtml.py:42-165`

The `FastHTMLDispatcher` integrates Nitro's entity actions with FastHTML's routing system:

```python
from nitro.adapters.fasthtml import FastHTMLDispatcher

dispatcher = FastHTMLDispatcher(rt, prefix="/api")
dispatcher.configure(
    entity_base_class=Entity,
    auto_discover=True
)
```

### Features

- ✅ Automatic route registration using FastHTML's `@rt` decorator
- ✅ Path, query, and body parameter extraction
- ✅ Full async/await support
- ✅ Returns RustyTags elements or JSON
- ✅ HTMX-compatible responses
- ✅ Consistent error handling

## Using RustyTags with Entities

Nitro's entity actions can return RustyTags HTML elements for HTMX swap operations:

```python
from rusty_tags import Div, Span, Button
from nitro.infrastructure.routing import action

class Counter(Entity, table=True):
    count: int = 0

    @action(method="POST")
    def increment(self):
        """Increment counter and return updated UI."""
        self.count += 1
        self.save()
        # Return RustyTags element for HTMX swap
        return Div(
            Span(f"Count: {self.count}"),
            Button("-", hx_post=f"/counter/{self.id}/decrement"),
            Button("+", hx_post=f"/counter/{self.id}/increment"),
            id=f"counter-{self.id}"
        )

    @action(method="POST")
    def decrement(self):
        """Decrement counter and return updated UI."""
        self.count -= 1
        self.save()
        return Div(
            Span(f"Count: {self.count}"),
            Button("-", hx_post=f"/counter/{self.id}/decrement"),
            Button("+", hx_post=f"/counter/{self.id}/increment"),
            id=f"counter-{self.id}"
        )
```

HTML template:
```html
<div hx-get="/counter/c1/increment" hx-trigger="load">
    Loading...
</div>
```

## Datastar Integration

Nitro entities work seamlessly with Datastar for reactive interfaces:

```python
from rusty_tags import Div, Button
from rusty_tags.datastar import Signals
from nitro.infrastructure.routing import action

class Product(Entity, table=True):
    name: str
    price: float
    stock: int = 0

    @action(method="POST")
    def purchase(self, quantity: int = 1):
        """Purchase product and return updated stock."""
        if self.stock < quantity:
            raise ValueError(f"Only {self.stock} items in stock")

        self.stock -= quantity
        self.save()

        # Return Datastar signal update
        sigs = Signals(
            stock=self.stock,
            message=f"Purchased {quantity} item(s)"
        )
        return Div(
            f"Stock: {self.stock}",
            signals=sigs,
            id=f"product-{self.id}-stock"
        )
```

See [Datastar Documentation](../frontend/datastar/philosophy.md) for more details.

## Mixing FastHTML Routes and Nitro Actions

You can freely mix traditional FastHTML routes with Nitro auto-routes:

```python
from fasthtml.common import *
from nitro.adapters.fasthtml import configure_nitro
from rusty_tags import Div, H1, Ul, Li, A

app, rt = fast_app()

# --- Traditional FastHTML Routes ---

@rt("/")
def index():
    """Homepage with navigation."""
    return Div(
        H1("My App"),
        Ul(
            Li(A("Products", href="/products")),
            Li(A("Customers", href="/customers"))
        )
    )

@rt("/products")
def products_page():
    """Product listing page."""
    products = Product.all()
    return Div(
        H1("Products"),
        Ul(*[
            Li(f"{p.name} - ${p.price}", id=f"product-{p.id}")
            for p in products
        ])
    )

# --- Nitro Auto-Routes ---

class Product(Entity, table=True):
    name: str
    price: float

    @action(method="PUT")
    def update_price(self, price: float):
        """Update product price (auto-route)."""
        self.price = price
        self.save()
        return Li(f"{self.name} - ${self.price}", id=f"product-{self.id}")

# Configure Nitro
configure_nitro(rt)

serve()
```

**Routes:**
- `GET /` - FastHTML route
- `GET /products` - FastHTML route
- `PUT /product/{id}/update_price` - Nitro auto-route

## Parameter Handling

### Path Parameters

Entity ID is automatically extracted:

```python
@action(method="GET")
def details(self):
    # 'self' is the loaded entity instance
    return Div(f"{self.name}: {self.description}")

# GET /product/p1/details
# → Loads Product with id="p1"
```

### Query Parameters

```python
@action(method="GET")
def search_related(self, category: str, limit: int = 5):
    # Extract from query string
    results = self.related_products(category)[:limit]
    return Ul(*[Li(p.name) for p in results])

# GET /product/p1/search_related?category=electronics&limit=3
```

### Body Parameters

```python
from pydantic import BaseModel

class PriceUpdate(BaseModel):
    new_price: float
    reason: str

@action(method="POST")
def adjust_price(self, update: PriceUpdate):
    # Extract from JSON body
    self.price = update.new_price
    self.save()
    return {"price": self.price, "reason": update.reason}

# POST /product/p1/adjust_price
# Body: {"new_price": 19.99, "reason": "Sale"}
```

## Error Handling

### 404 - Entity Not Found

```python
GET /todo/nonexistent/toggle

# Response (404)
{
    "detail": "Todo with id 'nonexistent' not found"
}
```

### 422 - Validation Error

```python
POST /product/p1/update_price
{"price": "invalid"}

# Response (422)
{
    "detail": "Validation error: price must be a float"
}
```

### 500 - Internal Server Error

```python
@action()
def risky_action(self):
    raise ValueError("Something went wrong")

POST /product/p1/risky_action

# Response (500)
{
    "detail": "Something went wrong"
}
```

## Complete Example

A complete FastHTML + Nitro application with HTMX interactivity:

```python
from fasthtml.common import *
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.adapters.fasthtml import configure_nitro
from nitro.infrastructure.routing import action
from rusty_tags import Div, H1, H2, Button, Form, Input, Ul, Li, Span

# --- Entities ---

class Note(Entity, table=True):
    content: str
    pinned: bool = False

    @action(method="POST")
    def toggle_pin(self):
        self.pinned = not self.pinned
        self.save()
        return note_card(self)

    @action(method="PUT")
    def update_content(self, content: str):
        self.content = content
        self.save()
        return note_card(self)

    @action(method="DELETE")
    def remove(self):
        self.delete()
        return ""

# --- UI Components ---

def note_card(note):
    pin_icon = "📌" if note.pinned else "○"
    return Div(
        Div(
            Span(pin_icon),
            Button(
                "Pin" if not note.pinned else "Unpin",
                hx_post=f"/note/{note.id}/toggle_pin",
                hx_swap="outerHTML",
                hx_target="closest .note-card"
            ),
            Button(
                "Delete",
                hx_delete=f"/note/{note.id}/remove",
                hx_swap="outerHTML",
                hx_target="closest .note-card"
            ),
            cls="note-header"
        ),
        Div(note.content, cls="note-content"),
        id=f"note-{note.id}",
        cls="note-card pinned" if note.pinned else "note-card"
    )

# --- FastHTML App ---

app, rt = fast_app()
repo = SQLModelRepository()
repo.init_db()

@rt("/")
def index():
    notes = Note.all()
    return Div(
        H1("Notes App"),
        Form(
            Input(name="content", placeholder="New note..."),
            Button("Add", type="submit"),
            hx_post="/add-note",
            hx_target="#notes-list",
            hx_swap="afterbegin"
        ),
        H2("Pinned Notes"),
        Div(
            *[note_card(n) for n in notes if n.pinned],
            id="pinned-notes"
        ),
        H2("All Notes"),
        Div(
            *[note_card(n) for n in notes if not n.pinned],
            id="notes-list"
        )
    )

@rt("/add-note")
def add_note(content: str):
    note = Note(content=content)
    note.save()
    return note_card(note)

configure_nitro(rt)
serve()
```

## Next Steps

- **[Framework Overview](./overview.md)** - Framework-agnostic design
- **[RustyTags Overview](../frontend/rustytags/overview.md)** - HTML generation
- **[Datastar Philosophy](../frontend/datastar/philosophy.md)** - Reactive components

## Related Frameworks

- **[FastAPI Integration](./fastapi.md)** - For JSON APIs
- **[Flask Integration](./flask.md)** - Traditional web framework
- **[Starlette Integration](./starlette.md)** - SSE event helpers
