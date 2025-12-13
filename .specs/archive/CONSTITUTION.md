# Nitro Framework - Constitution

**Version:** 0.1 (Draft)
**Last Updated:** January 2025
**Status:** Work in Progress

This document defines the fundamental vision, principles, and architectural decisions of the Nitro Framework.

---

## WHY: The Core Vision

**The Vision:**
Nitro is a **performance-enhancing layer** for Python web frameworks - think of it as a nitro boost for your existing framework. It doesn't replace FastAPI, Flask, Django, or FastHTML; it supercharges them.

**What Nitro Brings:**
Nitro adds three powerful capabilities to any Python web framework:

1. **Rich Domain Entities** - Active Record pattern with built-in persistence, validation, and business logic
2. **Smart Event-Driven Routing** - CQRS-ready architecture with intelligent conventions that can be overridden
3. **Reactive HTML Templating** - Datastar-powered reactive frontends with zero JavaScript configuration

These three modules are **independent and composable** - use one, two, or all three based on your needs. No dependencies or hierarchy between them. Pick what you need, skip what you don't.

**Who It's For:**
- Solo developers who want to ship faster without sacrificing code quality
- Growing teams who need a solid foundation that scales with their needs
- Anyone who values Domain-Driven Design and convention over configuration

**The Philosophy:**
Framework-agnostic enhancement. Choose your core framework (FastAPI, Flask, Django, FastHTML, Sanic, LiteStar), add Nitro, and gain Rails-like productivity without vendor lock-in.

**In Practice:**
Install Nitro on your existing FastAPI app and immediately get rich entities, event-driven routing, and reactive templates - without rewriting a single route. Use what you need, when you need it.

---

## WHAT: The Three Core Modules

Nitro consists of three independent, composable modules. Each can be used standalone or combined with others.

---

### Module 1: Rich Domain Entities

**Purpose:** Provide Active Record pattern for domain models with built-in persistence, validation, and business logic.

**Core Capabilities:**
- **Active Record Pattern** - Entities know how to save/load/delete themselves
- **Hybrid Persistence** - Multiple backends (Memory, SQL, Redis, Browser storage)
- **Pydantic Validation** - Type-safe with automatic validation
- **Rich Business Logic** - Methods on entities, not scattered in services
- **Framework-Agnostic** - Works with any Python web framework

**Example:**
```python
class Product(Entity):
    name: str
    price: float
    stock: int = 0

    def restock(self, quantity: int):
        """Business logic lives here"""
        self.stock += quantity
        self.save()
        emit('product_restocked', self)

# Works with any framework
product = Product.get(id="123")
product.restock(50)
```

**Design Questions (To Be Resolved):**

1. **Active Model Abstraction Layer**
   - Should we have a base `Entity` (no persistence) + `ActiveEntity` (with Active Record)?
   - Or just `Entity` with swappable backends?
   - Rails has Active Model (abstract) and Active Record (persistence) - do we need both?

2. **SQLModel Integration**
   - Current implementation uses SQLModel as base. Is this the right choice?
   - Should we abstract further to support other ORMs?
   - How do we balance convenience vs flexibility?

3. **Repository Pattern Visibility**
   - Current implementation uses repositories internally
   - Should this be:
     - Hidden implementation detail (users only see Active Record methods)?
     - Public API for advanced users who want custom backends?
     - Both - simple API by default, repository access for power users?

---

### Module 2: Smart Event-Driven Routing

**Purpose:** Flexible event-driven architecture with optional CQRS support and convention-based routing.

**Core Capabilities:**
- **Event-Driven Commands/Queries** - Single endpoint, multiple handlers via events
- **CQRS-Ready** - Optional Command/Query separation for complex domains
- **Flexible Event System** - Enhanced Blinker with sync/async support
- **Convention Over Configuration** - Smart defaults, override when needed
- **Framework Adapters** - Works with FastAPI, Flask, FastHTML, Django, etc.

