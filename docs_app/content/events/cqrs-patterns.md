# Real-Time Communication with Client

The Client class enables real-time communication between backend and frontend using Server-Sent Events (SSE) and topic-based subscriptions.

Reference: `nitro/infrastructure/events/client.py:1-127`

---

## Overview

The Client class implements a pub/sub pattern where:

1. **Clients subscribe to topics** (event patterns like `"todo.*"` or `"user.created"`)
2. **Backend emits events** when entities change
3. **Clients receive updates** via SSE stream
4. **Frontend updates UI** in real-time

This enables real-time features like live dashboards, collaborative editing, and instant notifications without polling.

---

## Quick Start

### Backend: SSE Endpoint

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from nitro.infrastructure.events import Client, event, emit

app = FastAPI()

# Define event
todo_created = event('todo.created')

@app.get("/events")
async def sse_endpoint():
    """Server-Sent Events endpoint for real-time updates"""
    # Create client subscribed to all todo events
    client = Client(topics=["todo.*"])

    async def event_stream():
        with client:  # Connect and auto-disconnect
            async for data in client.stream():
                yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# Emit events when data changes
@app.post("/todos")
def create_todo(title: str):
    todo = Todo(id=str(uuid.uuid4()), title=title, completed=False)
    todo.save()

    # Emit event with result data
    emit(todo_created, todo, result=todo.model_dump())

    return {"status": "created", "id": todo.id}
```

### Frontend: EventSource

```javascript
const eventSource = new EventSource('/events');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received update:', data);

    // Update UI
    addTodoToList(data);
};

eventSource.onerror = (error) => {
    console.error('SSE error:', error);
};
```

---

## Client Class

### Constructor

```python
Client(
    client_id: str | None = None,
    topics: list[str] | dict[str, list[str]] | Any = ["ANY"],
    muted_topics: str | list[str] | Any = ANY
)
```

**Parameters:**
- `client_id` (str, optional) - Unique identifier (auto-generated if None)
- `topics` - Topics to subscribe to (list, dict, or ANY)
- `muted_topics` - Topics to ignore (string, list, or ANY)

**Returns:** Client instance

### Topic Subscription Patterns

#### Subscribe to All Events
```python
client = Client(topics=["ANY"])
# or
client = Client(topics=ANY)
```

#### Subscribe to Specific Events
```python
# Single event
client = Client(topics=["todo.created"])

# Multiple events
client = Client(topics=["todo.created", "todo.updated", "user.login"])
```

#### Subscribe to Event Patterns
```python
# All todo events
client = Client(topics=["todo.*"])

# All creation events
client = Client(topics=["*.created"])

# Multiple patterns
client = Client(topics=["todo.*", "user.*", "order.placed"])
```

#### Subscribe with Sender Filtering
```python
# Only receive events from specific senders
client = Client(topics={
    "todo.*": ["user-123", "user-456"],  # Only these users' todo events
    "order.placed": ["system"]            # Only system-generated orders
})
```

#### Mute Specific Topics
```python
# Subscribe to all user events except deleted
client = Client(
    topics=["user.*"],
    muted_topics=["user.deleted"]
)

# Mute multiple topics
client = Client(
    topics=["*"],
    muted_topics=["debug.*", "system.heartbeat"]
)
```

---

## Methods

### `subscribe(topic, senders=ANY)`

Subscribe to a topic after client creation.

**Parameters:**
- `topic` (str) - Topic pattern to subscribe to
- `senders` (list[str] | ANY, default: ANY) - Filter by specific senders

**Example:**
```python
client = Client()

# Subscribe to new topic
client.subscribe("user.login")

# Subscribe with sender filtering
client.subscribe("order.*", senders=["admin-user", "system"])
```

### `unsubscribe(topic)`

Unsubscribe from a topic.

**Parameters:**
- `topic` (str) - Topic to unsubscribe from

**Example:**
```python
client = Client(topics=["todo.*", "user.*"])

# Stop receiving user events
client.unsubscribe("user.*")
```

### `connect()`

Connect the client and start receiving events.

**Returns:** self (for chaining)

**Example:**
```python
client = Client(topics=["todo.*"])
client.connect()
# Client is now active
```

### `disconnect()`

Disconnect the client and cleanup resources.

**Returns:** self (for chaining)

**Example:**
```python
client.disconnect()
# Client no longer receives events
```

### `async stream(delay=0.1)`

Async generator that yields events from the queue.

**Parameters:**
- `delay` (float, default: 0.1) - Timeout in seconds for queue polling

**Yields:** Event data

**Example:**
```python
client = Client(topics=["todo.*"])
client.connect()

