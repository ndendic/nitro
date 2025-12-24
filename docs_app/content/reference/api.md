# API Reference

Quick reference for Nitro Framework APIs. See linked documentation for detailed usage and examples.

---

## Entity API

Complete documentation: [Entity Overview](../entity/overview.md) | [Active Record Patterns](../entity/active-record.md)

### Instance Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `save()` | `def save(self) -> bool` | Persist entity to repository. Returns True on success. |
| `delete()` | `def delete(self) -> bool` | Remove entity from repository. Returns True if deleted. |

### Class Methods - Retrieval

| Method | Signature | Description |
|--------|-----------|-------------|
| `get(id)` | `@classmethod def get(cls, id: Any) -> Optional[Entity]` | Retrieve entity by ID. Returns None if not found. |
| `find(id)` | `@classmethod def find(cls, id: Any) -> Optional[Entity]` | Alias for get(). |
| `exists(id)` | `@classmethod def exists(cls, id: Any) -> bool` | Check if entity exists without loading it. |
| `all()` | `@classmethod def all(cls) -> List[Entity]` | Retrieve all entities of this type. |
| `find_by(**kwargs)` | `@classmethod def find_by(cls, **kwargs) -> Optional[Entity]` | Find first entity matching field values. |

### Class Methods - Querying

| Method | Signature | Description |
|--------|-----------|-------------|
| `where(*expr, ...)` | `@classmethod def where(cls, *expressions, order_by=None, limit=None, offset=None) -> List[Entity]` | Query with SQLAlchemy expressions. Supports ordering and pagination. |
| `filter(**kwargs)` | `@classmethod def filter(cls, sorting_field=None, sort_direction="asc", limit=None, offset=None, as_dict=False, fields=None, exact_match=True, **kwargs) -> List[Entity]` | Filter by exact field matches with sorting and pagination. |
| `search(value, ...)` | `@classmethod def search(cls, search_value=None, sorting_field=None, sort_direction="asc", limit=None, offset=None, as_dict=False, fields=None) -> List[Entity]` | Search across all text fields with partial matching. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `signals` | `Signals` | Returns Signals object for reactive UI integration. |

---

## Events API

Complete documentation: [Events Overview](../events/overview.md) | [Backend Events](../events/backend-events.md)

### Event Creation

| Function | Signature | Description |
|----------|-----------|-------------|
| `event(name, doc=None)` | `def event(name: str, doc: str = None) -> Event` | Create or retrieve a named event from the default namespace. |

### Handler Registration

| Decorator | Signature | Description |
|-----------|-----------|-------------|
| `@on(evt, ...)` | `@on(evt, sender=ANY, weak=True, priority=0, condition=None)` | Register handler function to event. Supports async, generators, priorities, and conditions. |

### Event Emission

| Function | Signature | Description |
|----------|-----------|-------------|
| `emit(event, sender, ...)` | `def emit(event_to_emit, sender=ANY, *args, **kwargs) -> List` | Emit event synchronously. Async handlers scheduled but not awaited. |
| `emit_async(event, sender, ...)` | `async def emit_async(event_to_emit, sender=ANY, *args, **kwargs) -> List` | Emit event asynchronously, awaiting all handlers in parallel. |

---

## Client API (SSE/Real-time)

Complete documentation: [CQRS Patterns](../events/cqrs-patterns.md)

### Constructor

| Class | Signature | Description |
|-------|-----------|-------------|
| `Client` | `Client(client_id=None, topics=["ANY"], muted_topics=ANY)` | Create client for topic-based SSE subscriptions. |

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `subscribe(topic, senders=ANY)` | `def subscribe(self, topic: str, senders=ANY)` | Subscribe to topic pattern after creation. |
| `unsubscribe(topic)` | `def unsubscribe(self, topic: str)` | Unsubscribe from topic. |
| `connect()` | `def connect(self) -> Client` | Connect client and start receiving events. |
| `disconnect()` | `def disconnect(self) -> Client` | Disconnect client and cleanup resources. |
| `stream(delay=0.1)` | `async def stream(self, delay: float = 0.1)` | Async generator yielding events from queue. |
| `send(item)` | `def send(self, item) -> bool` | Manually send item to client's queue. |

