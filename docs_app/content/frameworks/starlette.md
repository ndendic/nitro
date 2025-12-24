# Starlette Integration

Nitro provides SSE (Server-Sent Events) helpers for Starlette applications, enabling real-time updates with Datastar. Unlike FastAPI/Flask/FastHTML, Starlette integration focuses on event streaming rather than auto-routing (routes are typically defined manually in Starlette).

## Overview

Starlette integration provides:

- ✅ **SSE Helper Functions** - Emit HTML elements, signals, and scripts to clients
- ✅ **Client Management** - Topic-based subscriptions and automatic lifecycle handling
- ✅ **Datastar Integration** - Native support for Datastar SSE protocol
- ⚠️ **No Auto-Routing** - Routes must be defined manually (Starlette's design philosophy)

**Source:** `nitro/infrastructure/events/starlette.py`

## Quick Start

```python
from starlette.applications import Starlette
from starlette.responses import StreamingResponse
from starlette.routing import Route
from nitro.infrastructure.events import Client, emit
from nitro.infrastructure.events.starlette import emit_elements, emit_signals
from rusty_tags import Div, H1, Button
from rusty_tags.datastar import SSE

# SSE endpoint for real-time updates
async def sse_endpoint(request):
    """Stream server-sent events to client."""
    # Create client subscribed to "updates.*" topics
    client = Client(topics=["updates.*"])

    async def event_stream():
        with client:  # Auto-connect and disconnect
            async for data in client.stream():
                # Data is already formatted as SSE
                yield data

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )

# Trigger endpoint that emits updates
async def trigger_update(request):
    """Trigger an update to all connected clients."""
    # Emit HTML element to all clients subscribed to "updates.content"
    emit_elements(
        Div(
            H1("Updated!"),
            "Content was updated at " + str(request.state.timestamp)
        ),
        selector="#content",
        topic="updates.content"
    )
    return {"message": "Update sent"}

# Create Starlette app
app = Starlette(routes=[
    Route("/events", sse_endpoint),
    Route("/trigger", trigger_update, methods=["POST"]),
])
```

**HTML Client:**
```html
<div id="content" data-on-sse="/events">
    Loading...
</div>
<button onclick="fetch('/trigger', {method: 'POST'})">
    Trigger Update
</button>
```

## SSE Helper Functions

### emit_elements()

Emit HTML elements to connected clients.

**Source:** `nitro/infrastructure/events/starlette.py:19-37`

```python
def emit_elements(
    elements: str | _HtmlProvider,
    selector: str | None = None,
    mode: ElementPatchMode = ElementPatchMode.REPLACE,
    use_view_transition: bool | None = None,
    event_id: str | None = None,
    retry_duration: int | None = None,
    topic: str | list[str] | Any = ANY,
    sender: str | Any = ANY
):
    """
    Emit HTML elements to clients via SSE.

    Args:
        elements: HTML string or RustyTags element
        selector: CSS selector for target element (None = use element's id)
        mode: How to patch (REPLACE, MORPH, PREPEND, APPEND, BEFORE, AFTER)
        use_view_transition: Enable view transitions
        event_id: Custom event ID
        retry_duration: SSE retry duration in milliseconds
        topic: Topic(s) to emit to (default: ANY = all clients)
        sender: Sender identifier

    Returns:
        Formatted SSE data
    """
```

**Example:**

```python
from rusty_tags import Div, Span
from nitro.infrastructure.events.starlette import emit_elements
from datastar_py.consts import ElementPatchMode

# Replace element content
emit_elements(
    Div("New content!", id="message"),
    topic="updates.ui"
)

# Morph element (smart diff)
emit_elements(
    Div("Updated content", id="message"),
    mode=ElementPatchMode.MORPH,
    topic="updates.ui"
)

# Prepend to list
emit_elements(
    Span("New item"),
    selector="#item-list",
    mode=ElementPatchMode.PREPEND,
    topic="updates.list"
)

# Append to list
emit_elements(
    Span("Another item"),
    selector="#item-list",
    mode=ElementPatchMode.APPEND,
    topic="updates.list"
)
```

### emit_signals()

Update Datastar signals on connected clients.

**Source:** `nitro/infrastructure/events/starlette.py:55-69`

```python
def emit_signals(
    signals: dict | str,
    *,
    event_id: str | None = None,
    only_if_missing: bool | None = None,
    retry_duration: int | None = None,
    topic: str | list[str] | Any = ANY,
    sender: str | Any = ANY
):
    """
    Emit signal updates to clients via SSE.

    Args:
        signals: Dict of signal names and values, or merge expression string
        event_id: Custom event ID
        only_if_missing: Only set signals that don't exist on client
        retry_duration: SSE retry duration in milliseconds
        topic: Topic(s) to emit to
        sender: Sender identifier
    """
```

**Example:**

```python
from nitro.infrastructure.events.starlette import emit_signals

# Update multiple signals
emit_signals(
    {"counter": 42, "message": "Updated!"},
    topic="updates.state"
)

# Update single signal
emit_signals(
    {"user.name": "John Doe"},
    topic="updates.user"
)

# Merge expression (advanced)
emit_signals(
    "counter: $counter + 1",
    topic="updates.increment"
)
```

### remove_elements()

Remove elements from the DOM.

**Source:** `nitro/infrastructure/events/starlette.py:39-53`

```python
def remove_elements(
    selector: str,
    event_id: str | None = None,
    retry_duration: int | None = None,
    topic: str | list[str] | Any = ANY,
    sender: str | Any = ANY
):
    """
    Remove elements from the DOM via SSE.

    Args:
        selector: CSS selector for elements to remove
        event_id: Custom event ID
        retry_duration: SSE retry duration
        topic: Topic(s) to emit to
        sender: Sender identifier
    """
```

**Example:**

```python
from nitro.infrastructure.events.starlette import remove_elements

# Remove single element
remove_elements("#modal", topic="updates.ui")

# Remove multiple elements
remove_elements(".notification", topic="updates.notifications")
```

### execute_script()

Execute JavaScript on connected clients.

**Source:** `nitro/infrastructure/events/starlette.py:71-86`

```python
def execute_script(
    script: str,
    *,
    auto_remove: bool = True,
    attributes: Mapping[str, str] | list[str] | None = None,
    event_id: str | None = None,
    retry_duration: int | None = None,
    topic: str | list[str] | Any = ANY,
    sender: str | Any = ANY
):
    """
    Execute JavaScript on clients via SSE.

    Args:
        script: JavaScript code to execute
        auto_remove: Remove script element after execution
        attributes: Script tag attributes
        event_id: Custom event ID
        retry_duration: SSE retry duration
        topic: Topic(s) to emit to
        sender: Sender identifier
    """
```

**Example:**

```python
from nitro.infrastructure.events.starlette import execute_script

# Simple alert
execute_script(
    "alert('Update complete!')",
    topic="updates.notifications"
)

# Complex script
execute_script(
    """
    console.log('Processing update...');
    localStorage.setItem('lastUpdate', Date.now());
    """,
    topic="updates.system"
)
```

### redirect()

Redirect clients to a different URL.

**Source:** `nitro/infrastructure/events/starlette.py:88-94`

```python
def redirect(
    location: str,
    topic: str | list[str] | Any = ANY,
    sender: str | Any = ANY
):
    """
    Redirect clients to a new URL.

    Args:
        location: Target URL
        topic: Topic(s) to emit to
        sender: Sender identifier
    """
```

**Example:**

```python
from nitro.infrastructure.events.starlette import redirect

# Redirect all clients
redirect("/dashboard", topic="updates.navigation")

# Redirect specific topic subscribers
redirect("/login", topic="auth.session_expired")
```

## Client Management

The `Client` class manages individual client connections with automatic lifecycle handling.

**Source:** `nitro/infrastructure/events/client.py:11-126`

### Creating Clients

```python
from nitro.infrastructure.events import Client, ANY

# Subscribe to all topics
client = Client(topics=ANY)

# Subscribe to specific topics
client = Client(topics=["updates.*", "notifications.*"])

# Subscribe to topics with specific senders
client = Client(topics={
    "orders.*": ["user-123"],
    "notifications.*": ANY
})

# Subscribe with muted topics
client = Client(
    topics=["updates.*"],
    muted_topics=["updates.debug"]
)
```

### Client Lifecycle

```python
# Manual connect/disconnect
client = Client(topics=["updates.*"])
client.connect()
# ... do work ...
client.disconnect()

# Context manager (recommended)
with Client(topics=["updates.*"]) as client:
    async for data in client.stream():
        yield data
    # Auto-disconnects when exiting context
```

### Streaming Events

```python
async def sse_endpoint(request):
    client = Client(topics=["updates.*"])

    async def event_stream():
        with client:
            async for event_data in client.stream(delay=0.1):
                # event_data is pre-formatted SSE data
                yield event_data

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
```

## Topic-Based Subscriptions

Topics use wildcard patterns for flexible subscriptions:

```python
# Exact match
client = Client(topics=["user.login"])

# Wildcard patterns
client = Client(topics=["user.*"])  # Matches user.login, user.logout, etc.

# Multiple topics
client = Client(topics=["user.*", "order.*", "notifications.*"])

# All topics
from nitro.infrastructure.events import ANY
client = Client(topics=ANY)
```

### Emitting to Topics

```python
from nitro.infrastructure.events.starlette import emit_elements
from rusty_tags import Div

# Emit to specific topic
emit_elements(
    Div("Update!"),
    topic="user.profile.updated"
)

# Emit to multiple topics
emit_elements(
    Div("Alert!"),
    topic=["notifications.alerts", "ui.updates"]
)

# Emit to all clients
emit_elements(
    Div("Global announcement"),
    topic=ANY
)
```

## Complete Example

Here's a complete Starlette application with SSE updates:

```python
from starlette.applications import Starlette
from starlette.responses import StreamingResponse, JSONResponse, HTMLResponse
from starlette.routing import Route
from nitro.infrastructure.events import Client, emit
from nitro.infrastructure.events.starlette import (
    emit_elements,
    emit_signals,
    remove_elements
)
from rusty_tags import Div, H1, Ul, Li, Button
import asyncio

# --- SSE Endpoint ---

async def sse_events(request):
    """Stream server-sent events to client."""
    # Create client subscribed to chat updates
    client = Client(topics=["chat.*"])

    async def event_stream():
        with client:
            async for data in client.stream():
                yield data

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )

# --- HTTP Endpoints ---

async def send_message(request):
    """Send a chat message to all connected clients."""
    data = await request.json()
    message = data.get("message", "")

    # Emit new message to all chat clients
    emit_elements(
        Li(message, cls="chat-message"),
        selector="#messages",
        mode="append",
        topic="chat.messages"
    )

    # Update message count signal
    emit_signals(
        {"messageCount": "$messageCount + 1"},
        topic="chat.state"
    )

    return JSONResponse({"status": "sent"})

async def clear_messages(request):
    """Clear all messages."""
    # Remove all message elements
    remove_elements(".chat-message", topic="chat.messages")

    # Reset counter
    emit_signals({"messageCount": 0}, topic="chat.state")

    return JSONResponse({"status": "cleared"})

async def homepage(request):
    """Render HTML homepage."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat App</title>
        <script src="https://cdn.jsdelivr.net/npm/@datastar-js/browser/dist/datastar.min.js"></script>
    </head>
    <body>
        <h1>Chat Room</h1>
        <div data-on-sse="/events">
            <div data-signals='{"messageCount": 0}'>
                <p>Messages: <span data-text="$messageCount"></span></p>
            </div>
            <ul id="messages"></ul>
            <input id="message-input" type="text" placeholder="Type a message...">
            <button onclick="sendMessage()">Send</button>
            <button onclick="clearMessages()">Clear</button>
        </div>

        <script>
        function sendMessage() {
            const input = document.getElementById('message-input');
            fetch('/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: input.value})
            });
            input.value = '';
        }

        function clearMessages() {
            fetch('/clear', {method: 'POST'});
        }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

# --- Application ---

app = Starlette(routes=[
    Route("/", homepage),
    Route("/events", sse_events),
    Route("/send", send_message, methods=["POST"]),
    Route("/clear", clear_messages, methods=["POST"]),
])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Integration with Nitro Entities

Combine SSE updates with Nitro entities:

```python
from starlette.applications import Starlette
from starlette.routing import Route
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.infrastructure.events import Client, event, on
from nitro.infrastructure.events.starlette import emit_elements
from rusty_tags import Li

# Define entity
class Task(Entity, table=True):
    title: str
    completed: bool = False

# Event handler
task_created = event("task.created")

@on(task_created)
async def broadcast_new_task(sender, **kwargs):
    """Broadcast new task to all connected clients."""
    task = sender
    emit_elements(
        Li(f"{task.title} - {'✓' if task.completed else '○'}"),
        selector="#task-list",
        mode="append",
        topic="tasks.updates"
    )

# SSE endpoint
async def sse_events(request):
    client = Client(topics=["tasks.*"])
    async def stream():
        with client:
            async for data in client.stream():
                yield data
    return StreamingResponse(stream(), media_type="text/event-stream")

# Create task endpoint
async def create_task(request):
    data = await request.json()
    task = Task(title=data["title"])
    task.save()
    task_created.emit(task)
    return JSONResponse({"id": task.id})

app = Starlette(routes=[
    Route("/events", sse_events),
    Route("/tasks", create_task, methods=["POST"]),
])
```

## Next Steps

- **[Framework Overview](./overview.md)** - Framework-agnostic design
- **[Backend Events](../events/backend-events.md)** - Event system details
- **[Datastar SSE Integration](../frontend/datastar/sse-integration.md)** - Datastar protocol

## Related Frameworks

- **[FastAPI Integration](./fastapi.md)** - Auto-routing with OpenAPI
- **[FastHTML Integration](./fasthtml.md)** - HTML-first applications
- **[Flask Integration](./flask.md)** - Traditional Python framework
