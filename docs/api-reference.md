# Nitro API Reference

> **Version:** 0.1.0
> **Last updated:** 2026-04-03
> **Status:** Draft — ready for review

Nitro is a collection of abstraction layers for Python web development. This reference covers the complete public API surface.

---

## Table of Contents

1. [Top-Level Exports](#top-level-exports)
2. [Entity (Active Record)](#entity)
3. [Repository](#repository)
4. [Routing](#routing)
5. [Events](#events)
6. [SSE Helpers](#sse-helpers)
7. [Adapters](#adapters)
8. [HTML & Templating](#html--templating)
9. [Datastar (Reactivity)](#datastar-reactivity)
10. [Configuration](#configuration)
11. [CLI](#cli)
12. [Monitoring](#monitoring)
13. [Utilities](#utilities)

---

## Top-Level Exports

```python
from nitro import (
    # Core
    Entity,
    # Routing decorators
    action, get, post, put, delete,
    ActionMetadata,
    # Events
    Client,
    # Utils
    show, AttrDict, uniq,
)
```

Everything from `nitro.html` and `nitro.html.datastar` is also re-exported at the top level (all HTML tags, `Signals`, `Signal`, `DS`, `Page`, etc.).

---

## Entity

**Module:** `nitro.domain.entities.base_entity`
**Import:** `from nitro import Entity`
**Inherits:** `SQLModel` (SQLAlchemy + Pydantic)

The Entity class implements the Active Record pattern. Business logic lives in entity methods. All entities share a singleton `SQLModelRepository`.

### Defining an Entity

```python
from nitro import Entity

class Order(Entity, table=True):
    id: str
    customer_name: str
    total: float = 0.0
    status: str = "draft"

    def place(self):
        self.status = "placed"
        self.save()
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Primary key (required on all entities) |

### Class Methods

#### `Entity.repository() -> SQLModelRepository`

Returns the singleton repository instance.

#### `Entity.get(id: Any) -> Optional[Entity]`

Fetches an entity by primary key.

```python
order = Order.get("order-1")
```

#### `Entity.exists(id: Any) -> bool`

Returns `True` if a record with the given id exists.

#### `Entity.all() -> List[Entity]`

Returns all records for this entity type.

#### `Entity.where(*expressions, order_by=None, limit=None, offset=None) -> List[Entity]`

Filters using raw SQLAlchemy expressions.

```python
orders = Order.where(
    Order.status == "placed",
    Order.total > 100,
    order_by=Order.total,
    limit=10,
)
```

**Parameters:**
- `*expressions: Any` — SQLAlchemy filter expressions
- `order_by: Optional[sa.Column]` — Column to sort by
- `limit: Optional[int]` — Max records to return
- `offset: Optional[int]` — Records to skip

#### `Entity.find(id: Any) -> Optional[Entity]`

Alias for `get()` with eager relationship loading.

#### `Entity.find_by(**kwargs) -> Union[List[Entity], Entity, None]`

Finds records matching all provided field/value pairs.

```python
order = Order.find_by(customer_name="Alice", status="placed")
```

#### `Entity.search(search_value=None, sorting_field=None, sort_direction="asc", limit=None, offset=None, as_dict=False, fields=None) -> List[Dict]`

Full-text ILIKE search across all string fields.

```python
results = Order.search("alice", sorting_field="total", sort_direction="desc", limit=20)
```

**Parameters:**
- `search_value: Optional[str]` — Search term (ILIKE across all `str` fields)
- `sorting_field: Optional[str]` — Field name to sort by
- `sort_direction: str` — `"asc"` or `"desc"` (default: `"asc"`)
- `limit: Optional[int]` — Max results
- `offset: Optional[int]` — Skip count
- `as_dict: bool` — Return dicts instead of entities
- `fields: Optional[List[str]]` — Project specific fields only

#### `Entity.filter(sorting_field=None, sort_direction="asc", limit=None, offset=None, as_dict=False, fields=None, exact_match=True, **kwargs) -> List[Entity]`

Field-level filtering with sorting and pagination.

```python
orders = Order.filter(status="placed", exact_match=True, limit=50)
```

**Parameters:**
- `exact_match: bool` — `True` for exact match, `False` for ILIKE (default: `True`)
- `**kwargs` — Field/value pairs to filter by
- All other params same as `search()`

#### `Entity.fields_meta(exclude=None, include_computed=False) -> AttrDict`

Returns field metadata (names, types, defaults) for the entity.

### Instance Methods

#### `entity.save() -> bool`

Persists the current instance (upsert by id). Always returns `True`.

```python
order = Order(id="o1", customer_name="Alice", total=42.0)
order.save()
```

#### `entity.delete() -> bool`

Deletes the current instance from the database.

### Properties

#### `entity.signals -> Signals`

Returns a `Signals` instance populated from the entity's current field values. Used for Datastar reactivity.

```python
order = Order.get("o1")
sigs = order.signals  # Signals(id="o1", customer_name="Alice", ...)
```

### Lifecycle Hook

#### `Entity.__init_subclass__(**kwargs)`

Automatically calls `register_entity_actions(cls)` on subclass definition, which scans for `@get`, `@post`, `@put`, `@delete` decorated methods and registers them as Blinker event handlers.

---

## Repository

### SQLModelRepository

**Module:** `nitro.domain.repository.sql`
**Pattern:** Singleton

```python
from nitro.domain.repository.sql import SQLModelRepository
```

#### Constructor

```python
SQLModelRepository(
    url: Optional[str] = config.db_url,  # default: "sqlite:///nitro.db"
    echo: bool = False,
    pool_size: Optional[int] = None,
    max_overflow: Optional[int] = None,
    pool_timeout: Optional[float] = None,
    **engine_kwargs,
)
```

Pool parameters are ignored for SQLite URLs. Singleton — only the first call configures the instance.

#### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `init_db` | `()` | `None` | Creates all registered tables |
| `get_session` | `()` | `Generator[Session]` | Yields a SQLAlchemy Session context manager |
| `schema` | `()` | `str` | Human-readable table/column listing |
| `all` | `(model)` | `List[SQLModel]` | All rows for a model type |
| `get` | `(model, id)` | `Optional[SQLModel]` | Fetch by primary key |
| `find` | `(model, id)` | `Optional[SQLModel]` | Fetch by PK with eager relationship loading |
| `find_by` | `(model, **kwargs)` | `Optional[SQLModel]` | First match for field/value pairs |
| `exists` | `(model, id)` | `bool` | Check existence by PK |
| `save` | `(record)` | `bool` | Upsert by id |
| `update` | `(model, id, data)` | `Dict` | Partial update from dict |
| `delete` | `(record)` | `bool` | Delete by type + id |
| `where` | `(model, *exprs, order_by, limit, offset)` | `List[SQLModel]` | Raw expression filtering |
| `filter` | `(model, sorting_field, sort_direction, limit, offset, as_dict, fields, exact_match, **kwargs)` | `List[Dict]` | Field-level filtering |
| `search` | `(model, search_value, sorting_field, sort_direction, limit, offset, as_dict, fields)` | `List[Dict]` | ILIKE search across string fields |
| `count` | `(model)` | `int` | Row count |
| `bulk_create` | `(model, data: List[Dict])` | `List[SQLModel]` | Batch insert |
| `bulk_upsert` | `(model, data: List[Dict])` | `List[SQLModel]` | Batch update existing records by id |

### MemoryRepository

**Module:** `nitro.domain.repository.memory`
**Pattern:** Singleton

In-process dict-based persistence with optional TTL.

```python
from nitro.domain.repository.memory import MemoryRepository, get_memory_persistence
```

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `save` | `(entity, ttl=None)` | `bool` | Store with optional TTL (seconds) |
| `find` | `(key: str)` | `Optional[Entity]` | Fetch by key, evicts if expired |
| `delete` | `(key: str)` | `bool` | Remove by key |
| `exists` | `(key: str)` | `bool` | Check existence with lazy expiry |

### EntityRepositoryInterface (ABC)

**Module:** `nitro.domain.repository.base`

Abstract base class. Subclasses must implement: `save`, `find`, `delete`, `exists`.

### Inheritance

```
ABC
└── EntityRepositoryInterface
    ├── SQLModelRepository   (SQL-backed, singleton)
    └── MemoryRepository     (in-process dict, singleton)
```

---

## Routing

**Module:** `nitro.routing`
**Import:** `from nitro import action, get, post, put, delete, ActionMetadata`

Nitro's routing system is event-driven: decorators register Blinker event handlers, and catch-all adapter routes dispatch incoming requests.

### Decorators

#### `@get(prefix="", **kwargs)`

Registers a method as a GET action handler.

```python
class Counter(Entity, table=True):
    count: int = 0

    @get()
    def status(self):
        return {"count": self.count, "id": self.id}
```

#### `@post(prefix="", status_code=200, **kwargs)`

Registers a method as a POST action handler.

```python
@post()
async def increment(self, request, amount: int = 1):
    self.count += amount
    self.save()
```

#### `@put(prefix="", **kwargs)`

Registers a method as a PUT action handler.

#### `@delete(prefix="", status_code=204, **kwargs)`

Registers a method as a DELETE action handler. Note: default `status_code=204`.

#### `@action(method="POST", prefix="", path=None, status_code=200, ...)`

Core decorator factory — the other four are shortcuts to this.

**Full parameters:**
- `method: str` — HTTP method (default: `"POST"`)
- `prefix: str` — URL prefix
- `path: Optional[str]` — Custom URL path
- `status_code: int` — Response status code
- `summary: Optional[str]` — API summary
- `description: Optional[str]` — API description
- `tags: Optional[list]` — API tags
- `response_model: Optional[Any]` — Response type

**Behavior:**
- On **standalone functions**: stamps `ActionMetadata` and immediately registers a Blinker handler
- On **Entity methods**: stamps metadata only — registration deferred to `Entity.__init_subclass__`

### Action String Generator

#### `action(method_or_func, **params) -> str`

**Import:** `from nitro import action` (same name, different usage — function reference vs decorator)

Generates a Datastar-compatible action string from a decorated method reference.

```python
counter = Counter.get("c1")
action(counter.increment, amount=5)
# → "$amount = 5; @post('/post/Counter:c1.increment')"

action(Counter.status)
# → "@get('/get/Counter.status')"
```

### ActionRef

**Module:** `nitro.routing.actions`

```python
from nitro.routing import ActionRef, parse_action

@dataclass
class ActionRef:
    entity: Optional[str] = None
    id: Optional[str] = None
    method: Optional[str] = None
    prefix: Optional[str] = None
    function: Optional[str] = None
```

**Properties:**
- `is_instance_method -> bool` — `True` when `id` is not `None`
- `event_name -> str` — Reconstructed Blinker event name

#### `parse_action(action: str) -> ActionRef`

Parses action string formats:
- `"Counter:c1.increment"` → entity=Counter, id=c1, method=increment
- `"prefix.function"` → prefix=prefix, function=function
- `"function"` → function=function

### ActionMetadata

**Module:** `nitro.routing.metadata`

```python
@dataclass
class ActionMetadata:
    method: str = "POST"
    path: Optional[str] = None
    status_code: int = 200
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    response_model: Optional[Type] = None
    function_name: str = ""
    entity_class_name: str = ""
    event_name: str = ""
    prefix: str = ""
    is_async: bool = False
    parameters: dict = field(default_factory=dict)
```

**Utility functions:**
- `set_action_metadata(func, metadata)` — Store metadata on a function
- `get_action_metadata(func) -> Optional[ActionMetadata]` — Retrieve metadata
- `has_action_metadata(func) -> bool` — Check if metadata exists
- `extract_parameters(func) -> dict` — Inspect function signature

### NotFoundError

```python
from nitro.routing import NotFoundError

class NotFoundError(Exception): ...
```

Raised when an entity instance method handler cannot find the entity by id.

### Registration

#### `register_entity_actions(cls) -> None`

**Module:** `nitro.routing.registration`

Scans all public methods of `cls` for `ActionMetadata`, sets `entity_class_name` and `event_name`, then registers Blinker handlers. Called automatically by `Entity.__init_subclass__`.

---

## Events

**Module:** `nitro.events`

Nitro's event system is transitioning from a Blinker-based legacy API to a new `nitro_events` pub/sub API.

### New API (Recommended)

```python
from nitro.events import subscribe, publish, publish_sync, Signal, Message
```

| Name | Kind | Description |
|------|------|-------------|
| `subscribe` | function/decorator | Subscribe a handler to a topic pattern |
| `publish` | async function | Publish a `Message` to a topic |
| `publish_sync` | function | Publish synchronously |
| `Signal` | class | Named pub/sub signal |
| `Message` | class | Envelope with `topic`, `data`, `source` |
| `PubSub` | class | Pub/sub backend |
| `get_default_pubsub` | function | Get global PubSub instance |
| `set_default_pubsub` | function | Replace global PubSub instance |
| `match` | function | Topic pattern matching |
| `filter_dict` | function | Filter dict by topic pattern |

### Legacy API (Deprecated — removed in v2.0)

```python
from nitro.events import event, on, emit, emit_async, Event, ANY
```

#### `event(name, doc=None) -> Event`

Get or create a named event.

#### `@on(evt, sender=ANY, weak=True, priority=0, condition=None)`

Decorator to connect a handler to an event.

```python
from nitro.events import event, on, emit

order_placed = event('order-placed')

@on(order_placed)
def send_email(sender, **kwargs):
    ...

emit(order_placed, sender=order_instance)
```

#### `emit(event_name, sender=ANY, *args, **kwargs) -> list`

Synchronous emit.

#### `emit_async(event_name, sender=ANY, *args, **kwargs) -> list`

Async emit (parallel via `asyncio.gather`).

#### `ANY = "*"`

Wildcard sender — subscribe to all senders.

### Client (SSE Streaming)

**Module:** `nitro.events.client`
**Import:** `from nitro import Client`

```python
class Client(BaseClient):
    async def stream(timeout: float = 30.0) -> AsyncGenerator[Message]
    def send(item: Message | Any) -> bool
    def send_data(topic: str, data: Any, **kwargs) -> bool
```

```python
from nitro import Client

with Client(topics={"updates.*": ["user-123"]}) as client:
    async for update in client.stream(timeout=30):
        yield update
```

### Deprecation Map

| Legacy | New Replacement |
|--------|-----------------|
| `Event` | `Signal` |
| `event(name)` | `Signal(name)` |
| `on(evt)` | `@subscribe(pattern)` |
| `emit()` | `publish_sync()` |
| `emit_async()` | `await publish()` |
| `active_clients` | `Client.get_active_clients()` |

---

## SSE Helpers

**Module:** `nitro.events.starlette`

Functions for publishing SSE-formatted Datastar updates to topics.

### `emit_elements(elements, selector=None, mode=REPLACE, topic="sse", source=None, ...) -> str`

Publishes HTML element patches via SSE.

```python
from nitro.events.starlette import emit_elements
from nitro.html.components.model_views import ModelTable

return emit_elements(
    ModelTable(Counter, id="counter-table"),
    topic="updates.ui",
    source=user_id,
)
```

**Parameters:**
- `elements: str | HtmlProvider` — HTML content to send
- `selector: Optional[str]` — CSS selector target
- `mode: ElementPatchMode` — `REPLACE` (default), `APPEND`, `PREPEND`, etc.
- `use_view_transition: Optional[bool]` — Enable view transitions
- `event_id: Optional[str]` — SSE event ID
- `retry_duration: Optional[int]` — SSE retry interval
- `topic: str | list[str]` — Topic(s) to publish to (default: `"sse"`)
- `source: Optional[str]` — Source identifier

### `remove_elements(selector, topic="sse", source=None, ...) -> str`

Removes elements matching a CSS selector.

### `emit_signals(signals, topic="sse", source=None, ...) -> str`

Publishes signal value updates.

```python
emit_signals({"count": 42}, topic="updates.ui")
```

**Parameters:**
- `signals: dict | str` — Signal values to update
- `only_if_missing: Optional[bool]` — Only set if signal doesn't exist yet

### `execute_script(script, auto_remove=True, topic="sse", source=None, ...) -> str`

Executes JavaScript on connected clients.

### `redirect(location, topic="sse", source=None, ...) -> str`

Redirects connected clients to a new URL.

### `publish_to_topic(topic, data, source=None) -> None`

Low-level topic publish for raw data.

---

## Adapters

**Module:** `nitro.adapters`

Each adapter registers 5 catch-all routes (GET/POST/PUT/DELETE/PATCH) on the target framework, dispatching to Nitro's event-driven routing system.

### Sanic (Primary)

```python
from nitro.adapters.sanic_adapter import configure_nitro

app = Sanic("MyApp")
configure_nitro(app, prefix="")
```

### FastAPI

```python
from nitro.adapters.fastapi import configure_nitro

app = FastAPI()
configure_nitro(app, prefix="")
```

### Flask

```python
from nitro.adapters.flask import configure_nitro

app = Flask(__name__)
configure_nitro(app, prefix="")
```

### `configure_nitro(app, prefix="") -> None`

All three adapters share the same function signature:
- `app` — Framework application instance
- `prefix: str` — URL prefix for catch-all routes (default: `""`)

Raises `ImportError` if the target framework is not installed.

### `dispatch_action(action_str, sender, signals=None, request=None) -> Any`

**Module:** `nitro.adapters.catch_all`

Framework-agnostic action dispatcher. Parses the action string, looks up the Blinker handler, and calls it.

---

## HTML & Templating

### HTML Tags

**Module:** `nitro.html` (re-exports from `rusty_tags`)

All standard HTML5 tags are available as Python functions:

```python
from nitro import Div, H1, P, A, Button, Span, Input, Form, Table, ...
```

Plus: `Fragment`, `Safe`, `HtmlString`, `CustomTag`, `TagBuilder`, and all SVG elements.

### Page

**Module:** `nitro.html.templating`

```python
from nitro.html import Page

page = Page(
    H1("Welcome"),
    Div("Content"),
    title="My Page",
    datastar=True,
    tailwind4=True,
    lucide=True,
    highlightjs=True,
)
```

**Parameters:**
- `*content` — HTML elements
- `title: str` — Page title (default: `"Nitro"`)
- `hdrs: Optional[tuple]` — Extra header elements
- `ftrs: Optional[tuple]` — Extra footer elements
- `htmlkw: Optional[dict]` — Attributes on `<html>` tag
- `bodykw: Optional[dict]` — Attributes on `<body>` tag
- `datastar: bool` — Include Datastar SDK (default: `True`)
- `ds_version: str` — Datastar version (default: `"1.0.0-RC.6"`)
- `nitro_components: bool` — Include Nitro component scripts (default: `True`)
- `charts: bool` — Include chart libraries
- `tailwind4: bool` — Include Tailwind v4 CDN
- `lucide: bool` — Include Lucide icons
- `highlightjs: bool` — Include Highlight.js
- `favicon: Optional[str]` — Favicon URL
- `favicon_dark: Optional[str]` — Dark mode favicon URL

### Templates

#### `page_template(page_title="Nitro", ...) -> Callable`

Factory that returns a template decorator pre-configured with `Page` options.

```python
from nitro.html import page_template

my_page = page_template("My App", datastar=True, tailwind4=True)

@my_page
def index():
    return Div(H1("Hello"), P("World"))
```

Alias: `create_template = page_template`

#### `@template`

Decorator that marks a function as a layout template.

```python
from nitro.html import template

@template
def layout(content):
    return Div(cls="container")(content)

@layout
def page():
    return H1("Inside layout")
```

### Components

Located in `nitro.html.components`. Includes: Accordion, Alert, AlertDialog, Avatar, Badge, Breadcrumb, Button, Calendar, Card, Charts, Checkbox, Codeblock, Combobox, Command, Datepicker, Dialog, Dropdown, Dropzone, Field, Icons, Input, InputGroup, Kbd, Label, Pagination, Popover, Progress, Radio, Select, Sheet, Sidebar, Skeleton, Spinner, Switch, Table, Tabs, Textarea, ThemeSwitcher, Toast, Tooltip.

### Model Views

**Module:** `nitro.html.components.model_views`

Entity-driven UI components that auto-generate from entity field metadata:

- `ModelTable` — Data table from entity records
- `ModelForm` — Form generated from entity fields
- `ModelCards` — Card grid from entity records
- `ModelDialog` — Modal dialog for entity CRUD
- `ModelCombobox` — Searchable select from entity records
- `ModelField` — Individual field renderer

---

## Datastar (Reactivity)

**Module:** `nitro.html.datastar` (re-exports from `rusty_tags.datastar`)

### Signal

```python
from nitro import Signal

count = Signal("count", initial=0)
count.to_js()      # → "$count"
count.set(5)       # → Assignment: "$count = 5"
count.add(1)       # → "$count + 1"
count.toggle(True, False)  # → toggle between values
```

**Constructor:**
- `name: str` — Signal name
- `initial: Any` — Initial value (default: `None`)
- `type_: Optional[type]` — Type hint
- `namespace: Optional[str]` — Signal namespace

**Expression methods** (chainable, return JS expressions):
`.set()`, `.add()`, `.sub()`, `.mul()`, `.div()`, `.mod()`, `.toggle()`, `.if_()`, `.then()`, `.lower()`, `.upper()`, `.strip()`, `.contains()`, `.round()`, `.abs()`, `.min()`, `.max()`, `.clamp()`, `.append()`, `.prepend()`, `.pop()`, `.remove()`, `.join()`, `.slice()`

**Operator overloads:** `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `&`, `|`, `~`

### Signals

```python
from nitro import Signals

sigs = Signals(count=0, name="Alice")
sigs.count          # → Signal("count", initial=0)
sigs.count.add(1)   # → JS expression
str(sigs)           # → JSON for data-signals attribute
```

**Constructor:** `Signals(**kwargs)` — special kwarg `namespace` sets signal namespace.

### DS (Static Actions)

```python
from nitro.html.datastar import DS

DS.get("/api/data")              # → "@get('/api/data')"
DS.post("/api/save", target="#result", data={"name": "$name"})
DS.set("count", 5)               # → "$count = 5"
DS.toggle("visible")             # → "$visible = !$visible"
DS.increment("count", 2)         # → "$count = $count + 2"
DS.chain(DS.set("loading", True), DS.post("/api/save"))
```

### Expression Utilities

```python
from nitro.html.datastar import js, value, expr, f, if_, all_, any_, classes

js("console.log('hello')")       # Raw JS passthrough
value(42)                         # Safe JS literal
expr(signal).add(1)               # Chainable expression
f("Hello {name}")                 # Reactive template literal
if_(condition, "yes", "no")       # Ternary
all_(sig1, sig2)                  # All truthy check
any_(sig1, sig2)                  # Any truthy check
classes(active="$isActive", hidden="!$visible")  # Reactive classes
```

**Additional utilities:** `regex()`, `match()`, `switch()`, `collect()`, `seq()`, `post()`, `get()`, `put()`, `patch()`, `delete()`, `clipboard()`, `set_timeout()`, `clear_timeout()`, `reset_timeout()`, `signals()`, `reactive_class()`, `build_data_signals()`

### SSE / Datastar Types (from `datastar_py`)

```python
from nitro.html.datastar import SSE, ElementPatchMode, EventType
```

---

## Configuration

**Module:** `nitro.config`

### NitroConfig

```python
from nitro.config import get_nitro_config

config = get_nitro_config()
config.db_url           # "sqlite:///nitro.db"
config.project_root     # Path.cwd()
config.tailwind         # TailwindConfig instance
```

**Fields:**
- `project_root: Path` — Project root (default: `cwd()`)
- `db_url: str` — Database URL (default: `"sqlite:///nitro.db"`)
- `tailwind: TailwindConfig` — Tailwind settings

**Computed properties:**
- `css_input_absolute -> Path`
- `css_output_absolute -> Path`
- `css_dir_absolute -> Path`

**Environment variables:** Prefix `NITRO_`
- `NITRO_DB_URL` — Database connection string
- `NITRO_TAILWIND_CSS_INPUT` — Input CSS path
- `NITRO_TAILWIND_CSS_OUTPUT` — Output CSS path
- `NITRO_TAILWIND_CONTENT_PATHS` — JSON array of globs

**Config files:** Loads from `.env`, `.env.local`, `.env.prod` (in order).

### TailwindConfig

```python
class TailwindConfig(BaseSettings):
    css_input: Path = Path("static/css/input.css")
    css_output: Path = Path("static/css/output.css")
    content_paths: list[str] = ["**/*.py", "**/*.html", "**/*.jinja2", ...]
```

### Backward Compatibility

```python
ProjectConfig = NitroConfig
detect_project_config = get_nitro_config
get_project_config = get_nitro_config
```

---

## CLI

**Entry point:** `nitro` (registered in `pyproject.toml`)

### Tailwind Commands

```bash
nitro tw init       # Initialize Tailwind CSS in project
nitro tw dev        # Watch mode for development
nitro tw build      # Production build with minification
```

### Database Commands

```bash
nitro db init                      # Initialize Alembic migrations
nitro db migrations -m "message"   # Generate migration
nitro db migrate                   # Apply migrations
```

### Scaffold

```bash
nitro boost         # Scaffold a new Nitro project
```

---

## Monitoring

**Module:** `nitro.monitoring`

### Logging

```python
from nitro.monitoring import configure_nitro_logging, log_entity_operation

logger = configure_nitro_logging(level=logging.INFO)
log_entity_operation("Order", "save", entity_id="o1", total=42.0)
```

### Repository Monitor

```python
from nitro.monitoring import repository_monitor

repository_monitor.enable()
# ... run operations ...
stats = repository_monitor.all_stats()
# {"Order": {"queries_executed": 5, "saves": 3, "avg_query_time": 0.002, ...}}
repository_monitor.reset()
```

**RepositoryStats fields:** `queries_executed`, `saves`, `deletes`, `gets`, `cache_hits`, `cache_misses`, `total_query_time`, `avg_query_time` (property), `cache_hit_ratio` (property)

### Event Bus Monitor

```python
from nitro.monitoring import event_bus_monitor

event_bus_monitor.enable()
# ... fire events ...
metrics = event_bus_monitor.all_metrics()
event_bus_monitor.reset()
```

**EventMetrics fields:** `events_fired`, `handlers_executed`, `total_handler_time`, `errors`, `avg_handler_time` (property)

---

## Utilities

**Module:** `nitro.utils`

### `uniq(length=6) -> str`

Random hex string (from `uuid4`).

```python
from nitro import uniq
uniq()    # → "a3f2b1"
uniq(12)  # → "a3f2b1c8d4e5"
```

### `show(html) -> IPython.display.HTML`

Render HTML in Jupyter notebooks. Raises `ImportError` if IPython unavailable.

### `AttrDict(dict)`

Dict with attribute-style access. Missing keys return `None`.

```python
from nitro import AttrDict
d = AttrDict(name="Alice", age=30)
d.name    # "Alice"
d.email   # None (no KeyError)
```

### `match(query, item) -> bool`

Glob pattern match using `fnmatch`. Supports `!` prefix for negation.

### `filter_dict(query, dct) -> dict`

Filter dict keys by glob pattern.

---

## Quick Reference: Complete Example

```python
from sanic import Sanic
from nitro import Entity, get, post, action, Div, Button, Span, Signals, Page
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events.starlette import emit_elements

# 1. Define entity with actions
class Counter(Entity, table=True):
    count: int = 0

    @post()
    async def increment(self, request, amount: int = 1):
        self.count += amount
        self.save()
        return emit_elements(counter_view(self), topic="updates.ui")

    @get()
    def status(self):
        return {"count": self.count, "id": self.id}

# 2. Build reactive UI
def counter_view(counter):
    sigs = counter.signals
    return Div(
        Span(f"Count: {counter.count}", id="count"),
        Button("+1", data_on_click=action(counter.increment, amount=1)),
    )

# 3. Setup app
app = Sanic("CounterApp")
configure_nitro(app)

@app.get("/")
async def index(request):
    Entity.repository().init_db()
    counter = Counter.get("main") or Counter(id="main", count=0)
    counter.save()
    return Page(counter_view(counter), title="Counter")
```
