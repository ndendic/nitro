# Quickstart: Build a Todo App

Build a complete Todo application with Nitro Framework in 5 minutes.

**What you'll build:**
- Todo CRUD operations
- FastAPI backend
- SQL persistence
- Modern UI with Tailwind CSS
- Event-driven logging

**Time:** 5 minutes | **Lines of code:** < 50

## Prerequisites

Before starting, ensure you have:

- Python 3.10 or higher
- pip installed
- [Nitro installed](installation.md) - Run `pip install nitro-boost`

## Step 1: Create Your App File

Create a file called `app.py` with the following code:

```python
from fastapi import FastAPI
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.infrastructure.events import on
from rusty_tags import H1, Div, Button, Form, Input, Ul, Li, A
from nitro.infrastructure.html import Page

# Define Todo Entity
class Todo(Entity, table=True):
    title: str
    completed: bool = False

# Create FastAPI app
app = FastAPI()
SQLModelRepository().init_db()

# Event handler for logging
@on("todo.created")
def log_creation(sender, **kwargs):
    print(f"📝 Created: {sender.title}")

# Homepage route
@app.get("/")
def homepage():
    todos = Todo.all()

    page = Page(
        H1("Nitro Todo App", class_="text-4xl font-bold text-blue-600 mb-6"),

        # Add todo form
        Form(
            Input(
                type="text",
                name="title",
                placeholder="What needs to be done?",
                class_="border rounded px-4 py-2 mr-2 flex-1"
            ),
            Button(
                "Add",
                type="submit",
                class_="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-700"
            ),
            method="POST",
            action="/add",
            class_="flex mb-6"
        ),

        # Todo list
        Ul(*[
            Li(
                f"{'✓' if t.completed else '○'} {t.title}",
                class_="mb-2"
            )
            for t in todos
        ] if todos else [Li("No todos yet!", class_="text-gray-500")]),

        title="Todo App",
        tailwind4=True,  # Include Tailwind CSS
        class_="container mx-auto p-8 max-w-2xl"
    )

    return str(page)

# Create todo route
@app.post("/add")
def add_todo(title: str):
    from fastapi.responses import RedirectResponse
    todo = Todo(id=str(len(Todo.all()) + 1), title=title)
    todo.save()
    return RedirectResponse("/", status_code=303)
```

**That's it! Just 48 lines including comments.**

## Step 2: Run Your App

Start the development server:

```bash
uvicorn app:app --reload
```

You should see output like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 3: Test It Out

1. **Open your browser** to http://localhost:8000
2. **Add a todo** by typing in the input field and clicking "Add"
3. **See it appear** in the list instantly
4. **Check the console** for the event log: `📝 Created: ...`

Congratulations! You now have a working todo application.

## What You Just Built

In under 50 lines, you created:

- **Entity Model** - `Todo` class with automatic validation via Pydantic
- **SQL Persistence** - Automatic database storage with SQLModel
- **FastAPI Routes** - Homepage (GET /) and create endpoint (POST /add)
- **Event System** - Logged todo creation with a domain event
- **Modern UI** - Tailwind CSS styling with responsive design
- **CRUD Operations** - Create and read functionality

## Understanding the Code

Let's break down the key concepts:

### Entity Definition

```python
class Todo(Entity, table=True):
    title: str
    completed: bool = False
```

- Inherits from `Entity` base class
- `table=True` makes it a SQL entity (creates a database table)
- Pydantic fields provide automatic validation
- Gets CRUD methods automatically: `save()`, `get()`, `delete()`, `all()`

See: [Entity Overview](../entity/overview.md) | [Active Record Patterns](../entity/active-record.md)

### Event Handler

```python
@on("todo.created")
def log_creation(sender, **kwargs):
    print(f"📝 Created: {sender.title}")
```

- Uses Blinker for event handling
- Decorates a function to listen for `"todo.created"` events
- Automatically called when the event is emitted
- `sender` is the Todo instance

