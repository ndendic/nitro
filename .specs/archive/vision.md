# Nitro Framework - Project Intent

**The Problem We're Solving**

Python web development forces developers into a false choice: use heavyweight monolithic frameworks that make decisions for you, or assemble low-level components yourself and write endless boilerplate. Neither approach respects how software actually evolves - starting simple and growing complex.

**What We're Building**

Nitro is a full-stack Python web framework add-on layer that treats business logic as first-class citizens. It provides rich domain entities that contain both data and behavior, lets each entity choose its own persistence backend, works on top of any Python web framework you already use, and scales from prototype to production without rewrites.

## The Core Intent

### 1. **Business Logic Belongs in Domain Entities**

**The Problem:**
Most Python frameworks push you toward "anemic domain models" - data classes with no behavior. Business logic ends up scattered across service layers, view functions, and utility modules. Finding where something happens requires grepping through multiple files.

**Our Solution:**
```python
class Order(Entity):
    customer_name: str
    total: float = 0.0
    status: str = "draft"
    
    def add_item(self, price: float):
        """Business logic lives here, not in a service layer."""
        self.total += price
        self.save()
    
    def place_order(self):
        """Domain operations are discoverable and testable."""
        if self.total == 0:
            raise ValueError("Cannot place empty order")
        self.status = "placed"
        self.save()
        order_placed.send(self)  # Domain event
```

**Why This Matters:**
- Business logic is **discoverable** - look at the entity class
- Changes are **localized** - modify one place, not five
- Testing is **straightforward** - test entity methods directly
- Domain expertise is **preserved** - the code reads like the business

### 2. **Persistence Should Match Your Needs**

**The Problem:**
Traditional ORMs force a one-size-fits-all approach. Everything must be in SQL, even when a shopping cart belongs in memory, analytics in Redis, and UI preferences in the browser.

**Our Solution:**
```python
# Session data - ephemeral
class UserSession(Entity):
    cart_items: list = []
    _persistence_backend_class = MemoryRepo

# Domain models - durable
class Product(SQLEntity, table=True):
    name: str
    price: float
    _persistence_backend_class = SQLModelBackend

# Caching layer - fast access
class UserAnalytics(Entity):
    page_views: int = 0
    _persistence_backend_class = RedisRepo

# UI state - client-side
class UIPreferences(Entity):
    theme: str = "light"
    _persistence_backend_class = DatastarRepo
```

**Why This Matters:**
- **Right tool for the job** - don't put everything in PostgreSQL
- **Independent scaling** - cache separately from persistent storage
- **Clear data ownership** - each entity declares its storage strategy
- **Performance optimization** - use memory for hot paths, SQL for durability

### 3. **Framework-Agnostic by Design**

**The Problem:**
Choosing a web framework becomes a permanent decision. Want to switch from Flask to FastAPI? Rewrite everything. Need to add FastHTML for hypermedia? Can't mix them.

**Our Solution:**
```python
# Works with FastAPI
from fastapi import FastAPI
from nitro import Entity

app = FastAPI()

@app.post("/orders")
def create_order(customer_name: str):
    order = Order(customer_name=customer_name)
    order.save()
    return order

# Works with Flask
from flask import Flask
app = Flask(__name__)

@app.route("/orders", methods=["POST"])
def create_order():
    order = Order(customer_name=request.json["customer_name"])
    order.save()
    return jsonify(order.model_dump())

# Works with FastHTML
from fasthtml.common import *
app, rt = fast_app()

@rt("/orders")
def orders():
    orders = Order.all()
    return Div(*[order_card(o) for o in orders])
```

**Why This Matters:**
- **Adopt incrementally** - add Nitro to existing apps
- **Mix frameworks** - use FastAPI for API, FastHTML for admin UI
- **No lock-in** - switch routing layer without touching domain logic
- **Future-proof** - new frameworks emerge, your entities remain unchanged

### 4. **Events for Decoupled Architecture**

**The Problem:**
Business operations have side effects. Placing an order should send emails, update inventory, create audit logs. Cramming all this into one function creates a tangled mess.

**Our Solution:**
```python
from blinker import signal

# Domain event
order_placed = signal('order-placed')

# Business operation
class Order(Entity):
    def place_order(self):
        self.status = "placed"
        self.save()
        order_placed.send(self)  # Single responsibility

# Decoupled handlers
@on(order_placed)
def send_confirmation_email(order):
    EmailService.send(order.customer_email, "Order confirmed")

@on(order_placed)
def update_inventory(order):
    for item in order.items:
        Product.get(item.product_id).reduce_stock(item.quantity)

@on(order_placed)
def create_audit_log(order):
    AuditLog(action="order_placed", order_id=order.id).save()
```

