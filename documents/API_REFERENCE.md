# Nitro Framework - API Reference

Complete API documentation for Nitro Framework Phase 1.

---

## Table of Contents

1. [Entity API](#entity-api)
2. [Persistence API](#persistence-api)
3. [Event System API](#event-system-api)
4. [Templating API](#templating-api)
5. [CLI API](#cli-api)

---

## Entity API

### Overview

Entities are rich domain models that combine Pydantic validation with persistence capabilities. They serve as the core of your application's business logic.

### Base Entity Class

```python
from nitro.domain.entities.base_entity import Entity

class Todo(Entity, table=True):
    title: str
    completed: bool = False
```

### Core Methods

#### `Entity.save() -> bool`

Persists the entity to the configured repository.

**Returns:** `True` if save succeeded, `False` otherwise

**Example:**
```python
todo = Todo(id="1", title="Buy milk")
success = todo.save()
if success:
    print("Todo saved!")
```

---

#### `Entity.delete() -> bool`

Removes the entity from the repository.

**Returns:** `True` if deletion succeeded, `False` otherwise

**Example:**
```python
todo = Todo.get("1")
if todo:
    todo.delete()
```

---

#### `Entity.get(id: Any) -> Optional[Entity]`

Retrieves an entity by its ID.

**Parameters:**
- `id`: The entity's unique identifier

**Returns:** Entity instance or `None` if not found

**Example:**
```python
todo = Todo.get("1")
if todo:
    print(f"Found: {todo.title}")
else:
    print("Not found")
```

---

#### `Entity.exists(id: Any) -> bool`

Checks if an entity exists without retrieving it.

**Parameters:**
- `id`: The entity's unique identifier

**Returns:** `True` if entity exists, `False` otherwise

**Example:**
```python
if Todo.exists("1"):
    print("Todo exists")
```

---

#### `Entity.all() -> List[Entity]`

Retrieves all entities of this type.

**Returns:** List of all entity instances

**Example:**
```python
all_todos = Todo.all()
for todo in all_todos:
    print(f"- {todo.title}")
```

---

#### `Entity.where(*expressions, order_by=None, limit=None, offset=None) -> List[Entity]`

Queries entities with SQLAlchemy-style expressions.

**Parameters:**
- `*expressions`: SQLAlchemy filter expressions
- `order_by`: Column to order by (optional)
- `limit`: Maximum number of results (optional)
- `offset`: Number of results to skip (optional)

**Returns:** List of matching entities

**Example:**
```python
# Find incomplete todos
incomplete = Todo.where(Todo.completed == False)

# With ordering and limit
recent = Todo.where(
    Todo.completed == True,
    order_by=Todo.id.desc(),
    limit=10
)
```

---

#### `Entity.find(id: Any) -> Optional[Entity]`

Alias for `Entity.get()`. Retrieves entity by ID.

**Example:**
```python
todo = Todo.find("1")
```

---

#### `Entity.find_by(**kwargs) -> Union[List[Entity], Entity, None]`

Finds entities by field values.

**Parameters:**
- `**kwargs`: Field name and value pairs

**Returns:** Single entity, list of entities, or `None`

**Example:**
```python
# Find by title
todo = Todo.find_by(title="Buy milk")

# Find all completed todos
completed = Todo.find_by(completed=True)
```

---

#### `Entity.search(search_value: str, search_fields: List[str], ...) -> List[Entity]`

Searches entities across multiple text fields.

**Parameters:**
- `search_value`: Text to search for
- `search_fields`: List of field names to search in
- `order_by`: Column to order by (optional)
- `limit`: Maximum results (optional)

**Returns:** List of matching entities

**Example:**
```python
results = Todo.search(
    "milk",
    search_fields=["title", "description"],
    limit=10
)
```

---

#### `Entity.filter(**conditions) -> List[Entity]`

Filters entities by exact field matches.

**Parameters:**
- `**conditions`: Field names and values

**Returns:** List of matching entities

**Example:**
```python
completed_todos = Todo.filter(completed=True)
```

---

### Entity Properties

#### `entity.signals -> Signals`

Returns a `Signals` object for reactive UI integration.

**Example:**
```python
todo = Todo(id="1", title="Buy milk", completed=False)
sigs = todo.signals

# Use in templates
Div(
    Span(data_text=sigs.title),
    signals=sigs
)
```

---

### Entity Configuration

Configure entity persistence via `model_config`:

```python
from nitro.infrastructure.repository.memory import MemoryRepository
from nitro.infrastructure.repository.sql import SQLModelRepository

class Todo(Entity, table=True):
    title: str
    completed: bool = False

    # Option 1: SQL persistence (default)
    model_config = {"repository_class": SQLModelRepository}

    # Option 2: In-memory persistence
    model_config = {"repository_class": MemoryRepository}
```

---

## Persistence API

### SQLModelRepository

SQL database persistence using SQLModel and SQLAlchemy.

```python
from nitro.infrastructure.repository.sql import SQLModelRepository

# Initialize database
repo = SQLModelRepository()
repo.init_db()
```

**Methods:**
- `init_db()`: Initialize database tables
- `get(model, id)`: Get entity by ID
- `save(entity)`: Save entity
- `delete(entity)`: Delete entity
- `all(model)`: Get all entities
- `where(model, *expressions, ...)`: Query with filters

---

### MemoryRepository

In-memory persistence for testing/prototyping.

```python
from nitro.infrastructure.repository.memory import MemoryRepository

class SessionData(Entity, table=False):
    data: dict = {}
    model_config = {"repository_class": MemoryRepository}
```

**Features:**
- TTL support for auto-expiration
- Fast read/write operations
- Ephemeral data (lost on restart)

---

## Event System API

### Event Registration

#### `@on(event_name: str)`

Decorator to register event handlers.

**Example:**
```python
from nitro.infrastructure.events import on

@on("todo.created")
def log_creation(sender, **kwargs):
    print(f"Todo created: {sender.title}")

@on("todo.created")
async def send_notification(sender, **kwargs):
    await send_email(sender.user_email, "Todo created!")
```

---

### Event Emission

#### `emit(event_name: str, sender, **kwargs)`

Emit event synchronously.

**Parameters:**
- `event_name`: Name of the event
- `sender`: Object emitting the event
- `**kwargs`: Additional data

**Example:**
```python
from nitro.infrastructure.events import emit

todo = Todo(id="1", title="Buy milk")
todo.save()
emit("todo.created", todo, user_id="user123")
```

---

#### `emit_async(event_name: str, sender, **kwargs)`

Emit event asynchronously.

**Example:**
```python
from nitro.infrastructure.events import emit_async

async def create_todo(title: str):
    todo = Todo(id="1", title=title)
    todo.save()
    await emit_async("todo.created", todo)
```

---

### Event System Features

- ✅ Sync and async handlers
- ✅ Generator support (sync and async)
- ✅ Multiple handlers per event
- ✅ Wildcard event matching
- ✅ FastAPI background task integration

---

## Templating API

### Page Component

Create complete HTML documents.

```python
from nitro.infrastructure.html import Page
from rusty_tags import H1, Div, P

page = Page(
    H1("Welcome"),
    Div(
        P("Content here"),
        class_="container"
    ),
    title="My Page",
    tailwind4=True,  # Include Tailwind 4 CDN
    datastar=True,   # Include Datastar SDK
    htmx=True,       # Include HTMX
)

# Convert to HTML string
html = str(page)
```

**Parameters:**
- `*content`: HTML elements to include in body
- `title`: Page title (default: "Nitro Page")
- `tailwind4`: Include Tailwind CSS 4 (default: False)
- `datastar`: Include Datastar SDK (default: False)
- `htmx`: Include HTMX (default: False)
- `hdrs`: Additional headers (tuple of elements)

---

### Signals (Reactive State)

```python
from nitro.infrastructure.html.datastar import Signals

# Create signals
sigs = Signals(count=0, name="John")

# Use in templates
Div(
    Span(data_text="$count"),  # Reactive text
    Button(
        "Increment",
        data_on_click="$count++"  # Reactive handler
    ),
    signals=sigs
)
```

**Features:**
- Reactive updates
- Two-way data binding
- Operator overloading
- Nested object support

---

### HTML Tags

Import from `rusty_tags`:

```python
from rusty_tags import (
    # Structure
    Html, Head, Body, Div, Span, Main, Section,

    # Text
    H1, H2, H3, H4, H5, H6, P, A, Strong, Em,

    # Forms
    Form, Input, Button, Select, Option, Textarea, Label,

    # Lists
    Ul, Ol, Li,

    # Tables
    Table, Tr, Td, Th, Tbody, Thead,

    # Media
    Img, Video, Audio, Canvas,

    # SVG
    Svg, Circle, Rect, Path, Line, Polygon,

    # And many more...
)
```

---

## CLI API

### Tailwind CSS Commands

```bash
# Initialize Tailwind CSS
nitro tw init

# Development mode (watch for changes)
nitro tw dev

# Production build (minified)
nitro tw build
```

**Configuration via environment variables:**
```bash
NITRO_TAILWIND_CSS_INPUT="static/css/input.css"
NITRO_TAILWIND_CSS_OUTPUT="static/css/output.css"
NITRO_TAILWIND_CONTENT_PATHS='["**/*.py", "**/*.html"]'
```

---

### Database Commands

```bash
# Initialize database
nitro db init

# Create migration
nitro db migrations -m "Add user table"

# Run migrations
nitro db migrate
```

---

### General Commands

```bash
# Show version
nitro --version

# Show help
nitro --help

# Show command-specific help
nitro tw --help
```

---

## Complete Example

```python
from fastapi import FastAPI
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.infrastructure.events import on, emit
from rusty_tags import H1, Div, Button
from nitro.infrastructure.html import Page

# Define Entity
class Todo(Entity, table=True):
    title: str
    completed: bool = False

    def toggle(self):
        self.completed = not self.completed
        self.save()
        emit("todo.toggled", self)

# Event Handler
@on("todo.toggled")
def log_toggle(sender, **kwargs):
    print(f"Todo {sender.id} toggled to {sender.completed}")

# FastAPI App
app = FastAPI()
SQLModelRepository().init_db()

@app.get("/")
def homepage():
    todos = Todo.all()
    page = Page(
        H1("My Todos"),
        Div(*[
            Div(f"{'✓' if t.completed else '○'} {t.title}")
            for t in todos
        ]),
        title="Todo App",
        tailwind4=True
    )
    return str(page)

@app.post("/todos")
def create_todo(title: str):
    todo = Todo(id=str(len(Todo.all()) + 1), title=title)
    todo.save()
    emit("todo.created", todo)
    return todo
```

---

## Next Steps

- Read the [Tutorial](TUTORIAL.md) for step-by-step guidance
- Check out [Examples](../examples/) for complete applications
- Review [CHANGELOG.md](../CHANGELOG.md) for version history
- See [Migration Guide](../examples/migration_from_starmodel.md) for StarModel users

---

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/nitro/issues)
- Documentation: [Full Docs](https://nitro.dev)
- Examples: [`examples/`](../examples/) directory