See: [Backend Events](../events/backend-events.md)

### HTML Generation

```python
page = Page(
    H1("Nitro Todo App"),
    Form(...),
    title="Todo App",
    tailwind4=True
)
```

- Uses RustyTags for high-performance HTML generation (3-10x faster than Python)
- `Page()` creates a complete HTML document
- `tailwind4=True` includes Tailwind CSS v4 CDN
- Returns a string with `str(page)`

See: [RustyTags Usage](../frontend/rustytags/usage.md)

## Next Steps: Add More Features

### Add Toggle Functionality

Make todos clickable to toggle their completion status.

**1. Add a toggle method to your `Todo` class:**

```python
class Todo(Entity, table=True):
    title: str
    completed: bool = False

    def toggle(self):
        self.completed = not self.completed
        self.save()
```

**2. Add a route for toggling:**

```python
@app.get("/toggle/{todo_id}")
def toggle_todo(todo_id: str):
    from fastapi.responses import RedirectResponse
    todo = Todo.get(todo_id)
    if todo:
        todo.toggle()
    return RedirectResponse("/", status_code=303)
```

**3. Update the list item to be clickable:**

```python
Li(
    A(
        f"{'✓' if t.completed else '○'} {t.title}",
        href=f"/toggle/{t.id}",
        class_="cursor-pointer hover:text-blue-600"
    ),
    class_="mb-2"
)
```

Now you can toggle todos by clicking them!

### Add Delete Functionality

Allow users to delete todos.

**1. Add a delete route:**

```python
@app.get("/delete/{todo_id}")
def delete_todo(todo_id: str):
    from fastapi.responses import RedirectResponse
    todo = Todo.get(todo_id)
    if todo:
        todo.delete()
    return RedirectResponse("/", status_code=303)
```

**2. Update the list item with a delete button:**

```python
Li(
    Div(
        A(
            f"{'✓' if t.completed else '○'} {t.title}",
            href=f"/toggle/{t.id}",
            class_="cursor-pointer hover:text-blue-600 flex-1"
        ),
        A(
            "Delete",
            href=f"/delete/{t.id}",
            class_="text-red-500 ml-4 hover:text-red-700"
        ),
        class_="flex justify-between"
    ),
    class_="mb-2"
)
```

Now you have full CRUD functionality!

### Swap Persistence Backend in 1 Line

Want to use in-memory storage instead of SQL? Just change the repository:

```python
from nitro.infrastructure.repository.memory import MemoryRepository

class Todo(Entity, table=False):  # Change table=True to table=False
    title: str
    completed: bool = False

    # Use memory storage
    model_config = {"repository_class": MemoryRepository}
```

That's it! Your app now uses memory storage instead of SQL. Perfect for prototyping or caching.

See: [Repository Patterns](../entity/repository-patterns.md)

## Complete Feature Overview

### Entity Operations

Nitro entities support rich querying:

```python
# Create
todo = Todo(id="1", title="Buy milk")
todo.save()

# Read
todo = Todo.get("1")
all_todos = Todo.all()
incomplete = Todo.where(Todo.completed == False)

# Update
todo.title = "Buy almond milk"
todo.save()

# Delete
todo.delete()

# Search
results = Todo.search("milk", search_fields=["title"])

# Filter
urgent_todos = Todo.filter(priority="high")
```

See: [Active Record Patterns](../entity/active-record.md)

### Event System

Events decouple side effects from business logic:

```python
from nitro.infrastructure.events import on, emit

@on("todo.created")
def send_notification(sender, **kwargs):
    print(f"Notify user: {sender.title} created")

@on("todo.completed")
async def update_analytics(sender, **kwargs):
    await analytics.track("todo_completed")

# Emit events manually
emit("todo.created", sender=todo)
await emit_async("todo.completed", sender=todo)
```

See: [Backend Events](../events/backend-events.md) | [CQRS Patterns](../events/cqrs-patterns.md)

### Reactive UI with Datastar

Add reactivity without JavaScript:

```python
from nitro.infrastructure.html.datastar import Signals

sigs = Signals(count=0)

page = Page(
    Div(
        Span(data_text="$count"),
        Button("+", data_on_click="$count++"),
        Button("-", data_on_click="$count--"),
        signals=sigs
    ),
    datastar=True
)
```

See: [Datastar Signals](../frontend/datastar/signals.md) | [Datastar Philosophy](../frontend/datastar/philosophy.md)

## CLI Tools

Nitro includes helpful CLI commands:

```bash
# Tailwind CSS
nitro tw init    # Initialize Tailwind CSS
nitro tw dev     # Watch mode for development
nitro tw build   # Production build with minification

# Database (if available)
nitro db init      # Initialize database
nitro db migrate   # Run migrations
```

See: [CLI Reference](../reference/cli.md) | [Tailwind CLI](../frontend/components/nitro-tw-cli.md)

## Tips & Tricks

### Hot Reload

Use `uvicorn app:app --reload` for automatic reloading during development. The server will restart whenever you save changes to `app.py`.

### Type Hints

Nitro has full type hint support for IDE autocomplete:

```python
from typing import List

todo: Todo = Todo.get("1")  # IDE knows all methods
todos: List[Todo] = Todo.all()
```

### Error Handling

Add proper error handling for production:

```python
from fastapi import HTTPException

@app.get("/todos/{todo_id}")
def get_todo(todo_id: str):
    todo = Todo.get(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo
```

### Environment Configuration

Use environment variables for configuration:

```bash
# .env file
NITRO_DB_URL=sqlite:///todos.db
NITRO_TAILWIND_CSS_INPUT=static/css/input.css
NITRO_TAILWIND_CSS_OUTPUT=static/css/output.css
```

See: [Installation - Configuration](installation.md#configuration)

## What's Next?

Now that you've built your first Nitro application, explore these topics:

### Core Concepts

1. **Entity System** - Learn all entity methods and patterns
   - [Entity Overview](../entity/overview.md)
   - [Active Record Patterns](../entity/active-record.md)
   - [Repository Patterns](../entity/repository-patterns.md)

2. **Event System** - Build event-driven applications
   - [Events Overview](../events/overview.md)
   - [Backend Events](../events/backend-events.md)
   - [CQRS Patterns](../events/cqrs-patterns.md)

### Framework Integration

3. **Use with Other Frameworks**
   - [FastHTML Integration](../frameworks/fasthtml.md)
   - [Flask Integration](../frameworks/flask.md)
   - [Starlette Integration](../frameworks/starlette.md)

### Frontend

4. **Build Rich UIs**
   - [RustyTags Overview](../frontend/rustytags/overview.md) - High-performance HTML
   - [Datastar Philosophy](../frontend/datastar/philosophy.md) - Reactive UI
   - [Component Styling](../frontend/components/basecoat-styling.md) - Beautiful components

### Reference

5. **API Documentation**
   - [API Reference](../reference/api.md) - Complete API docs
   - [CLI Reference](../reference/cli.md) - Command-line tools

## Example Applications

Check out these example applications for inspiration:

- **Todo App** (you just built this!)
- **Counter App** - Reactive counter with Datastar
- **Blog Platform** - Posts, comments, and search
- **E-commerce** - Products, cart, and checkout
- **Admin Dashboard** - CRUD interface with tables

## Need Help?

- **Documentation** - You're reading it! Check the sidebar for more topics
- **Examples** - Look in the `examples/` directory
- **Issues** - Report bugs on [GitHub Issues](https://github.com/yourusername/nitro/issues)

## Congratulations!

You've successfully built a complete web application with Nitro in just a few minutes. You've learned:

- How to define entities with automatic persistence
- How to create FastAPI routes
- How to use the event system
- How to generate HTML with RustyTags
- How to style with Tailwind CSS

Time to build something amazing! Start with the [Entity Overview](../entity/overview.md) to learn more about what Nitro can do.
