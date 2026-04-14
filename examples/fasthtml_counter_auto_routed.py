"""
FastHTML Counter Example with Event-Driven Routing

Demonstrates Nitro's event-driven routing system with FastHTML.
Entity methods decorated with @post/@get are automatically
registered as Blinker event handlers. The Starlette adapter
(used by FastHTML) provides catch-all endpoints that dispatch
to those handlers.

Requires: pip install python-fasthtml

Routes auto-generated:
    POST   /post/Counter:demo.increment
    POST   /post/Counter:demo.decrement
    POST   /post/Counter:demo.reset
    GET    /get/Counter:demo.status
"""
import os
os.environ.setdefault("NITRO_DB_URL", "sqlite:///fh_counter.db")


from fasthtml.common import *
from nitro import Entity, get, post, action
from nitro.adapters.starlette import configure_nitro
from rusty_tags import Div, H1, H2, P, Button, Span, Br, Pre
from nitro.html import Page


class Counter(Entity, table=True):
    """Counter entity with event-driven routed actions."""

    count: int = 0
    name: str = "Counter"

    @post(summary="Increment counter")
    def increment(self, amount: int = 1):
        """Increment the counter by the specified amount."""
        self.count += amount
        self.save()
        return {
            "count": self.count,
            "message": f"Incremented by {amount}"
        }

    @post(summary="Decrement counter")
    def decrement(self, amount: int = 1):
        """Decrement the counter by the specified amount."""
        self.count -= amount
        self.save()
        return {
            "count": self.count,
            "message": f"Decremented by {amount}"
        }

    @post(summary="Reset counter")
    def reset(self):
        """Reset the counter to zero."""
        self.count = 0
        self.save()
        return {
            "count": self.count,
            "message": "Counter reset to 0"
        }

    @get(summary="Get counter status")
    def status(self):
        """Get the current counter status."""
        return {
            "id": self.id,
            "name": self.name,
            "count": self.count
        }


# Initialize database
Counter.repository().init_db()

# Create demo counter if it doesn't exist
if not Counter.get("demo"):
    Counter(id="demo", name="Demo Counter", count=0).save()

# Create FastHTML app
app, rt = fast_app()

# Configure Nitro event-driven routing (Starlette catch-all endpoints)
configure_nitro(app)

# Manual homepage route
@rt("/")
def homepage():
    """Homepage with counter info."""
    counter = Counter.get("demo")
    count_value = counter.count if counter else 0

    page_content = Page(
        Div(
            H1("FastHTML Counter with Nitro Event-Driven Routing", class_="text-4xl font-bold text-indigo-600 mb-4"),
            H2(f"Current Count: {count_value}", class_="text-3xl mb-6"),

            # Counter controls
            Div(
                Button("+ Increment",
                       class_="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded mr-2",
                       onclick="fetch('/post/Counter:demo.increment', {method: 'POST'}).then(() => location.reload())"),
                Button("- Decrement",
                       class_="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded mr-2",
                       onclick="fetch('/post/Counter:demo.decrement', {method: 'POST'}).then(() => location.reload())"),
                Button("Reset",
                       class_="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded",
                       onclick="fetch('/post/Counter:demo.reset', {method: 'POST'}).then(() => location.reload())"),
                class_="mb-8"
            ),

            # API Routes
            H2("Auto-Generated API Routes:", class_="text-2xl mb-4"),
            Pre("""POST /post/Counter:{id}.increment
POST /post/Counter:{id}.decrement
POST /post/Counter:{id}.reset
GET  /get/Counter:{id}.status""",
                class_="bg-gray-100 p-4 rounded"),

            Br(),
            P("Example: ", class_="text-sm text-gray-600"),
            Pre("""curl -X POST http://localhost:8093/post/Counter:demo.increment
curl -X GET http://localhost:8093/get/Counter:demo.status""",
                class_="bg-gray-100 p-2 rounded text-xs"),

            class_="container mx-auto p-8"
        ),
        title="FastHTML Counter - Nitro Event-Driven Routing"
    )

    return str(page_content)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FastHTML Counter App with Nitro Event-Driven Routing")
    print("="*60)
    print("\nAuto-generated routes:")
    print("  POST   /post/Counter:<id>.increment")
    print("  POST   /post/Counter:<id>.decrement")
    print("  POST   /post/Counter:<id>.reset")
    print("  GET    /get/Counter:<id>.status")
    print("  GET    /")
    print("\n" + "="*60)
    print("Server starting on http://0.0.0.0:8093")
    print("="*60 + "\n")

    # Run FastHTML app (reload=False to avoid route duplication)
    serve(port=8093, reload=False)
