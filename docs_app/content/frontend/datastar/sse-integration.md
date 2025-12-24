---
title: SSE Integration
category: Frontend
order: 8
---

# Datastar SSE Integration

This document covers Server-Sent Events (SSE) integration with Datastar for real-time server-to-client updates. SSE enables your backend to push HTML fragments, signal updates, script execution, and navigation commands to connected clients.

## Overview

Nitro provides a high-level API in `nitro.infrastructure.events.starlette` that wraps the underlying `datastar_py` SSE functionality. These helpers integrate seamlessly with Nitro's event system, allowing you to emit updates to specific topics or broadcast to all connected clients.

**Source:** `nitro/nitro/infrastructure/events/starlette.py`

---

## Core Concepts

### SSE Class

The `SSE` class from `rusty_tags.datastar` generates Server-Sent Event messages that Datastar clients understand.

```python
from rusty_tags.datastar import SSE

sse = SSE()
```

### Element Patch Modes

When updating the DOM, Datastar supports multiple merge strategies via `ElementPatchMode`:

- **`REPLACE`** (morph) - Intelligent DOM morphing (default) - preserves focus, scroll position
- **`INNER`** - Replace inner HTML only
- **`OUTER`** - Replace entire element including itself
- **`PREPEND`** - Insert before first child
- **`APPEND`** - Insert after last child
- **`BEFORE`** - Insert before element
- **`AFTER`** - Insert after element
- **`REMOVE`** - Delete element from DOM

```python
from datastar_py.consts import ElementPatchMode

# Use in emit_elements
emit_elements(sse, content, mode=ElementPatchMode.APPEND)
```

---

## Nitro SSE Helpers

All helpers accept `topic` and `sender` parameters for integration with Nitro's event bus. These parameters default to broadcasting to all topics (`ANY`).

### emit_elements()

Send HTML updates to the client. Elements are identified by their `id` attribute or via explicit `selector`.

**Signature:**
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
) -> str
```

**Basic Usage:**
```python
from nitro.infrastructure.events.starlette import emit_elements
from rusty_tags import Div, Span
from datastar_py.consts import ElementPatchMode

# Replace element by id (morph mode)
emit_elements(sse, Div("Updated content", id="target"))

# Append to a list
emit_elements(sse,
    Li("New todo item", id="item-5"),
    mode=ElementPatchMode.APPEND,
    selector="#todo-list"
)

# Multiple elements at once
emit_elements(sse,
    Div("First update", id="box-a"),
    Div("Second update", id="box-b")
)

# Prepend notification
emit_elements(sse,
    Div("New message", id="msg-123", cls="notification"),
    mode=ElementPatchMode.PREPEND,
    selector="#notification-area"
)
```

**With Event Bus Topics:**
```python
# Send to specific topic
emit_elements(sse,
    Div("Admin notification", id="admin-msg"),
    topic="admin.updates",
    sender="system"
)

# Broadcast to multiple topics
emit_elements(sse,
    Span(f"Count: {count}", id="counter"),
    topic=["dashboard.metrics", "sidebar.stats"]
)
```

---

### emit_signals()

Update signal values on the client side. This changes the reactive state without modifying the DOM directly.

**Signature:**
```python
def emit_signals(
    signals: dict | str,
    *,
    event_id: str | None = None,
    only_if_missing: bool | None = None,
    retry_duration: int | None = None,
    topic: str | list[str] | Any = ANY,
    sender: str | Any = ANY
) -> str
```

**Usage:**
```python
from nitro.infrastructure.events.starlette import emit_signals

# Update single signal
emit_signals(sse, count=42)

# Update multiple signals
emit_signals(sse,
    loading=False,
    data={"items": [1, 2, 3]},
    message="Updated successfully",
    timestamp=datetime.now().isoformat()
)

# Conditional update (only if signal doesn't exist)
emit_signals(sse,
    user_id="user-123",
    only_if_missing=True
)

# To specific topic
emit_signals(sse,
    score=95,
    rank=1,
    topic="leaderboard.updates"
)
```

**Client-side usage:**
```html
<!-- Signal values automatically update bound elements -->
<div data-text="$message"></div>
<input data-model="$count" type="number">
<span data-show="!$loading">Ready</span>
```

---

### remove_elements()

Delete elements from the DOM by selector.

**Signature:**
```python
def remove_elements(
    selector: str,
    event_id: str | None = None,
    retry_duration: int | None = None,
    topic: str | list[str] | Any = ANY,
    sender: str | Any = ANY
) -> str
```

**Usage:**
```python
from nitro.infrastructure.events.starlette import remove_elements

# Remove by ID
remove_elements(sse, "#notification-1")

# Remove multiple elements
remove_elements(sse, ".temp-item")