**The Event-Driven Routing Pattern:**
```python
# Single command endpoint handles multiple commands via events
@app.get("/cmds/{command}/{sender}")
async def commands(command: str, sender: str, request: Request, signals: ReadSignals):
    """Trigger events and broadcast to all connected clients"""
    backend_signal = event(command)
    await emit_async(backend_signal, sender, signals=signals, request=request)

# Handlers respond to specific commands
@on('product_restock')
async def handle_restock(sender, signals, request):
    product = Product.get(signals.product_id)
    product.restock(signals.quantity)
    # Emit result back to client via SSE
    yield emit_signals(product.signals)

# Multiple handlers can respond to same event
@on('product_restock')
async def log_restock(sender, signals, request):
    AuditLog.create(action='restock', product_id=signals.product_id)
```

**Key Design Principles:**
- **Fewer Endpoints, Wider Handling** - One `/cmds` endpoint can trigger many operations
- **CQRS is Optional** - Use full Command/Query separation when needed, or simple events
- **Flexible Architecture** - Events can be used in many ways beyond CQRS
- **Real-time by Default** - SSE streaming built-in for reactive updates

**Design Questions (To Be Resolved):**

1. **Convention-Based Route Generation**
   - Should we auto-generate routes from entity methods with decorators?
   - Example: `@action`, `@command`, `@query` decorators?
   - Or keep routing explicit and manual?
   - Both options available?

2. **CQRS Pattern**
   - Is CQRS a core feature or optional advanced pattern?
   - Should we provide `Command` and `Query` base classes?
   - Or let it emerge naturally from event usage patterns?

3. **Event System Enhancements**
   - Current: Enhanced Blinker with sync/async support
   - Future: Redis pub/sub for multi-instance?
   - Message queue integration (Celery, Dramatiq)?

---

### Module 3: Reactive HTML Templating

**Purpose:** RustyTags + Datastar powered reactive templates with smart Entity view helpers.

**Core Capabilities:**
- **RustyTags Integration** - Rust-powered HTML generation (3-10x faster than pure Python)
- **Datastar Reactivity** - Real-time updates via SSE + client-side reactive signals
- **Entity View Helpers** - Auto-generate forms, tables, CRUD UIs from entities
- **Tailwind CSS Support** - Built-in CLI for Tailwind integration
- **Smart Defaults, Fully Customizable** - Convention over configuration

**Example:**
```python
from nitro import Page, Form, Table

# Auto-generate form from entity
@app.get("/products/new")
def new_product():
    return Page(
        Form.from_entity(Product),  # Auto-generates input fields
        title="New Product"
    )

# Auto-generate table with real-time updates
@app.get("/products")
def product_list():
    return Page(
        Table.from_entity(Product)
            .with_actions(['edit', 'delete'])
            .with_search()
            .reactive(),  # Live updates via SSE
        title="Products"
    )
```

**Reactivity Model:**
- **Server-Side Real-time**: SSE (Server-Sent Events) for live updates from backend
- **Client-Side Reactivity**: Datastar signals for frontend state management
- **Zero JavaScript Configuration**: Reactive UIs without writing JS

**Entity View Helpers:**
1. **Auto-generate forms** - `Form.from_entity(Product)` creates input fields from entity schema
2. **Auto-generate tables/CRUD** - `Table.from_entity(Product)` creates admin-style tables
3. **Helper methods** - `product.to_card()`, `product.to_form()`, `product.to_row()`

**Design Questions (To Be Resolved):**

1. **RustyTags vs Other Templating**
   - RustyTags is recommended but optional - correct?
   - Should we support Jinja2, Mako, etc. as alternatives?
   - How do we maintain reactivity without RustyTags/Datastar?

2. **View Helper API Design**
   - Should helpers be methods on entities (`product.to_card()`)?
   - Or separate functions (`Card.from_entity(product)`)?
   - Or both for flexibility?

3. **Customization Strategy**
   - How do users override default templates?
   - Template inheritance? Component composition? Both?
   - How much control vs convention?

4. **Real-time Architecture**
   - SSE by default, WebSocket as option?
   - How to handle multi-instance deployments (Redis pub/sub)?
   - Client reconnection strategy?

---

