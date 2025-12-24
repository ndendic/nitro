---
title: Repository Patterns
category: Entity
order: 3
---

# Repository Patterns

The Repository pattern separates persistence logic from business logic. Nitro provides two built-in repositories: `SQLModelRepository` for database persistence and `MemoryRepository` for in-memory storage.

---

## Table of Contents

1. [Overview](#overview)
2. [SQLModelRepository](#sqlmodelrepository)
3. [MemoryRepository](#memoryrepository)
4. [Configuration](#configuration)
5. [Swapping Backends](#swapping-backends)

---

## Overview

### What is a Repository?

A repository is an abstraction layer between your entities and the underlying data storage. It provides a consistent API regardless of where data is actually stored (database, memory, cache, etc.).

### Why Use Repositories?

1. **Swap backends easily** - Switch from SQLite to PostgreSQL, or from database to memory, with minimal code changes
2. **Test with ease** - Use in-memory repositories for fast unit tests
3. **Separation of concerns** - Business logic doesn't need to know about database details
4. **Single responsibility** - Repositories handle *only* persistence

### Repository Interface

All repositories implement `EntityRepositoryInterface`:

**Source:** `nitro/infrastructure/repository/base.py`

```python
from abc import ABC, abstractmethod
from typing import Optional

class EntityRepositoryInterface(ABC):
    @abstractmethod
    def save(self, entity, ttl: Optional[int] = None) -> bool:
        """Save entity instance to the persistence backend."""
        pass

    @abstractmethod
    def find(self, entity_id: str) -> Optional:
        """Load entity instance from the persistence backend."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity from the persistence backend."""
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists in the persistence backend."""
        pass
```

---

## SQLModelRepository

The default repository for Nitro entities. Provides SQL database persistence using SQLModel/SQLAlchemy.

**Source:** `nitro/infrastructure/repository/sql.py`

### Features

- **Singleton pattern** - All entities share the same repository instance
- **Automatic session management** - No need to manually handle database sessions
- **Connection pooling** - Efficient database connection reuse (configurable)
- **Query methods** - `filter()`, `search()`, `where()`, bulk operations
- **Relationship loading** - Automatically eager-loads relationships to avoid detached instance errors

### Singleton Pattern

SQLModelRepository uses the singleton pattern, meaning there's only **one instance** shared across all entities:

```python
from nitro.domain.entities.base_entity import Entity

class Product(Entity, table=True):
    name: str
    price: float

class Order(Entity, table=True):
    customer_name: str
    total: float

# Both use the same repository instance
repo1 = Product.repository()
repo2 = Order.repository()
assert repo1 is repo2  # True - same object
```

### Database Configuration

The database URL is configured via the `NITRO_DB_URL` environment variable:

```bash
# Default (SQLite)
NITRO_DB_URL=sqlite:///nitro.db

# PostgreSQL
NITRO_DB_URL=postgresql://user:password@localhost/dbname

# MySQL
NITRO_DB_URL=mysql+pymysql://user:password@localhost/dbname
```

You can also configure it in your `.env` file:

```bash
# .env
NITRO_DB_URL=postgresql://user:password@localhost/nitro_production
```

### Initialization

Before using entities, you must initialize the database to create tables:

```python
from nitro.domain.entities.base_entity import Entity

class Todo(Entity, table=True):
    title: str
    completed: bool = False

# Initialize database - creates all tables
Todo.repository().init_db()

# Now you can use entities
todo = Todo(id="1", title="Buy milk")
todo.save()
```

**Method Signature:**
```python
def init_db(self) -> None:
    """Create all database tables defined by entities."""
```

**Notes:**
- Calls `SQLModel.metadata.create_all()`
- Safe to call multiple times (won't recreate existing tables)
- Uses SQLAlchemy's `extend_existing=True` configuration

### Connection Pooling

For production deployments, you can configure connection pooling:

```python
from nitro.infrastructure.repository.sql import SQLModelRepository

repo = SQLModelRepository(
    url="postgresql://user:password@localhost/dbname",
    pool_size=10,           # Number of connections to maintain
    max_overflow=20,        # Additional connections when pool is full
    pool_timeout=30.0,      # Seconds to wait for available connection
    echo=False              # Set to True to log SQL queries
)

# Initialize tables
repo.init_db()
```

**Notes:**
- Pool configuration is ignored for SQLite (uses SingletonThreadPool)
- Pool settings apply to the singleton instance
- Useful for high-traffic production environments

### Schema Inspection

View your database schema programmatically:

```python
from nitro.domain.entities.base_entity import Entity

class Product(Entity, table=True):
    name: str
    price: float

# Initialize database
Product.repository().init_db()

# Inspect schema
schema = Product.repository().schema()
print(schema)
```

**Output:**
```
Table: product
  * id: VARCHAR
  - name: VARCHAR
  - price: FLOAT
```

**Method Signature:**
```python
def schema(self) -> str:
    """Return a string representation of the database schema."""
```

---

## MemoryRepository

In-memory entity persistence for development and testing. Fast, ephemeral storage that doesn't require a database.

**Source:** `nitro/infrastructure/repository/memory.py`

### Features

- **Fast** - No database I/O, all operations in RAM
- **TTL support** - Automatic expiration of entities after a specified time
- **Singleton pattern** - Single shared instance across all entities
- **Automatic cleanup** - Removes expired entities periodically
- **Zero configuration** - No database setup required

### When to Use MemoryRepository

1. **Testing** - Fast unit tests without database dependencies
2. **Prototyping** - Quickly build features without database setup
3. **Session data** - Store temporary data like shopping carts
4. **Caching** - Short-lived data that doesn't need persistence

### Basic Usage

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository
from pydantic import ConfigDict

class Session(Entity, table=False):
    user_id: str
    cart_items: list = []

    model_config = ConfigDict(
        repository_class=MemoryRepository
    )

# No need to call init_db() for memory repository

# Use like any other entity
session = Session(id="session-123", user_id="user-456")
session.save()

# Retrieve it
retrieved = Session.get("session-123")
```

**Important:** Use `table=False` when using MemoryRepository to prevent SQLModel from trying to create a database table.

### TTL (Time-To-Live) Support

MemoryRepository supports automatic expiration of entities:

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository
from pydantic import ConfigDict

class VerificationCode(Entity, table=False):
    code: str
    email: str

    model_config = ConfigDict(
        repository_class=MemoryRepository
    )

# Save with 5-minute expiration
code = VerificationCode(id="verify-123", code="ABC123", email="user@example.com")
code.repository().save(code, ttl=300)  # 300 seconds = 5 minutes

# After 5 minutes, it will be automatically removed
# Accessing it will return None
```

**Note:** TTL is specified in seconds.

### Automatic Cleanup

MemoryRepository automatically cleans up expired entities:

```python
from nitro.infrastructure.repository.memory import MemoryRepository

# Get the singleton instance
repo = MemoryRepository()

# Cleanup runs automatically on access (lazy cleanup)
# You can also manually trigger cleanup:
expired_count = repo.cleanup_expired_sync()
print(f"Removed {expired_count} expired entities")
```

**Method Signature:**
```python
def cleanup_expired_sync(self) -> int:
    """Clean up expired entity entries. Returns count of removed entities."""
```

### Singleton Pattern

Like SQLModelRepository, MemoryRepository uses the singleton pattern:

```python
from nitro.infrastructure.repository.memory import MemoryRepository

repo1 = MemoryRepository()
repo2 = MemoryRepository()
assert repo1 is repo2  # True - same instance
```

This ensures all entities using MemoryRepository share the same data store.

---

## Configuration

### Configuring Repository for an Entity

There are two ways to configure which repository an entity uses:

#### 1. Via model_config (Recommended)

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository
from pydantic import ConfigDict

class ShoppingCart(Entity, table=False):
    items: list = []

    model_config = ConfigDict(
        repository_class=MemoryRepository
    )
```

#### 2. Via Environment Variables (Database URL)

For SQLModelRepository, configure the database URL:

```bash
# .env
NITRO_DB_URL=postgresql://user:password@localhost/myapp
```

Then all entities using `table=True` will use this database.

### Default Repository

By default, all entities with `table=True` use `SQLModelRepository`:

```python
from nitro.domain.entities.base_entity import Entity

# This uses SQLModelRepository automatically
class Product(Entity, table=True):
    name: str
    price: float
```

---

## Swapping Backends

One of Nitro's most powerful features is the ability to swap persistence backends with minimal code changes.

### Example: Prototype to Production

**Development (In-Memory):**

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository
from pydantic import ConfigDict

class Todo(Entity, table=False):
    title: str
    completed: bool = False

    model_config = ConfigDict(
        repository_class=MemoryRepository
    )

# No database setup needed
todo = Todo(id="1", title="Build feature")
todo.save()
```

**Production (SQL Database):**

Change just **two lines**:

```python
from nitro.domain.entities.base_entity import Entity

# Change 1: Remove model_config
# Change 2: Set table=True
class Todo(Entity, table=True):
    title: str
    completed: bool = False

# Initialize database (once)
Todo.repository().init_db()

# Everything else stays the same
todo = Todo(id="1", title="Build feature")
todo.save()
```

That's it! Your business logic remains unchanged.

### Hybrid Persistence

You can mix repositories in the same application:

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository
from pydantic import ConfigDict

# SQL persistence for domain models
class Order(Entity, table=True):
    customer_name: str
    total: float

# Memory persistence for session data
class UserSession(Entity, table=False):
    cart_items: list = []

    model_config = ConfigDict(
        repository_class=MemoryRepository
    )

# Initialize SQL database
Order.repository().init_db()

# Use both together
session = UserSession(id="sess-1", cart_items=["item1", "item2"])
session.save()  # Saved to memory

order = Order(id="ord-1", customer_name="Alice", total=99.99)
order.save()  # Saved to database
```

---

## Complete Example: Multi-Repository App

Here's a complete example showing both repositories in action:

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository
from pydantic import ConfigDict

# SQL-backed product catalog (persistent)
class Product(Entity, table=True):
    name: str
    price: float
    stock: int

# Memory-backed shopping sessions (ephemeral)
class ShoppingSession(Entity, table=False):
    user_id: str
    items: list = []

    model_config = ConfigDict(
        repository_class=MemoryRepository
    )

# Initialize SQL database
Product.repository().init_db()

# Create some products (persistent)
laptop = Product(id="prod-1", name="Laptop", price=999.99, stock=10)
laptop.save()

mouse = Product(id="prod-2", name="Mouse", price=29.99, stock=50)
mouse.save()

# Create a shopping session (ephemeral, 30-minute TTL)
session = ShoppingSession(id="sess-abc", user_id="user-123", items=["prod-1", "prod-2"])
session.repository().save(session, ttl=1800)

# Retrieve data
all_products = Product.all()
active_session = ShoppingSession.get("sess-abc")

# Session expires after 30 minutes
# Product data persists indefinitely
```

---

## Related Documentation

- [Entity Overview](/entity/overview.md) - Understanding entity-centric design
- [Active Record Patterns](/entity/active-record.md) - All entity methods (save, get, filter, etc.)
- [Configuration Guide](/reference/api.md) - Environment variables and settings