async for event_data in client.stream():
    print(f"Received: {event_data}")
```

### `send(item)`

Manually send an item to the client's queue.

**Parameters:**
- `item` - Data to send to client

**Returns:** bool (True if sent, False if client disconnected)

**Example:**
```python
# Send custom data to specific client
client = active_clients["client-123"]
success = client.send({"type": "notification", "message": "Hello!"})
```

---

## Context Manager

Client supports context manager protocol for automatic lifecycle management:

```python
async def event_stream():
    client = Client(topics=["todo.*"])

    # Automatically connects on enter, disconnects on exit
    with client:
        async for data in client.stream():
            yield f"data: {data}\n\n"
```

Equivalent to:
```python
async def event_stream():
    client = Client(topics=["todo.*"])
    client.connect()
    try:
        async for data in client.stream():
            yield f"data: {data}\n\n"
    finally:
        client.disconnect()
```

---

## Complete Examples

### Example 1: Todo App with Real-Time Updates

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.events import Client, event, emit
import json
import uuid

app = FastAPI()

# Define events
todo_created = event('todo.created')
todo_updated = event('todo.updated')
todo_deleted = event('todo.deleted')

# Entity
class Todo(Entity, table=True):
    title: str
    completed: bool = False

# Initialize database
Todo._repository.init_db()

# SSE endpoint
@app.get("/events")
async def events():
    """Real-time event stream"""
    client = Client(topics=["todo.*"])

    async def event_generator():
        with client:
            async for data in client.stream():
                yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

# CRUD endpoints that emit events
@app.post("/todos")
def create_todo(title: str):
    todo = Todo(id=str(uuid.uuid4()), title=title)
    todo.save()
    emit(todo_created, todo, result=todo.model_dump())
    return {"status": "created", "todo": todo.model_dump()}

@app.patch("/todos/{todo_id}")
def update_todo(todo_id: str, completed: bool):
    todo = Todo.get(todo_id)
    if not todo:
        return {"error": "Not found"}, 404

    todo.completed = completed
    todo.save()
    emit(todo_updated, todo, result=todo.model_dump())
    return {"status": "updated", "todo": todo.model_dump()}

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: str):
    todo = Todo.get(todo_id)
    if not todo:
        return {"error": "Not found"}, 404

    todo.delete()
    emit(todo_deleted, todo, result={"id": todo_id})
    return {"status": "deleted"}

# Get all todos
@app.get("/todos")
def get_todos():
    return {"todos": [t.model_dump() for t in Todo.all()]}
```

**Frontend (JavaScript):**
```javascript
// Connect to SSE
const eventSource = new EventSource('/events');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // Update UI based on event
    if (data.id && data.title) {
        // Todo created or updated
        updateTodoInUI(data);
    } else if (data.id) {
        // Todo deleted
        removeTodoFromUI(data.id);
    }
};

// Create todo
async function createTodo(title) {
    await fetch('/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `title=${encodeURIComponent(title)}`
    });
    // UI updates automatically via SSE
}

// Toggle todo
async function toggleTodo(id, completed) {
    await fetch(`/todos/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `completed=${completed}`
    });
    // UI updates automatically via SSE
}
```

### Example 2: Multi-User Chat with Room Filtering

```python
from fastapi import FastAPI
from nitro.infrastructure.events import Client, event, emit

app = FastAPI()

# Events for different rooms
message_sent = event('chat.message')

@app.get("/chat/events/{room_id}")
async def chat_events(room_id: str):
    """SSE endpoint for specific chat room"""
    # Only receive messages from this room
    client = Client(topics={
        "chat.message": [room_id]
    })

    async def event_generator():
        with client:
            async for data in client.stream():
                yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.post("/chat/{room_id}/send")
