---
title: Event-Driven Architecture
category: Events
order: 1
---

# Event-Driven Architecture

Nitro's event system decouples business logic from side effects, enabling clean, testable code that's easy to extend without modification.

## Core Philosophy

**Business logic should focus on business logic** - When an entity performs an action (like placing an order), it shouldn't need to know about sending emails, updating analytics, or triggering webhooks. These side effects should be handled separately.

Events solve this by allowing entities to announce "something happened" without knowing who's listening or what they'll do about it.

---

## Why Events?

### Without Events

```python
from nitro.domain.entities.base_entity import Entity

class Order(Entity, table=True):
    customer_email: str
    total: float = 0.0
    status: str = "draft"

    def place_order(self):
        # Business logic mixed with side effects
        self.status = "placed"
        self.save()

        # Side effects tightly coupled
        EmailService.send(self.customer_email, "Order confirmed")
        Analytics.track("order_placed", {"total": self.total})
        InventoryService.reduce_stock(self.items)
        WebhookService.notify("https://api.example.com/orders")
```

**Problems:**
- Entity knows about email, analytics, inventory, webhooks
- Hard to test business logic in isolation
- Adding new side effects requires modifying entity code
- Side effects execute synchronously, slowing down the request

### With Events

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.events import event, on, emit

# Define the event
order_placed = event('order-placed')

class Order(Entity, table=True):
    customer_email: str
    total: float = 0.0
    status: str = "draft"

    def place_order(self):
        # Pure business logic
        self.status = "placed"
        self.save()

        # Announce what happened (fire and forget)
        emit(order_placed, self)

# Side effects handled separately
@on(order_placed)
def send_confirmation_email(sender, **kwargs):
    EmailService.send(sender.customer_email, "Order confirmed")

@on(order_placed)
def track_analytics(sender, **kwargs):
    Analytics.track("order_placed", {"total": sender.total})

@on(order_placed)
async def update_inventory(sender, **kwargs):
    for item in sender.items:
        await InventoryService.reduce_stock(item.product_id, item.quantity)

@on(order_placed)
def trigger_webhook(sender, **kwargs):
    WebhookService.notify("https://api.example.com/orders", sender.model_dump())
```

**Benefits:**
- Entity focuses on business logic only
- Side effects are decoupled and independent
- Easy to add/remove handlers without touching entity code
- Each handler can be tested independently
- Async handlers run without blocking
- Clear separation of concerns

---

## Built on Blinker

Nitro's event system is built on [Blinker](https://blinker.readthedocs.io/), Python's fast signal library. We enhance it with:

- **Async support** - Handlers can be sync, async, generators, or async generators
- **Priority execution** - Control handler execution order
- **Conditional handlers** - Handlers only execute when conditions are met
- **Cancellation** - Handlers can stop event propagation
- **Namespace organization** - Group related events together

Reference: `nitro/infrastructure/events/events.py:1-270`

---

## When to Use Events

### Use Events For:

**Decoupling side effects** - Emails, notifications, webhooks, analytics
```python
@on('user-registered')
def send_welcome_email(sender, **kwargs):
    pass
```

**Cross-cutting concerns** - Logging, auditing, caching
```python
@on('entity-updated')
def audit_trail(sender, **kwargs):
    AuditLog.create(entity=sender, action="updated")
```

**Real-time updates** - WebSocket/SSE notifications to clients
```python
@on('todo-created')
async def notify_clients(sender, **kwargs):
    await broadcast_to_clients(sender.model_dump())
```

**Async processing** - Long-running tasks that shouldn't block
```python
@on('order-placed')
async def process_payment(sender, **kwargs):
    await PaymentService.charge(sender.total)
```

### Don't Use Events For:

**Direct relationships** - Use method calls or return values
```python
# ❌ Don't use events
emit('calculate-tax', order)

# ✅ Use direct calls
tax = TaxService.calculate(order)
```

**Request-response patterns** - Use functions or APIs
```python
# ❌ Don't use events
emit('get-user', user_id)

# ✅ Use direct calls
user = User.get(user_id)
```

**Critical business logic** - Keep it in entity methods
```python
# ❌ Don't put business logic in handlers
@on('order-placed')
def validate_order(sender, **kwargs):
    if sender.total < 0:
        raise ValueError("Invalid order")

# ✅ Validate in entity method
class Order(Entity):
    def place_order(self):
        if self.total < 0:
            raise ValueError("Invalid order")
        self.status = "placed"
        self.save()
        emit(order_placed, self)
```

---

## Quick Example

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.events import event, on, emit

# 1. Define your event
user_registered = event('user-registered')

# 2. Add handlers
@on(user_registered)
def send_welcome_email(sender, **kwargs):
    print(f"📧 Sending welcome email to {sender.email}")

@on(user_registered)
async def create_profile(sender, **kwargs):
    print(f"👤 Creating profile for {sender.username}")

# 3. Emit from entity
class User(Entity, table=True):
    email: str
    username: str

    def register(self):
        self.save()
        emit(user_registered, self)

# 4. Use it
user = User(id="u1", email="alice@example.com", username="alice")
user.register()
# Output:
# 📧 Sending welcome email to alice@example.com
# 👤 Creating profile for alice
```

---

## Event System Features

### Handler Types

Events support four handler types:

```python
# Sync function
@on('event')
def sync_handler(sender, **kwargs):
    return "result"

# Async function
@on('event')
async def async_handler(sender, **kwargs):
    await some_async_work()
    return "result"

# Sync generator
@on('event')
def generator_handler(sender, **kwargs):
    for item in process_items(sender):
        yield item

# Async generator
@on('event')
async def async_generator_handler(sender, **kwargs):
    async for item in async_stream(sender):
        yield item
```

### Priority & Conditions

```python
# Higher priority executes first
@on('order-placed', priority=10)
def validate_order(sender, **kwargs):
    if not sender.is_valid():
        return False  # Cancels remaining handlers

@on('order-placed', priority=0)
def send_confirmation(sender, **kwargs):
    pass  # Only runs if validation passed

# Conditional execution
@on('order-placed', condition=lambda sender, **kw: sender.total > 100)
def high_value_alert(sender, **kwargs):
    """Only fires for orders over $100"""
    pass
```

### Async Emission

```python
# Sync emission (handlers run independently)
emit(order_placed, order)

# Async emission (wait for all handlers)
results = await emit_async(order_placed, order)
```

---

## Next Steps

- **[Backend Events →](backend-events.md)** - Learn the full event system API
- **[CQRS Patterns →](cqrs-patterns.md)** - Real-time updates with the Client class

---

## Related Documentation

- **[Entity Overview →](../entity/overview.md)** - Entity-centric domain models
- **[Repository Patterns →](../entity/repository-patterns.md)** - Persistence layer
