---
title: Backend Events API
category: Events
order: 2
---

# Backend Events API

Complete reference for Nitro's event system including event creation, handler registration, emission, and advanced features like priorities and conditions.

Reference: `nitro/infrastructure/events/events.py:1-270`

---

## Quick Reference

```python
from nitro.infrastructure.events import event, on, emit, emit_async, Event, Namespace, ANY

# Create or get event
user_created = event('user-created')

# Register handler
@on('user-created')
def handler(sender, **kwargs):
    pass

# Emit event
emit('user-created', user_instance)

# Async emit
results = await emit_async('user-created', user_instance)
```

---

## Creating Events

### `event(name, doc=None)`

Creates or retrieves a named event from the default namespace.

**Parameters:**
- `name` (str) - Event name (e.g., `"user-created"`, `"order.placed"`)
- `doc` (str, optional) - Documentation string for the event

**Returns:** `Event` instance

**Example:**
```python
from nitro.infrastructure.events import event

# Create event
user_created = event('user-created')

# With documentation
order_placed = event(
    'order-placed',
    doc="Fired when an order is successfully placed"
)

# Same name returns same instance
evt1 = event('user-created')
evt2 = event('user-created')
assert evt1 is evt2  # True
```

**Naming Conventions:**
```python
# Simple names
event('created')
event('updated')
event('deleted')

# Namespaced with dots
event('user.created')
event('order.placed')
event('payment.failed')

# Namespaced with hyphens
event('user-registered')
event('order-shipped')
```

---

## Registering Handlers

### `@on(evt, sender=ANY, weak=True, priority=0, condition=None)`

Decorator to connect a handler function to an event.

**Parameters:**
- `evt` (str | Event) - Event name or Event instance
- `sender` (Any, default: ANY) - Only fire for specific sender
- `weak` (bool, default: True) - Use weak references (garbage collection)
- `priority` (int, default: 0) - Higher priority executes first
- `condition` (Callable, optional) - Must return True for handler to execute

**Returns:** Decorated function (unchanged)

### Basic Usage

```python
from nitro.infrastructure.events import event, on

user_created = event('user-created')

# Simple handler
@on(user_created)
def welcome_email(sender, **kwargs):
    print(f"Welcome {sender.email}!")

# Using event name directly
@on('user-created')
def create_profile(sender, **kwargs):
    print(f"Creating profile for {sender.username}")
```

### Handler Types

The event system automatically detects and handles different handler types:

#### Sync Function
```python
@on('order-placed')
def log_order(sender, **kwargs):
    print(f"Order {sender.id} placed")
    return "logged"
```

#### Async Function
```python
@on('order-placed')
async def send_email(sender, **kwargs):
    await email_service.send(sender.customer_email, "Order confirmed")
    return "email sent"
```

#### Sync Generator
```python
@on('order-placed')
def process_items(sender, **kwargs):
    for item in sender.items:
        # Process each item
        updated_item = process(item)
        yield updated_item
```

#### Async Generator
```python
@on('order-placed')
async def stream_updates(sender, **kwargs):
    async for update in async_process_order(sender):
        yield update
```

### Sender Filtering

Only fire handlers for specific senders:

```python
from nitro.infrastructure.events import ANY

# Fire for all senders (default)
@on('entity-updated', sender=ANY)
def log_all_updates(sender, **kwargs):
    print(f"Entity {sender.id} updated")

# Fire only for specific sender
admin_user = User.get("admin-123")

@on('entity-updated', sender=admin_user)
def admin_update_alert(sender, **kwargs):
    print("Admin entity updated!")
```

### Priority Execution

Control handler execution order with priorities (higher = first):

```python
@on('user-registered', priority=10)
def validate_user(sender, **kwargs):
    """Runs first - validates user data"""
    if not sender.email or '@' not in sender.email:
        print("Invalid email!")
        return False  # Cancels remaining handlers
    return True

@on('user-registered', priority=5)
def assign_default_role(sender, **kwargs):
    """Runs second"""
    sender.role = "user"
    sender.save()

@on('user-registered', priority=0)
def send_welcome_email(sender, **kwargs):
    """Runs last (default priority)"""
    EmailService.send(sender.email, "Welcome!")
```

**Priority Rules:**
- Higher numbers execute first
- Same priority: execution order is registration order
- Default priority is 0
- Negative priorities are allowed

### Conditional Handlers

Only execute handlers when conditions are met:

```python
# Simple condition - lambda
@on('order-placed', condition=lambda sender, **kw: sender.total > 100)
def high_value_alert(sender, **kwargs):
    """Only fires for orders over $100"""
    print(f"High value order: ${sender.total}")

# Complex condition - function
def is_premium_user(sender, **kwargs):
    return hasattr(sender, 'subscription') and sender.subscription == 'premium'

@on('user-login', condition=is_premium_user)
def premium_greeting(sender, **kwargs):
    print(f"Welcome back, premium user {sender.username}!")

# Multiple conditions
def large_order_condition(sender, **kwargs):
    return sender.total > 500 and len(sender.items) > 10

@on('order-placed', condition=large_order_condition)
def bulk_order_processing(sender, **kwargs):
    print("Processing bulk order")
```

