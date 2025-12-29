"""
Counter App Example - Demonstrates Nitro Features

This example demonstrates:
1. Entity with persistence
2. Reactive UI updates
3. Event-driven architecture
4. Simple CRUD operations

Run: uvicorn examples.counter_demo:app --reload --port 8001
Then visit: http://localhost:8001
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.events.events import on, emit_async
from nitro.infrastructure.html import Page
from rusty_tags import Div, H1, H2, P, Button, Span
from sqlmodel import Field


# Define Counter Entity
class Counter(Entity, table=True):
    """Counter entity with persistence."""
    name: str = Field(default="Counter")
    count: int = Field(default=0)

    model_config = {
        "repository_class": "nitro.infrastructure.repository.sql.SQLModelRepository"
    }

    async def increment(self) -> None:
        """Increment counter and emit event."""
        self.count += 1
        self.save()
        await emit_async("counter.incremented", sender=self)

    async def decrement(self) -> None:
        """Decrement counter and emit event."""
        self.count -= 1
        self.save()
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


# FastAPI app
app = FastAPI(title="Counter Demo")


@app.on_event("startup")
async def startup():
    """Initialize database."""
    from nitro.infrastructure.repository.sql import SQLModelRepository
    repo = SQLModelRepository()
    repo.init_db()
    print("✓ Database initialized")

    # Create initial counter if it doesn't exist
    counter = Counter.get("demo")
    if not counter:
        counter = Counter(id="demo", name="Demo Counter", count=0)
        counter.save()
        print("✓ Initial counter created")


@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Homepage with counter display."""
    counter = Counter.get("demo")
    if not counter:
        counter = Counter(id="demo", name="Demo Counter", count=0)
        counter.save()

    page = Page(
        Div(
            H1("Nitro Counter Example", class_="text-4xl font-bold text-blue-600 mb-6"),

            Div(
                P("Current Count:", class_="text-lg text-gray-700"),
                H2(str(counter.count), class_="text-6xl font-bold text-blue-500 my-4 font-mono"),
                class_="text-center mb-8"
            ),

            Div(
                Button(
                    "➕ Increment",
                    class_="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition-all mx-2",
                    onclick="fetch('/api/increment', {method: 'POST'}).then(() => location.reload())"
                ),
                Button(
                    "➖ Decrement",
                    class_="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition-all mx-2",
                    onclick="fetch('/api/decrement', {method: 'POST'}).then(() => location.reload())"
                ),
                Button(
                    "🔄 Reset",
                    class_="bg-gray-500 hover:bg-gray-600 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition-all mx-2",
                    onclick="fetch('/api/reset', {method: 'POST'}).then(() => location.reload())"
                ),
                class_="flex justify-center gap-4 mb-8"
            ),

            Div(
                P(f"Entity ID: {counter.id}", class_="text-sm text-gray-600"),
                P(f"Entity Name: {counter.name}", class_="text-sm text-gray-600"),
                P("State: Persisted to SQLite database", class_="text-sm text-green-600 font-semibold"),
                class_="mt-8 p-4 bg-gray-100 rounded"
            ),

            class_="container mx-auto p-8 max-w-2xl"
        ),
        title="Nitro Counter Demo",
        tailwind4=True
    )

    return str(page)


@app.post("/api/increment")
async def increment_counter():
    """Increment the counter."""
    counter = Counter.get("demo")
    if not counter:
        return JSONResponse({"error": "Counter not found"}, status_code=404)

    await counter.increment()
    return JSONResponse({"count": counter.count, "status": "incremented"})


@app.post("/api/decrement")
async def decrement_counter():
    """Decrement the counter."""
    counter = Counter.get("demo")
    if not counter:
        return JSONResponse({"error": "Counter not found"}, status_code=404)

    await counter.decrement()
    return JSONResponse({"count": counter.count, "status": "decremented"})


@app.post("/api/reset")
async def reset_counter():
    """Reset the counter to zero."""
    counter = Counter.get("demo")
    if not counter:
        return JSONResponse({"error": "Counter not found"}, status_code=404)

    await counter.reset()
    return JSONResponse({"count": counter.count, "status": "reset"})


@app.get("/api/status")
async def get_status():
    """Get counter status."""
    counter = Counter.get("demo")
    if not counter:
        return JSONResponse({"error": "Counter not found"}, status_code=404)

    return JSONResponse({
        "id": counter.id,
        "name": counter.name,
        "count": counter.count
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
