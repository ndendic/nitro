# Active Record Patterns

The Active Record pattern combines data and behavior in a single object. Nitro entities provide rich persistence methods that eliminate boilerplate and let you focus on business logic.

**Source:** `nitro/domain/entities/base_entity.py`

---

## Table of Contents

1. [Instance Methods](#instance-methods)
   - [save()](#save)
   - [delete()](#delete)
2. [Class Methods - Retrieval](#class-methods---retrieval)
   - [get()](#get)
   - [find()](#find)
   - [exists()](#exists)
   - [all()](#all)
   - [find_by()](#find_by)
3. [Class Methods - Querying](#class-methods---querying)
   - [where()](#where)
   - [filter()](#filter)
   - [search()](#search)
4. [Properties](#properties)
   - [signals](#signals)

---

## Instance Methods

These methods operate on individual entity instances.

### save()

Persists the entity to the configured repository.

**Signature:** `def save(self) -> bool`

**Returns:** `True` if save succeeded, `False` otherwise

**Example:**

```python
from nitro.domain.entities.base_entity import Entity

class Todo(Entity, table=True):
    title: str
    completed: bool = False

# Create and save
todo = Todo(id="1", title="Buy milk")
success = todo.save()
if success:
    print("Todo saved!")

# Update and save
todo.completed = True
todo.save()
```

**Notes:**
- Creates a new record if the entity doesn't exist
- Updates an existing record if `id` already exists in database
- Automatically manages database sessions
- Skips computed fields (properties without setters)

---

### delete()

Removes the entity from the repository.

**Signature:** `def delete(self) -> bool`

**Returns:** `True` if deletion succeeded, `False` if entity didn't exist

**Example:**

```python
from nitro.domain.entities.base_entity import Entity

class Todo(Entity, table=True):
    title: str
    completed: bool = False

# Get and delete
todo = Todo.get("1")
if todo:
    success = todo.delete()
    if success:
        print("Todo deleted!")
```

**Notes:**
- Returns `False` if the entity doesn't exist in the database
- Does not affect the in-memory object (you can still access its attributes)
- Uses the entity's `id` to locate the record

---

## Class Methods - Retrieval

These methods retrieve entities from the repository.

### get()

Retrieves an entity by its ID.

**Signature:** `@classmethod def get(cls, id: Any) -> Optional[Entity]`

**Parameters:**
- `id`: The entity's unique identifier

**Returns:** Entity instance or `None` if not found

**Example:**

```python
from nitro.domain.entities.base_entity import Entity

class Product(Entity, table=True):
    name: str
    price: float

# Retrieve by ID
product = Product.get("prod-123")
if product:
    print(f"Found: {product.name} - ${product.price}")
else:
    print("Product not found")
```

**Notes:**
- Automatically loads all relationships to avoid detached instance errors
- Returns `None` if no entity with the given ID exists
- Efficient - uses SQLAlchemy's session.get() internally

---

### find()

Alias for `get()`. Retrieves an entity by its ID.

**Signature:** `@classmethod def find(cls, id: Any) -> Optional[Entity]`

**Example:**

```python
from nitro.domain.entities.base_entity import Entity

class User(Entity, table=True):
    email: str
    name: str

# find() is identical to get()
user = User.find("user-456")
same_user = User.get("user-456")
```

**Notes:**
- Provided for developer preference (some prefer `find` over `get`)
- Functionally identical to `get()`

---

### exists()

Checks if an entity exists without retrieving it.

**Signature:** `@classmethod def exists(cls, id: Any) -> bool`

**Parameters:**
- `id`: The entity's unique identifier

**Returns:** `True` if entity exists, `False` otherwise

**Example:**

```python
from nitro.domain.entities.base_entity import Entity

class Order(Entity, table=True):
    customer_name: str
    total: float

# Check existence before processing
if Order.exists("order-789"):
    print("Order exists")
else:
    print("Order not found")
```

**Notes:**
- More efficient than `get()` when you only need to check existence
- Does not load the entity or its relationships
- Useful for validation logic

---

### all()

Retrieves all entities of this type.

**Signature:** `@classmethod def all(cls) -> List[Entity]`

**Returns:** List of all entity instances

**Example:**

```python
from nitro.domain.entities.base_entity import Entity

class Todo(Entity, table=True):
    title: str
    completed: bool = False

# Get all todos
all_todos = Todo.all()
for todo in all_todos:
    print(f"{todo.title}: {'✓' if todo.completed else '✗'}")

# Filter in Python
completed_todos = [t for t in all_todos if t.completed]
```

**Notes:**
- Returns an empty list if no entities exist
- Loads all records into memory - use with caution on large tables
- For large datasets, use `where()` or `filter()` with pagination

---

### find_by()

Finds entities by field values.

**Signature:** `@classmethod def find_by(cls, **kwargs) -> Union[List[Entity], Entity, None]`

**Parameters:**
- `**kwargs`: Field name and value pairs to match

**Returns:** First matching entity or `None` if not found

**Example:**

```python
from nitro.domain.entities.base_entity import Entity

class User(Entity, table=True):
    email: str
    name: str

# Find by single field
user = User.find_by(email="john@example.com")
if user:
    print(f"Found user: {user.name}")

# Find by multiple fields
user = User.find_by(email="john@example.com", name="John Doe")
```

**Notes:**
- Returns the **first** matching entity
- Returns `None` if no match found
- Use exact matching (not partial/fuzzy)
- For multiple results, use `filter()` instead

---

## Class Methods - Querying

These methods provide powerful querying capabilities.

### where()

Queries entities with SQLAlchemy-style expressions.

**Signature:**
```python
@classmethod
def where(
    cls,
    *expressions: Any,
    order_by: Optional[sa.Column] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Entity]
```

**Parameters:**
- `*expressions`: SQLAlchemy filter expressions
- `order_by`: Column to sort by (optional)
- `limit`: Maximum number of results (optional)
- `offset`: Number of results to skip (optional)

**Returns:** List of matching entities

**Example:**

```python
from nitro.domain.entities.base_entity import Entity

class Product(Entity, table=True):
    name: str
    price: float
    stock: int

# Simple filter
cheap_products = Product.where(Product.price < 10.0)

# Multiple conditions
available_cheap = Product.where(
    Product.price < 10.0,
    Product.stock > 0
)

# With ordering and pagination
top_expensive = Product.where(
    Product.stock > 0,
    order_by=Product.price.desc(),
    limit=10
)

# Offset for pagination
page_2 = Product.where(
    Product.stock > 0,
    order_by=Product.price,
    limit=10,
    offset=10
)
```

**Notes:**
- Most flexible querying method
- Supports all SQLAlchemy filter expressions
- Can pass column name as string to `order_by`: `order_by="price"`
- Use `.desc()` on columns for descending order

---

### filter()

Filters entities by exact field matches with sorting and pagination.

**Signature:**
```python
@classmethod
def filter(
    cls,
    sorting_field: Optional[str] = None,
    sort_direction: str = "asc",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    as_dict: bool = False,
    fields: Optional[List[str]] = None,
    exact_match: bool = True,
    **kwargs
) -> List[Entity]
```

**Parameters:**
- `sorting_field`: Field name to sort by (optional)
- `sort_direction`: `"asc"` or `"desc"` (default: `"asc"`)
- `limit`: Maximum number of results (optional)
- `offset`: Number of results to skip (optional)
- `as_dict`: Return dictionaries instead of entities (default: `False`)
- `fields`: List of field names to retrieve (optional, retrieves all by default)
- `exact_match`: Use exact matching vs. partial matching for strings (default: `True`)
- `**kwargs`: Field name and value pairs to filter by

**Returns:** List of matching entities (or dictionaries if `as_dict=True`)

**Example:**

```python
from nitro.domain.entities.base_entity import Entity

class Order(Entity, table=True):
    customer_name: str
    status: str
    total: float

# Simple filter
pending_orders = Order.filter(status="pending")

# With sorting
recent_pending = Order.filter(
    status="pending",
    sorting_field="total",
    sort_direction="desc"
)

# With pagination
page_1 = Order.filter(
    status="pending",
    limit=20,
    offset=0
)

# Partial string matching
johns_orders = Order.filter(
    customer_name="John",
    exact_match=False  # Finds "John Doe", "Johnny", etc.
)

# As dictionaries (for JSON responses)
orders_json = Order.filter(
    status="pending",
    as_dict=True
)

# Select specific fields
order_summaries = Order.filter(
    status="pending",
    fields=["id", "customer_name", "total"],
    as_dict=True
)
```

**Notes:**
- Validates field names against the model schema
- Supports `None` values: `filter(optional_field=None)`
- Supports `IN` queries: `filter(status=["pending", "processing"])`
- Date range queries: `filter(created_at=(start_date, end_date))`
- UUID fields: automatically converts strings to UUID objects
- Raises `ValueError` if invalid field names are provided

---

### search()

Searches entities across multiple text fields.

**Signature:**
```python
@classmethod
def search(
    cls,
    search_value: Optional[str] = None,
    sorting_field: Optional[str] = None,
    sort_direction: str = "asc",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    as_dict: bool = False,
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]
```

**Parameters:**
- `search_value`: Text to search for (optional)
- `sorting_field`: Field name to sort by (optional)
- `sort_direction`: `"asc"` or `"desc"` (default: `"asc"`)
- `limit`: Maximum number of results (optional)
- `offset`: Number of results to skip (optional)
- `as_dict`: Return dictionaries instead of entities (default: `False`)
- `fields`: List of field names to retrieve (optional)

**Returns:** List of matching entities (or dictionaries)

**Example:**

```python
from nitro.domain.entities.base_entity import Entity

class Product(Entity, table=True):
    name: str
    description: str
    sku: str
    price: float

# Search across all string fields
results = Product.search(search_value="laptop")
# Matches: name, description, or sku containing "laptop"

# With sorting and pagination
top_matches = Product.search(
    search_value="laptop",
    sorting_field="price",
    sort_direction="asc",
    limit=10
)

# As dictionaries
results_json = Product.search(
    search_value="laptop",
    as_dict=True
)
```

**Notes:**
- Automatically searches **all string fields** in the entity
- Uses case-insensitive partial matching (SQL `ILIKE`)
- Combines conditions with `OR` (matches any field)
- Returns all entities if `search_value` is `None` or empty
- Efficient for full-text-like searches without complex setup

---

## Properties

### signals

Returns a `Signals` object for reactive UI integration.

**Signature:** `@property def signals(self) -> Signals`

**Returns:** `Signals` instance containing all entity fields

**Example:**

```python
from nitro.domain.entities.base_entity import Entity
from rusty_tags import Div

class Counter(Entity, table=True):
    count: int = 0

# Use in Datastar components
counter = Counter.get("c1") or Counter(id="c1", count=0)

# The signals property creates a Signals object
component = Div(
    f"Count: {counter.count}",
    signals=counter.signals  # Signals(count=0)
)
```

**Notes:**
- Automatically converts entity fields to reactive signals
- Powered by `Signals(**self.model_dump())`
- See [Datastar Signals documentation](/frontend/datastar/signals.md) for frontend integration

---

## Complete Example: Blog Post Entity

Here's a comprehensive example showing multiple Active Record methods:

```python
from nitro.domain.entities.base_entity import Entity
from datetime import datetime, timezone

class BlogPost(Entity, table=True):
    title: str
    content: str
    author: str
    published: bool = False
    created_at: datetime = datetime.now(timezone.utc)

    def publish(self):
        """Business logic: publish the post."""
        self.published = True
        self.save()

# Initialize database
BlogPost.repository().init_db()

# Create posts
post1 = BlogPost(
    id="post-1",
    title="Getting Started",
    content="Welcome to my blog!",
    author="Alice"
)
post1.save()

post2 = BlogPost(
    id="post-2",
    title="Advanced Topics",
    content="Deep dive into...",
    author="Bob"
)
post2.save()
post2.publish()

# Retrieve by ID
post = BlogPost.get("post-1")

# Check existence
if BlogPost.exists("post-1"):
    print("Post exists")

# Get all posts
all_posts = BlogPost.all()

# Find by author
alice_posts = BlogPost.filter(author="Alice")

# Find published posts
published = BlogPost.filter(published=True)

# Search across all text fields
results = BlogPost.search(search_value="Advanced")

# Complex query with where()
recent_published = BlogPost.where(
    BlogPost.published == True,
    order_by=BlogPost.created_at.desc(),
    limit=5
)

# Delete a post
post1.delete()
```

---

## Related Documentation

- [Entity Overview](/entity/overview.md) - Understanding entity-centric design
- [Repository Patterns](/entity/repository-patterns.md) - Configuring persistence backends
- [Framework Integration](/frameworks/overview.md) - Using entities with web frameworks
