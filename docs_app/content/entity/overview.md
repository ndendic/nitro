---
title: Entity Overview
category: Entity
order: 1
---

# Entity Overview

Entities are the core abstraction in Nitro Framework. They combine data validation, business logic, and persistence in a single, cohesive class.

## Philosophy

In Nitro, **entities are where your business logic lives**. Instead of scattering logic across service layers, controllers, and models, you consolidate everything into rich domain objects that know how to save, validate, and manage themselves.

### Key Principles

1. **Business logic belongs in entities** - Methods on your entity classes encapsulate domain rules
2. **Automatic persistence** - Entities know how to save, load, and delete themselves
3. **Built-in validation** - Powered by Pydantic for robust type checking
4. **SQL-backed by default** - Uses SQLModel for seamless database integration

## Basic Entity Example

```python
from nitro.domain.entities.base_entity import Entity

class Order(Entity, table=True):
    customer_name: str
    total: float = 0.0
    status: str = "draft"

    def add_item(self, price: float):
        """Business logic lives in entity methods."""
        self.total += price
        self.save()

    def place_order(self):
        if self.total == 0:
            raise ValueError("Cannot place empty order")
        self.status = "placed"
        self.save()
```

This simple example demonstrates:
- **Data validation** - `customer_name` is required, `total` defaults to 0.0
- **Business methods** - `add_item()` and `place_order()` encapsulate domain logic
- **Automatic persistence** - `save()` method persists changes to the database

## Entity Base Class

The `Entity` class extends `SQLModel`, which means you get:

- **SQLAlchemy** - Full ORM capabilities for database operations
- **Pydantic** - Automatic validation and serialization
- **Type safety** - Python type hints enforced at runtime

**Source:** `nitro/domain/entities/base_entity.py:21-128`

## Table Configuration

Use `table=True` to create a database-backed entity:

```python
from nitro.domain.entities.base_entity import Entity

# This will create a database table
class Product(Entity, table=True):
    name: str
    price: float
    stock: int = 0
```

When you use `table=True`, Nitro will:
1. Create a database table matching your entity fields
2. Use SQLModel's ORM capabilities for queries
3. Provide all Active Record methods (`save()`, `get()`, `all()`, etc.)

## Primary Key

All entities must have an `id` field of type `str`. This is defined in the base `Entity` class:

```python
class Entity(SQLModel):
    id: str = Field(primary_key=True)
    # ... other methods
```

You can set the `id` when creating entities, or generate it automatically:

```python
import uuid

# Manual ID
product = Product(id="prod-123", name="Widget", price=9.99)

# Auto-generated ID
product = Product(id=str(uuid.uuid4()), name="Widget", price=9.99)
```

## Signals Property

Entities automatically provide a `signals` property for reactive UI integration with Datastar:

```python
from nitro.domain.entities.base_entity import Entity

class Counter(Entity, table=True):
    count: int = 0

# Access signals
counter = Counter(id="c1", count=5)
signals = counter.signals  # Returns Signals(count=5)
```

This enables seamless integration with frontend reactivity. See the [Datastar documentation](/frontend/datastar/signals.md) for more details.

## Repository Pattern

Entities use a singleton `SQLModelRepository` by default, which means:

- All entities share the same database connection
- The repository is automatically configured from `NITRO_DB_URL` environment variable
- Default database is `sqlite:///nitro.db`

```python
# All entities use the same repository
repo = Product.repository()  # SQLModelRepository singleton
same_repo = Order.repository()  # Same instance
```

See [Repository Patterns](/entity/repository-patterns.md) for details on swapping backends.

## Database Initialization

Before using entities, you must initialize the database to create tables:

```python
from nitro.domain.entities.base_entity import Entity

class Todo(Entity, table=True):
    title: str
    completed: bool = False

# Create database tables
Todo.repository().init_db()

# Now you can use the entity
todo = Todo(id="1", title="Buy milk")
todo.save()
```

## Quick Example: Complete Todo App

Here's a minimal but complete example showing entity-centric design:

```python
from nitro.domain.entities.base_entity import Entity

class Todo(Entity, table=True):
    title: str
    completed: bool = False

    def toggle(self):
        """Business logic: toggle completion status."""
        self.completed = not self.completed
        self.save()

    def mark_complete(self):
        """Business logic: mark as complete."""
        self.completed = True
        self.save()

# Initialize database
Todo.repository().init_db()

# Create a todo
todo = Todo(id="1", title="Write documentation")
todo.save()

# Use business methods
todo.toggle()  # Now completed=True
todo.toggle()  # Back to completed=False
todo.mark_complete()  # Completed=True again

# Query todos
all_todos = Todo.all()
completed = [t for t in all_todos if t.completed]
```

## Next Steps

- **[Active Record Patterns](/entity/active-record.md)** - Learn all entity methods: `save()`, `get()`, `all()`, `where()`, `filter()`, `search()`
- **[Repository Patterns](/entity/repository-patterns.md)** - Configure persistence backends and swap between SQL and memory storage

## Related Documentation

- [Events System](/events/overview.md) - Emit domain events from entity methods
- [Framework Integration](/frameworks/overview.md) - Use entities with FastAPI, Flask, or other frameworks