# Remove with topic targeting
remove_elements(sse, "#expired-session", topic="user.cleanup")

# Chain removals in SSE stream
remove_elements(sse, "#msg-1")
remove_elements(sse, "#msg-2")
remove_elements(sse, "#msg-3")
```

---

### execute_script()

Execute arbitrary JavaScript on the client. Use sparingly - prefer declarative approaches.

**Signature:**
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
) -> str
```

**Usage:**
```python
from nitro.infrastructure.events.starlette import execute_script

# Simple console log
execute_script(sse, "console.log('Update received')")

# Scroll to bottom
execute_script(sse, "window.scrollTo(0, document.body.scrollHeight)")

# Focus element
execute_script(sse, "document.getElementById('chat-input').focus()")

# Complex multi-line script
execute_script(sse, """
    const el = document.querySelector('.highlight');
    el.classList.add('flash');
    setTimeout(() => el.classList.remove('flash'), 300);
""")

# With custom attributes (e.g., nonce for CSP)
execute_script(sse,
    "initializeWidget()",
    attributes={"nonce": "abc123"}
)
```

---

### redirect()

Navigate the client to a different URL.

**Signature:**
```python
def redirect(
    location: str,
    topic: str | list[str] | Any = ANY,
    sender: str | Any = ANY
) -> str
```

**Usage:**
```python
from nitro.infrastructure.events.starlette import redirect

# Simple redirect
redirect(sse, "/dashboard")

# Redirect with query params
redirect(sse, "/login?next=/profile")

# Absolute URL
redirect(sse, "https://example.com/external")

# Conditional redirect (in your logic)
if user.is_authenticated:
    redirect(sse, "/app")
else:
    redirect(sse, "/login")
```

---

## Complete SSE Endpoint Examples

### Example 1: Basic Counter with FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from rusty_tags.datastar import SSE
from rusty_tags import Div, Span, Html, Body, Script
from nitro.infrastructure.events.starlette import emit_elements, emit_signals
import asyncio

app = FastAPI()

# Shared counter state
counter = {"value": 0}

@app.get("/")
def index():
    """Render the counter page."""
    return Html(
        Body(
            Div(
                Span(str(counter["value"]), id="counter-display"),
                # Connect to SSE endpoint on load
                data_on_load="@get('/sse')"
            ),
            Script(src="https://cdn.jsdelivr.net/npm/@sudodevnull/datastar")
        )
    )

@app.get("/sse")
async def sse_endpoint():
    """SSE stream that sends counter updates."""
    sse = SSE()

    async def event_generator():
        while True:
            await asyncio.sleep(1)
            counter["value"] += 1

            # Update both the DOM element and signal
            emit_elements(sse,
                Span(str(counter["value"]), id="counter-display")
            )
            emit_signals(sse, count=counter["value"])

            yield sse.flush()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )
```

### Example 2: Real-time Todo List with Event Bus

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from rusty_tags.datastar import SSE
from rusty_tags import Div, Li, Ul, Button, Input
from nitro.infrastructure.events import Client, emit
from nitro.infrastructure.events.starlette import emit_elements
from datastar_py.consts import ElementPatchMode
from typing import AsyncIterator

app = FastAPI()

@app.get("/todos/sse")
async def todos_sse():
    """SSE endpoint listening for todo updates."""
    client = Client(topics=["todos.*"])

    async def event_generator() -> AsyncIterator[str]:
        sse = SSE()
        with client:
            async for event in client.stream():
                event_type = event.get("type")

                if event_type == "todo_added":
                    # Append new todo to list
                    emit_elements(sse,
                        Li(event["text"], id=f"todo-{event['id']}"),
                        mode=ElementPatchMode.APPEND,
                        selector="#todo-list"
                    )

                elif event_type == "todo_removed":
                    # Remove todo from DOM
                    from nitro.infrastructure.events.starlette import remove_elements
                    remove_elements(sse, f"#todo-{event['id']}")

                elif event_type == "todo_updated":
                    # Update existing todo
                    emit_elements(sse,
                        Li(event["text"], id=f"todo-{event['id']}")
                    )

                yield sse.flush()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@app.post("/todos/add")
async def add_todo(text: str):
    """Add a new todo and broadcast to all clients."""
    todo_id = generate_id()

    # Emit event to all SSE clients
    emit("todos.added", sender="api", type="todo_added", id=todo_id, text=text)

    return {"status": "added", "id": todo_id}
```

### Example 3: Multi-room Chat with Topic Filtering

