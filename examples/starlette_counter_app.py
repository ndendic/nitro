"""
Starlette Integration Example - Counter App with Nitro Entity and Events

This example demonstrates:
1. Using Nitro Entity with Starlette
2. Event system with async handlers
3. RustyTags HTML generation with Datastar
4. Async route handlers

Run: uvicorn examples.starlette_counter_app:app --reload
Then visit: http://localhost:8000
"""

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.events.events import event, on, emit, emit_async
from nitro.infrastructure.html import Page
from rusty_tags import Div, H1, H2, P, Button, Br
from nitro.infrastructure.html.datastar import Signals


# Define Counter Entity
class Counter(Entity, table=True):
    """Counter entity with persistence."""
    name: str
    count: int = 0

    async def increment(self) -> None:
        """Increment counter and emit event."""
        self.count += 1
        self.save()
        # Emit async event
        await emit_async("counter.incremented", sender=self)

    async def decrement(self) -> None:
        """Decrement counter and emit event."""
        self.count -= 1
        self.save()
        # Emit async event
        await emit_async("counter.decremented", sender=self)

    async def reset(self) -> None:
        """Reset counter to zero."""
        self.count = 0
        self.save()
        await emit_async("counter.reset", sender=self)


# Event handlers
@on("counter.incremented")
async def log_increment(sender: Counter, **kwargs):
    """Log when counter is incremented."""
    print(f"✓ Counter '{sender.name}' incremented to {sender.count}")


@on("counter.decremented")
async def log_decrement(sender: Counter, **kwargs):
    """Log when counter is decremented."""
    print(f"✓ Counter '{sender.name}' decremented to {sender.count}")


@on("counter.reset")
async def log_reset(sender: Counter, **kwargs):
    """Log when counter is reset."""
    print(f"✓ Counter '{sender.name}' reset to 0")


# Routes
async def homepage(request):
    """Homepage with counter."""
    # Get or create counter
    counter = Counter.get("main")
    if not counter:
        counter = Counter(id="main", name="Main Counter", count=0)
        counter.save()

    # Build page with Datastar
    signals = Signals(count=counter.count)

    page_content = Page(
        Div(
            H1("Starlette + Nitro Counter", class_="text-4xl font-bold text-blue-600 mb-4"),
            H2("Counter Demo", class_="text-2xl mb-6"),
            P(f"Counter: {counter.count}", class_="text-xl mb-4 font-mono"),

            Div(
                Button(
                    "Increment",
                    class_="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mr-2",
                    onclick="fetch('/increment').then(r => r.json()).then(d => location.reload())"
                ),
                Button(
                    "Decrement",
                    class_="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded mr-2",
                    onclick="fetch('/decrement').then(r => r.json()).then(d => location.reload())"
                ),
                Button(
                    "Reset",
                    class_="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded",
                    onclick="fetch('/reset').then(r => r.json()).then(d => location.reload())"
                ),
                class_="mb-6"
            ),

            Br(),
            P("Entity ID: " + counter.id, class_="text-sm text-gray-600"),
            P("Entity Name: " + counter.name, class_="text-sm text-gray-600"),

            class_="container mx-auto p-8"
        ),
        title="Starlette + Nitro Counter",
        tailwind4=True
    )

    return HTMLResponse(str(page_content))


async def increment_endpoint(request):
    """Increment counter endpoint."""
    counter = Counter.get("main")
    if counter:
        await counter.increment()
        return JSONResponse({"count": counter.count, "status": "incremented"})
    return JSONResponse({"error": "Counter not found"}, status_code=404)


async def decrement_endpoint(request):
    """Decrement counter endpoint."""
    counter = Counter.get("main")
    if counter:
        await counter.decrement()
        return JSONResponse({"count": counter.count, "status": "decremented"})
    return JSONResponse({"error": "Counter not found"}, status_code=404)


async def reset_endpoint(request):
    """Reset counter endpoint."""
    counter = Counter.get("main")
    if counter:
        await counter.reset()
        return JSONResponse({"count": counter.count, "status": "reset"})
    return JSONResponse({"error": "Counter not found"}, status_code=404)


async def status_endpoint(request):
    """Get counter status."""
    counter = Counter.get("main")
    if counter:
        return JSONResponse({
            "id": counter.id,
            "name": counter.name,
            "count": counter.count
        })
    return JSONResponse({"error": "Counter not found"}, status_code=404)


# Startup/Shutdown
async def startup():
    """Initialize database tables."""
    from nitro.infrastructure.repository.sql import SQLModelRepository

    # Initialize database
    repo = SQLModelRepository()
    repo.init_db()
    print("✓ Database initialized")
    print("✓ Starlette app started")


async def shutdown():
    """Cleanup on shutdown."""
    print("✓ Starlette app shutdown")


# Create Starlette app
routes = [
    Route("/", endpoint=homepage),
    Route("/increment", endpoint=increment_endpoint, methods=["GET", "POST"]),
    Route("/decrement", endpoint=decrement_endpoint, methods=["GET", "POST"]),
    Route("/reset", endpoint=reset_endpoint, methods=["GET", "POST"]),
    Route("/status", endpoint=status_endpoint),
]

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
]

app = Starlette(
    debug=True,
    routes=routes,
    middleware=middleware,
    on_startup=[startup],
    on_shutdown=[shutdown]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
