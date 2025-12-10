"""
FastHTML Counter Example with Auto-Routing

Demonstrates Nitro's auto-routing system with FastHTML.
Entity methods decorated with @action are automatically
registered as FastHTML routes.

Routes auto-generated:
    POST   /counter/{id}/increment
    POST   /counter/{id}/decrement
    POST   /counter/{id}/reset
    GET    /counter/{id}/status
"""

import sys
from pathlib import Path

# Add parent directory to path to import local nitro
nitro_path = Path(__file__).parent.parent
sys.path.insert(0, str(nitro_path))

from fasthtml.common import *
from nitro import Entity, action
from nitro.adapters.fasthtml import configure_nitro
from nitro.infrastructure.repository.sql import SQLModelRepository
from rusty_tags import Div, H1, H2, P, Button, Span, Br, Pre
from nitro.infrastructure.html import Page


class Counter(Entity, table=True):
    """Counter entity with auto-routed actions."""

    count: int = 0
    name: str = "Counter"

    model_config = {
        "repository_class": SQLModelRepository
    }

    @action(method="POST", summary="Increment counter")
    def increment(self, amount: int = 1):
        """Increment the counter by the specified amount."""
        self.count += amount
        self.save()
        return {
            "count": self.count,
            "message": f"Incremented by {amount}"
        }

    @action(method="POST", summary="Decrement counter")
    def decrement(self, amount: int = 1):
        """Decrement the counter by the specified amount."""
        self.count -= amount
        self.save()
        return {
            "count": self.count,
            "message": f"Decremented by {amount}"
        }

    @action(method="POST", summary="Reset counter")
    def reset(self):
        """Reset the counter to zero."""
        self.count = 0
        self.save()
        return {
            "count": self.count,
            "message": "Counter reset to 0"
        }

    @action(method="GET", summary="Get counter status")
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

# Configure Nitro auto-routing (only register this Counter, not all discovered entities)
configure_nitro(rt, entities=[Counter], auto_discover=False)

# Manual homepage route
@rt("/")
def homepage():
    """Homepage with counter info."""
    counter = Counter.get("demo")
    count_value = counter.count if counter else 0

    page_content = Page(
        Div(
            H1("FastHTML Counter with Nitro Auto-Routing", class_="text-4xl font-bold text-indigo-600 mb-4"),
            H2(f"Current Count: {count_value}", class_="text-3xl mb-6"),

            # Counter controls
            Div(
                Button("➕ Increment",
                       class_="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded mr-2",
                       onclick="fetch('/counter/demo/increment', {method: 'POST'}).then(() => location.reload())"),
                Button("➖ Decrement",
                       class_="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded mr-2",
                       onclick="fetch('/counter/demo/decrement', {method: 'POST'}).then(() => location.reload())"),
                Button("🔄 Reset",
                       class_="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded",
                       onclick="fetch('/counter/demo/reset', {method: 'POST'}).then(() => location.reload())"),
                class_="mb-8"
            ),

            # API Routes
            H2("Auto-Generated API Routes:", class_="text-2xl mb-4"),
            Pre("""POST /counter/{id}/increment
POST /counter/{id}/decrement
POST /counter/{id}/reset
GET  /counter/{id}/status""",
                class_="bg-gray-100 p-4 rounded"),

            Br(),
            P("Example: ", class_="text-sm text-gray-600"),
            Pre("""curl -X POST http://localhost:8092/counter/demo/increment
curl -X GET http://localhost:8092/counter/demo/status""",
                class_="bg-gray-100 p-2 rounded text-xs"),

            class_="container mx-auto p-8"
        ),
        title="FastHTML Counter - Nitro Auto-Routing"
    )

    return str(page_content)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FastHTML Counter App with Nitro Auto-Routing")
    print("="*60)
    print("\nAuto-generated routes:")
    print("  POST   /counter/<id>/increment")
    print("  POST   /counter/<id>/decrement")
    print("  POST   /counter/<id>/reset")
    print("  GET    /counter/<id>/status")
    print("  GET    /")
    print("\n" + "="*60)
    print("Server starting on http://0.0.0.0:8093")
    print("="*60 + "\n")

    # Run FastHTML app (reload=False to avoid route duplication)
    serve(port=8093, reload=False)