**Condition Rules:**
- Must accept `sender` and `**kwargs` parameters
- Must return boolean (True = execute, False = skip)
- Exceptions in conditions cause handler to be skipped
- Conditions are evaluated in priority order

### Handler Cancellation

Handlers can stop event propagation by returning `False`:

```python
@on('order-placed', priority=10)
def fraud_check(sender, **kwargs):
    if sender.total > 10000:
        print("⚠️  Fraud alert! Blocking order.")
        return False  # Stops all remaining handlers

@on('order-placed', priority=0)
def send_confirmation(sender, **kwargs):
    # This won't run if fraud_check returned False
    print("Order confirmed!")
```

---

## Emitting Events

### `emit(event_to_emit, sender=ANY, *args, **kwargs)`

Emit an event synchronously. Async handlers are scheduled but not awaited.

**Parameters:**
- `event_to_emit` (str | Event) - Event name or Event instance
- `sender` (Any, default: ANY) - The object emitting the event
- `*args` - Positional arguments passed to handlers
- `**kwargs` - Keyword arguments passed to handlers

**Returns:** List of handler results

**Example:**
```python
from nitro.infrastructure.events import event, emit

order_placed = event('order-placed')

class Order(Entity, table=True):
    customer_email: str
    total: float

    def place_order(self):
        self.status = "placed"
        self.save()

        # Emit with self as sender
        results = emit(order_placed, self)
        print(f"Handlers returned: {results}")

        # Emit with custom data
        emit(order_placed, self, order_total=self.total, customer_id=self.customer_id)
```

**Passing Data to Handlers:**
```python
# Via kwargs
emit('user-registered', user, welcome_bonus=100, referral_code="XYZ")

@on('user-registered')
def apply_bonus(sender, welcome_bonus, referral_code, **kwargs):
    print(f"Applying ${welcome_bonus} bonus with code {referral_code}")
```

### `emit_async(event_to_emit, sender=ANY, *args, **kwargs)`

Emit an event asynchronously, awaiting all handlers in parallel.

**Parameters:** Same as `emit()`

**Returns:** List of handler results (awaited)

**Example:**
```python
from nitro.infrastructure.events import event, emit_async

order_placed = event('order-placed')

@on(order_placed)
async def send_email(sender, **kwargs):
    await email_service.send(sender.customer_email, "Order confirmed")
    return "email sent"

@on(order_placed)
async def update_inventory(sender, **kwargs):
    for item in sender.items:
        await inventory_service.reduce_stock(item.product_id, item.quantity)
    return "inventory updated"

# Emit and wait for all handlers
class Order(Entity, table=True):
    async def place_order_async(self):
        self.status = "placed"
        self.save()

        # Wait for all async handlers to complete
        results = await emit_async(order_placed, self)
        print(f"All handlers completed: {results}")
        # Output: ['email sent', 'inventory updated']
```

**Key Differences:**

| Feature | `emit()` | `emit_async()` |
|---------|----------|----------------|
| Async handlers | Scheduled (fire and forget) | Awaited in parallel |
| Sync handlers | Executed immediately | Executed immediately |
| Returns | Sync handler results only | All handler results |
| Use in | Sync and async code | Async code only |

---

## Event Class

Direct access to Event instances for advanced usage.

### Methods

#### `event.emit(sender, *args, **kwargs)`

Emit the event (same as `emit(event, sender, ...)`):

```python
from nitro.infrastructure.events import event

user_created = event('user-created')

# These are equivalent
user_created.emit(user)
emit(user_created, user)
```

#### `event.connect(receiver, sender=ANY, weak=True, priority=0, condition=None)`

Connect a handler without using the decorator:

```python
user_created = event('user-created')

def my_handler(sender, **kwargs):
    print(f"User created: {sender.username}")

# Connect manually
user_created.connect(my_handler, priority=5)
```

#### `async event.emit_async(sender, *args, **kwargs)`

Async emit from Event instance:

```python
user_created = event('user-created')

# These are equivalent
await user_created.emit_async(user)
await emit_async(user_created, user)
```

---

## Namespace

Organize related events into namespaces.

### Creating Namespaces

```python
from nitro.infrastructure.events import Namespace

# Create custom namespace
auth_events = Namespace()

# Create events in namespace
login_event = auth_events.event('login')
logout_event = auth_events.event('logout')
password_reset = auth_events.event('password-reset')
```

### Default Namespace

All `event()` calls use the default namespace:

```python
from nitro.infrastructure.events import default_namespace, event

# These are equivalent
user_created = event('user-created')
user_created = default_namespace.event('user-created')
```

### Filtering Events by Pattern

Query events using glob patterns:

```python
from nitro.infrastructure.events import event, filter_signals

# Create events
event('user.created')
event('user.updated')
event('user.deleted')
event('order.placed')

# Filter by pattern
user_events = filter_signals('user.*')
# Returns: {'user.created': Event(...), 'user.updated': Event(...), 'user.deleted': Event(...)}

all_events = filter_signals('*')
# Returns all events in default namespace
```

**Pattern Matching:**
- `*` - Matches anything
- `user.*` - Matches all events starting with "user."
- `*.created` - Matches all "created" events
- Uses `nitro.utils.match()` under the hood

---

## Complete Example

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.events import event, on, emit, emit_async, ANY

# Define events
order_placed = event('order-placed', doc="Order successfully placed")
payment_processed = event('payment-processed')

# Priority handler - validates first
@on(order_placed, priority=10)
def validate_order(sender, **kwargs):
    if sender.total <= 0:
        print("❌ Invalid order - total must be > 0")
        return False  # Cancel other handlers
    return True

# Conditional handler - only for large orders
@on(order_placed, condition=lambda sender, **kw: sender.total > 1000, priority=5)
def high_value_alert(sender, **kwargs):
    print(f"🚨 High value order: ${sender.total}")

# Regular handlers
@on(order_placed)
def send_confirmation(sender, **kwargs):
    print(f"📧 Sending confirmation to {sender.customer_email}")

@on(order_placed)
async def process_payment(sender, **kwargs):
    print(f"💳 Processing payment of ${sender.total}")
    await asyncio.sleep(1)  # Simulate async work
    emit(payment_processed, sender)
    return "payment complete"

@on(order_placed)
def update_inventory(sender, **kwargs):
    for item in sender.items:
        print(f"📦 Reducing stock for {item.product_name}")
    yield "inventory updated"

# Entity that emits events
class Order(Entity, table=True):
    customer_email: str
    total: float
    items: list = []

    def place_order(self):
        self.status = "placed"
        self.save()

        # Emit event (async handlers scheduled, sync handlers executed)
        results = emit(order_placed, self)
        print(f"Sync results: {results}")

    async def place_order_async(self):
        self.status = "placed"
        self.save()

        # Await all handlers
        results = await emit_async(order_placed, self)
        print(f"All results: {results}")

# Usage
order = Order(
    id="ord-123",
    customer_email="alice@example.com",
    total=1500,
    items=[{"product_name": "Widget"}]
)

order.place_order()
# Output:
# 🚨 High value order: $1500
# 📧 Sending confirmation to alice@example.com
# 💳 Processing payment of $1500
# 📦 Reducing stock for Widget
# Sync results: [True, ['inventory updated']]
```

---

## Best Practices

### Event Naming

```python
# ✅ Good - clear, descriptive
event('user-registered')
event('order-placed')
event('payment-failed')

# ✅ Good - namespaced
event('user.created')
event('order.shipped')
event('inventory.low-stock')

# ❌ Avoid - too generic
event('done')
event('finished')
event('update')
```

### Handler Signatures

Always accept `sender` and `**kwargs`:

```python
# ✅ Good - flexible
@on('event')
def handler(sender, **kwargs):
    pass

# ✅ Good - extract specific kwargs
@on('event')
def handler(sender, user_id, total, **kwargs):
    # user_id and total extracted from kwargs
    pass

# ❌ Avoid - will break if kwargs added
@on('event')
def handler(sender):
    pass  # Missing **kwargs
```

### Error Handling

Handlers should handle their own errors:

```python
@on('order-placed')
def send_email(sender, **kwargs):
    try:
        EmailService.send(sender.customer_email, "Confirmed")
    except Exception as e:
        print(f"Email failed: {e}")
        # Don't let exceptions prevent other handlers from running
```

### Testing

Test handlers independently:

```python
import pytest
from nitro.infrastructure.events import event, emit

def test_order_placed_handler():
    """Test email handler in isolation"""
    order_placed = event('test-order-placed')

    emails_sent = []

    @on(order_placed)
    def track_emails(sender, **kwargs):
        emails_sent.append(sender.customer_email)

    # Emit test event
    order = Order(id="test", customer_email="test@example.com", total=100)
    emit(order_placed, order)

    assert "test@example.com" in emails_sent
```

---

## Next Steps

- **[CQRS Patterns →](cqrs-patterns.md)** - Real-time updates with the Client class
- **[Events Overview →](overview.md)** - Event-driven architecture philosophy

---

## Related Documentation

- **[Entity Overview →](../entity/overview.md)** - Entity-centric domain models
- **[Datastar SSE →](../frontend/datastar/sse-integration.md)** - Frontend real-time updates