```python
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from rusty_tags.datastar import SSE
from rusty_tags import Div, Span
from nitro.infrastructure.events import Client
from nitro.infrastructure.events.starlette import emit_elements, emit_signals
from datastar_py.consts import ElementPatchMode

app = FastAPI()

@app.get("/chat/sse")
async def chat_sse(room: str = Query(...)):
    """SSE endpoint for a specific chat room."""
    # Subscribe only to events for this room
    client = Client(topics=[f"chat.{room}"])

    async def event_generator():
        sse = SSE()
        with client:
            async for event in client.stream():
                if event.get("type") == "message":
                    # Append message to chat
                    message_html = Div(
                        Span(event["username"], cls="username"),
                        Span(event["text"], cls="message-text"),
                        id=f"msg-{event['id']}",
                        cls="chat-message"
                    )

                    emit_elements(sse,
                        message_html,
                        mode=ElementPatchMode.APPEND,
                        selector="#chat-messages"
                    )

                    # Update message count signal
                    emit_signals(sse, message_count=event["total_count"])

                    # Auto-scroll to bottom
                    from nitro.infrastructure.events.starlette import execute_script
                    execute_script(sse,
                        "document.getElementById('chat-messages').scrollTop = 999999"
                    )

                yield sse.flush()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )

@app.post("/chat/{room}/send")
async def send_message(room: str, username: str, text: str):
    """Send message to specific room."""
    message_id = generate_id()

    # Emit to room-specific topic
    emit(f"chat.{room}",
         sender="api",
         type="message",
         id=message_id,
         username=username,
         text=text,
         total_count=get_message_count(room))

    return {"status": "sent"}
```

### Example 4: Progress Bar with Script Execution

```python
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import StreamingResponse
from rusty_tags.datastar import SSE
from rusty_tags import Div, Span
from nitro.infrastructure.events import Client
from nitro.infrastructure.events.starlette import emit_signals, execute_script, redirect
import asyncio

app = FastAPI()

@app.get("/job/sse")
async def job_progress_sse(job_id: str):
    """Monitor long-running job progress."""
    client = Client(topics=[f"job.{job_id}"])

    async def event_generator():
        sse = SSE()
        with client:
            async for event in client.stream():
                progress = event.get("progress", 0)

                # Update progress signal
                emit_signals(sse,
                    progress=progress,
                    status=event.get("status", "running")
                )

                # Flash progress bar on update
                execute_script(sse, """
                    const bar = document.querySelector('.progress-bar');
                    bar.classList.add('pulse');
                    setTimeout(() => bar.classList.remove('pulse'), 200);
                """)

                # Redirect when complete
                if event.get("status") == "complete":
                    await asyncio.sleep(0.5)  # Brief delay to show 100%
                    redirect(sse, f"/jobs/{job_id}/results")

                yield sse.flush()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )
```

---

## Best Practices

### 1. Always Set Cache-Control Headers

SSE connections must not be cached:

```python
return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"  # Nginx-specific
    }
)
```

### 2. Use Context Managers for Clients

Always use `with client:` to ensure proper cleanup:

```python
with client:
    async for event in client.stream():
        # Process events
        yield sse.flush()
```

### 3. Prefer Morphing Over Replace

`ElementPatchMode.REPLACE` (morph) is the smartest choice - it preserves:
- Input focus and cursor position
- Scroll position
- CSS animations
- Form state

### 4. Topic Naming Conventions

Use hierarchical topic names with dots:

```python
"users.created"        # Specific event
"users.*"              # All user events
"admin.notifications"  # Admin-only
"chat.room-42"         # Per-resource
```

### 5. Minimize Script Execution

Prefer declarative Datastar attributes over `execute_script()`:

```python
# ❌ Avoid
execute_script(sse, "document.getElementById('x').classList.add('active')")

# ✅ Better - use signals and data-class
emit_signals(sse, is_active=True)
# With: <div data-class.active="$is_active">
```

### 6. Handle Connection Drops

Clients may disconnect. Don't cache critical state only in SSE:

```python
async def event_generator():
    try:
        sse = SSE()
        with client:
            async for event in client.stream():
                yield sse.flush()
    except asyncio.CancelledError:
        # Client disconnected - cleanup
        logger.info("Client disconnected")
        raise
```

---

## Related Documentation

- [Datastar Signals](/frontend/datastar/signals) - Reactive state management
- [Datastar Attributes](/frontend/datastar/attributes) - DOM binding syntax
- [Datastar Helpers](/frontend/datastar/helpers) - JavaScript expression builders
- [Backend Events](/events/backend-events) - Event bus and Client class

---

## Reference

**Source Files:**
- `nitro/nitro/infrastructure/events/starlette.py` - Nitro SSE helpers
- `rusty_tags/datastar.py` - SSE class
- `datastar_py` - Underlying SSE implementation

**Key Classes:**
- `SSE` - Server-sent event generator
- `ElementPatchMode` - DOM update strategies
- `Client` - Event bus subscriber (for SSE endpoints)