**Why This Matters:**
- **Single Responsibility** - each handler does one thing
- **Easy to extend** - add new side effects without changing order logic
- **Testable in isolation** - mock event handlers during tests
- **CQRS ready** - separate commands from queries naturally

### 5. **Progressive Complexity**

**The Problem:**
Frameworks either start simple and become unmaintainable (Flask), or start complex and intimidate beginners (Django). You shouldn't need enterprise patterns for a prototype.

**Our Solution:**

**Day 1 - MVP:**
```python
class Counter(Entity):
    count: int = 0
    def increment(self): 
        self.count += 1

@app.post("/counter/{id}/increment")
def increment(id: str):
    counter = Counter.get(id)
    counter.increment()
    return counter
```

**Month 6 - Growing:**
```python
class Product(SQLEntity, table=True):
    name: str
    price: float
    
    @event(method="POST")  # Auto-routing
    def restock(self, quantity: int):
        self.stock += quantity
        inventory_changed.send(self)

admin.register(Product)  # Auto-generated CRUD UI
```

**Year 2 - Enterprise:**
```python
class Order(SQLEntity):
    @command  # CQRS pattern
    async def place_order(self, items: List[Item]):
        async with UnitOfWork() as uow:
            self.status = "placed"
            await uow.orders.save(self)
            await uow.commit()
        order_placed.send(self)

# Multi-instance sync via Redis pub/sub
# Background job processing via Celery
# GraphQL API auto-generated from entities
```

**Why This Matters:**
- **Learn gradually** - master basics before advanced patterns
- **Refactor confidently** - patterns emerge from needs, not imposed upfront
- **No rewrites** - the same entities work at every scale
- **Teams can collaborate** - junior devs work on entities, seniors add infrastructure

## What Makes Nitro Different

### Compared to Django/Rails
- **Not monolithic** - enhancement layer, not replacement
- **Hybrid persistence** - each entity chooses its backend
- **Real composability** - mix with any Python web framework

### Compared to FastAPI + SQLAlchemy
- **Rich domain models** - behavior built-in, not separated
- **Auto-CRUD** - admin UI generated from entity definitions
- **Event system** - domain events for decoupled architecture

### Compared to FastHTML
- **Domain modeling** - entities with business logic
- **Multiple persistence** - not just database tables
- **CQRS ready** - command/query separation when you need it

## The Intended Developer Experience

A Python developer should be able to:

1. **Build a working app in 15 minutes**
   ```bash
   pip install nitro
   # Write < 50 lines of code
   # Have CRUD + real-time updates working
   ```

2. **Scale to production without rewrites**
   ```python
   # Start: MemoryRepo for prototyping
   # Later: SQLModelBackend for persistence
   # Later: Add Redis caching
   # Later: Add CQRS patterns
   # Same entity class throughout
   ```

3. **Mix and match components**
   ```python
   # FastAPI for REST API
   # FastHTML for admin UI
   # Same entities power both
   # Event system coordinates them
   ```

4. **Test business logic easily**
   ```python
   def test_order_placement():
       order = Order(customer_name="Alice")
       order.add_item(29.99)
       order.place_order()
       assert order.status == "placed"
       assert order.total == 29.99
   ```

5. **Deploy to any infrastructure**
   ```python
   # SQLite for development
   # PostgreSQL for production
   # Redis for caching
   # Same code, different config
   ```

## Why This Matters

**For Solo Developers:**
Start with in-memory entities and manual routes. Ship your MVP in hours, not weeks. Upgrade to SQL when you get users. Add Redis when you hit performance bottlenecks. The framework grows with your needs.

**For Startups:**
Build features, not infrastructure. Domain experts can read and write entity code. Business logic is testable and maintainable. Pivot without throwing away your domain model.

**For Enterprises:**
Adopt incrementally into existing systems. Add Nitro entities to legacy FastAPI apps. Keep your existing routing layer. Add CQRS patterns when microservices require them. No big-bang migrations.

## The Path Forward

**Phase 1:** Rich entities with hybrid persistence - business logic first  
**Phase 2:** Auto-routing and CRUD UI generation - reduce boilerplate  
**Phase 3:** CQRS and application service layer - enterprise patterns  
**Phase 4:** Multi-instance coordination and plugins - production scale  

Each phase is optional. Use what you need, ignore what you don't.

## The Ultimate Goal

**Build web applications the way you think about them:**
- Business operations are methods on entities
- Data storage matches the data's nature
- Side effects are events, not entangled code
- Complexity emerges from requirements, not imposed upfront
- Your domain model is the documentation

**Python deserves a framework that respects this.**

Nitro is that framework.

---

**TL;DR:** Nitro brings rich domain modeling, hybrid persistence, framework agnosticism, event-driven architecture, and progressive complexity to Python web development. Start simple, scale to enterprise, never rewrite.