def send_message(room_id: str, username: str, message: str):
    """Send message to room"""
    msg_data = {
        "room": room_id,
        "username": username,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

    # Emit with room_id as sender (for filtering)
    emit(message_sent, room_id, result=msg_data)

    return {"status": "sent"}
```

### Example 3: Live Dashboard with Multiple Data Streams

```python
from fastapi import FastAPI
from nitro.infrastructure.events import Client, event, emit

app = FastAPI()

# Multiple event types
order_placed = event('analytics.order-placed')
user_registered = event('analytics.user-registered')
revenue_updated = event('analytics.revenue')

@app.get("/dashboard/events")
async def dashboard_events(user_role: str = "viewer"):
    """SSE endpoint with role-based filtering"""
    if user_role == "admin":
        # Admins see everything
        topics = ["analytics.*"]
    else:
        # Viewers see limited data
        topics = ["analytics.order-placed", "analytics.user-registered"]

    client = Client(topics=topics)

    async def event_generator():
        with client:
            async for data in client.stream():
                yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

# Background task that emits metrics
from apscheduler.schedulers.background import BackgroundScheduler

def emit_metrics():
    """Called every 5 seconds"""
    revenue = calculate_total_revenue()
    emit(revenue_updated, "system", result={"revenue": revenue})

scheduler = BackgroundScheduler()
scheduler.add_job(emit_metrics, 'interval', seconds=5)
scheduler.start()
```

---

## Active Clients Tracking

The Client class maintains a global registry of active clients:

```python
from nitro.infrastructure.events.client import active_clients

# Get all connected clients
print(f"Active clients: {len(active_clients)}")

# Send to specific client
client = active_clients.get("client-123")
if client:
    client.send({"notification": "Hello!"})

# Broadcast to all clients
for client_id, client in active_clients.items():
    client.send({"broadcast": "Server restarting in 5 minutes"})
```

---

## Lifecycle Events

The Client class emits lifecycle events that you can monitor:

```python
from nitro.infrastructure.events import on
from nitro.infrastructure.events.client import client_event

@on(client_event)
def monitor_clients(sender, action, client, **kwargs):
    if action == "connect":
        print(f"📡 Client {client.client_id} connected")
        print(f"   Topics: {client.topics}")
    elif action == "disconnect":
        print(f"📡 Client {client.client_id} disconnected")
```

---

## Best Practices

### Always Use Context Manager

```python
# ✅ Good - automatic cleanup
async def event_stream():
    client = Client(topics=["todo.*"])
    with client:
        async for data in client.stream():
            yield data

# ❌ Avoid - manual management
async def event_stream():
    client = Client(topics=["todo.*"])
    client.connect()
    async for data in client.stream():
        yield data
    # Disconnect may not happen on error!
```

### Include Result Data in Events

```python
# ✅ Good - include data in emit
emit(todo_created, todo, result=todo.model_dump())

# ❌ Avoid - clients get no data
emit(todo_created, todo)
```

### Use Specific Topics

```python
# ✅ Good - specific, efficient
client = Client(topics=["todo.created", "todo.updated"])

# ❌ Avoid - too broad, wasteful
client = Client(topics=["*"])
```

### Handle Disconnections Gracefully

```python
@app.get("/events")
async def events():
    client = Client(topics=["todo.*"])

    async def event_generator():
        try:
            with client:
                async for data in client.stream():
                    yield f"data: {json.dumps(data)}\n\n"
        except Exception as e:
            print(f"Client {client.client_id} error: {e}")
            # Client auto-disconnects via context manager

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

### Client-Side Reconnection

```javascript
// ✅ Good - auto-reconnect on error
function connectSSE() {
    const eventSource = new EventSource('/events');

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleUpdate(data);
    };

    eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        eventSource.close();

        // Reconnect after 3 seconds
        setTimeout(connectSSE, 3000);
    };
}

connectSSE();
```

---

## Troubleshooting

### No Events Received

Check that:
1. Client topics match emitted event names
2. Event includes `result` parameter: `emit(event, sender, result=data)`
3. SSE endpoint is not buffered by proxy/nginx
4. Frontend EventSource is connected

### Memory Leaks

Always disconnect clients:
```python
# ✅ Use context manager
with client:
    async for data in client.stream():
        yield data

# ✅ Or disconnect in finally
try:
    client.connect()
    async for data in client.stream():
        yield data
finally:
    client.disconnect()
```

### Events Delayed

Reduce `stream()` delay parameter:
```python
# Faster polling (more CPU usage)
async for data in client.stream(delay=0.01):
    yield data

# Default polling
async for data in client.stream(delay=0.1):
    yield data
```

---

## Next Steps

- **[Backend Events →](backend-events.md)** - Event system API reference
- **[Events Overview →](overview.md)** - Event-driven architecture philosophy
- **[Datastar SSE →](../frontend/datastar/sse-integration.md)** - Frontend SSE integration

---

## Related Documentation

- **[FastAPI Integration →](../frameworks/fastapi.md)** - FastAPI-specific patterns
- **[Starlette Integration →](../frameworks/starlette.md)** - Starlette SSE endpoints