---

## Page API

Complete documentation: [RustyTags Usage](../frontend/rustytags/usage.md)

### Constructor

| Component | Signature | Description |
|-----------|-----------|-------------|
| `Page` | `Page(*content, title="Nitro", hdrs=None, ftrs=None, htmlkw=None, bodykw=None, datastar=True, ds_version="1.0.0-RC.6", nitro_components=True, monsterui=False, tailwind4=False, lucide=False, highlightjs=False)` | Complete HTML page with CDN integrations. |

### Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `*content` | elements | - | Body content elements |
| `title` | str | "Nitro" | Page title |
| `hdrs` | tuple | None | Additional head elements |
| `ftrs` | tuple | None | Additional footer scripts |
| `htmlkw` | dict | None | HTML tag attributes |
| `bodykw` | dict | None | Body tag attributes |
| `datastar` | bool | True | Include Datastar SDK |
| `ds_version` | str | "1.0.0-RC.6" | Datastar version |
| `nitro_components` | bool | True | Include Nitro component styles |
| `tailwind4` | bool | False | Include Tailwind v4 CDN |
| `lucide` | bool | False | Include Lucide icons |
| `highlightjs` | bool | False | Include Highlight.js for code |

---

## Signal API

Complete documentation: [Datastar Signals](../frontend/datastar/signals.md)

### Signal Class

| Class | Signature | Description |
|-------|-----------|-------------|
| `Signal` | `Signal(name: str, initial=None, type_=None, namespace=None)` | Single reactive value with type inference and JavaScript generation. |

### Signal Methods

| Method | Description |
|--------|-------------|
| `to_js()` | Get JavaScript reference (e.g., "$count") |
| `add(n)` | Increment signal by n |
| `sub(n)` | Decrement signal by n |
| `set(value)` | Set signal to value |

### Signals Container

| Class | Signature | Description |
|-------|-----------|-------------|
| `Signals` | `Signals(namespace=None, **kwargs)` | Dictionary-like container managing multiple signals. |

### Signals Methods

| Method | Description |
|--------|-------------|
| `to_dict()` | Get dict for data-signals attribute (e.g., {"count": 0}) |
| `to_js()` | Get JavaScript reference for entire namespace |

**Usage Pattern:**
```python
sigs = Signals(count=0, name="Alice")
sigs.count              # → Signal object (for expressions)
sigs["count"]           # → 0 (raw value)
sigs.to_dict()          # → {"count": 0, "name": "Alice"}
```

---

## Framework Adapters

Complete documentation: [Framework Integration](../frameworks/overview.md)

### The @action Decorator

| Decorator | Signature | Description |
|-----------|-----------|-------------|
| `@action` | `@action(method="POST", path=None, response_model=None, status_code=200, tags=None, summary=None, description=None)` | Mark entity method as HTTP endpoint for auto-routing. |

**Source:** `nitro/infrastructure/routing/decorator.py:19-132`

### Framework Configuration

| Function | Signature | Description |
|----------|-----------|-------------|
| `configure_nitro(app, ...)` | `configure_nitro(app, entities=None, prefix="", auto_discover=True)` | Configure Nitro auto-routing for web framework. Available for FastAPI, Flask, FastHTML, Starlette. |

### Dispatcher Classes

| Class | Framework | Description |
|-------|-----------|-------------|
| `FastAPIDispatcher` | FastAPI | Auto-routing for FastAPI apps |
| `FlaskDispatcher` | Flask | Auto-routing for Flask apps |
| `FastHTMLDispatcher` | FastHTML | Auto-routing for FastHTML apps |
| `StarletteDispatcher` | Starlette | Auto-routing for Starlette apps |

**Source:** `nitro/infrastructure/routing/dispatcher.py:22-260`

---

## Related Documentation

- [Getting Started Guide](../getting-started/quickstart.md) - Quick introduction to Nitro
- [Entity Documentation](../entity/overview.md) - Entity-centric design patterns
- [Events System](../events/overview.md) - Event-driven architecture
- [Frontend Integration](../frontend/rustytags/overview.md) - RustyTags and Datastar
- [CLI Reference](cli.md) - Command-line tools
