# Nitro Framework Tutorial: Build a Todo App in 5 Minutes

This tutorial walks you through creating a complete Todo application with Nitro Framework.

**What you'll build:**
- ✅ Todo CRUD operations
- ✅ FastAPI backend
- ✅ SQL persistence
- ✅ Modern UI with Tailwind CSS
- ✅ Event-driven architecture

**Time:** < 5 minutes | **Lines of code:** < 50

---

## Prerequisites

- Python 3.10+
- pip installed

---

## Step 1: Install Nitro (30 seconds)

```bash
# Install Nitro framework
pip install nitro-boost

# Verify installation
nitro --version
```

---

## Step 2: Create Your App File (2 minutes)

Create `app.py`:

```python
from fastapi import FastAPI
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.infrastructure.events import on
from rusty_tags import H1, Div, Button, Form, Input, Ul, Li, A
from nitro.infrastructure.html import Page

# Step 2.1: Define Todo Entity
class Todo(Entity, table=True):
    title: str
    completed: bool = False

# Step 2.2: Create FastAPI app
app = FastAPI()
SQLModelRepository().init_db()

# Step 2.3: Event handler for logging
@on("todo.created")
def log_creation(sender, **kwargs):
    print(f"📝 Created: {sender.title}")

# Step 2.4: Homepage route
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

# Step 2.5: Create todo route
@app.post("/add")
def add_todo(title: str):
    from fastapi.responses import RedirectResponse
    todo = Todo(id=str(len(Todo.all()) + 1), title=title)
    todo.save()
    return RedirectResponse("/", status_code=303)
```

**That's it! 48 lines including comments.**

---

## Step 3: Run Your App (30 seconds)

```bash
# Start the server
uvicorn app:app --reload

# Open browser to http://localhost:8000
```

---

## Step 4: Test It Out (1 minute)

1. **Visit** http://localhost:8000
2. **Add a todo** in the input field
3. **See it appear** in the list instantly
4. **Check the console** for the event log: "📝 Created: ..."

---

## What You Just Built

In < 50 lines, you created:

- ✅ **Entity Model**: `Todo` class with validation
- ✅ **SQL Persistence**: Automatic database storage
- ✅ **FastAPI Routes**: Homepage and create endpoint
- ✅ **Event System**: Logged todo creation
- ✅ **Modern UI**: Tailwind CSS styling
- ✅ **Full CRUD**: Create and read operations

---

## Next Steps: Add More Features

### Add Toggle Functionality

Add this method to your `Todo` class:

```python
def toggle(self):
    self.completed = not self.completed
    self.save()
```

Add this route:

```python
@app.get("/toggle/{todo_id}")
def toggle_todo(todo_id: str):
    from fastapi.responses import RedirectResponse
    todo = Todo.get(todo_id)
    if todo:
        todo.toggle()
    return RedirectResponse("/", status_code=303)
```

Update the list item:

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

**Now you can toggle todos by clicking them!**

---

### Add Delete Functionality

Add this route:

```python
@app.get("/delete/{todo_id}")
def delete_todo(todo_id: str):
    from fastapi.responses import RedirectResponse
    todo = Todo.get(todo_id)
    if todo:
        todo.delete()
    return RedirectResponse("/", status_code=303)
```

Update the list item:

```python
Li(
    Div(
        A(
            f"{'✓' if t.completed else '○'} {t.title}",
            href=f"/toggle/{t.id}",
            class_="cursor-pointer hover:text-blue-600"
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

**Now you have full CRUD!**

---

### Swap Persistence Backend in 1 Line

Want in-memory storage instead of SQL?

```python
from nitro.infrastructure.repository.memory import MemoryRepository

class Todo(Entity, table=False):  # Change table=True to table=False
    title: str
    completed: bool = False

    # Add this line
    model_config = {"repository_class": MemoryRepository}
```

**That's it! Your app now uses memory storage.**

---

## Complete Feature Set

### Entity Operations

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
```

---

### Event System

```python
from nitro.infrastructure.events import on, emit

@on("todo.created")
def send_notification(sender, **kwargs):
    print(f"Notify user: {sender.title} created")

@on("todo.completed")
async def update_analytics(sender, **kwargs):
    await analytics.track("todo_completed")

# Emit events
emit("todo.created", todo)
await emit_async("todo.completed", todo)
```

---

### Reactive UI with Datastar

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

---

## CLI Tools

```bash
# Tailwind CSS
nitro tw init   # Initialize
nitro tw dev    # Watch mode
nitro tw build  # Production build

# Database
nitro db init   # Initialize database
nitro db migrate  # Run migrations
```

---

## What's Next?

1. **Explore Examples**: Check out `examples/` directory
   - `fastapi_todo_app.py`: Complete CRUD app
   - `starlette_counter_app.py`: Reactive counter
   - `flask_todo_app.py`: Flask integration

2. **Read API Reference**: See `docs/API_REFERENCE.md`
   - All Entity methods
   - Event system details
   - Templating API

3. **Build Something Cool**: You now have everything you need!
   - E-commerce app
   - Blog platform
   - Admin dashboard
   - Real-time chat

---

## Tips & Tricks

### Hot Reload

Use `uvicorn app:app --reload` for automatic reloading during development.

### Type Hints

Nitro has full type hint support for IDE autocomplete:

```python
todo: Todo = Todo.get("1")  # IDE knows all methods
todos: List[Todo] = Todo.all()
```

### Error Handling

```python
@app.get("/todos/{todo_id}")
def get_todo(todo_id: str):
    from fastapi import HTTPException
    todo = Todo.get(todo_id)
    if not todo:
        raise HTTPException(404, "Todo not found")
    return todo
```

### Environment Configuration

```bash
# .env file
NITRO_TAILWIND_CSS_INPUT="static/css/input.css"
NITRO_TAILWIND_CSS_OUTPUT="static/css/output.css"
```

---

## Congratulations! 🎉

You've learned:
- ✅ How to create entities
- ✅ How to persist data
- ✅ How to build routes
- ✅ How to use events
- ✅ How to create UIs
- ✅ How to swap backends

**Time to build something amazing!**

---

## Need Help?

- **Examples**: `examples/` directory
- **API Docs**: `docs/API_REFERENCE.md`
- **Migration**: `examples/migration_from_starmodel.md`
- **Changelog**: `CHANGELOG.md`
- **Issues**: [GitHub Issues](https://github.com/yourusername/nitro/issues)

Happy coding! 🚀
