"""
Flask Counter Example with Event-Driven Auto-Routing

Demonstrates Nitro's event-driven routing system with Flask.
Entity methods decorated with @post/@get are automatically
registered as Blinker event handlers, dispatched via catch-all routes.

Routes auto-generated:
    POST   /post/Counter:<id>.increment
    POST   /post/Counter:<id>.decrement
    POST   /post/Counter:<id>.reset
    GET    /get/Counter:<id>.status
"""

from flask import Flask
from nitro import Entity, get, post, action
from nitro.adapters.flask import configure_nitro


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


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)

    # Initialize database
    Counter.repository().init_db()

    # Create demo counter if it doesn't exist
    if not Counter.get("demo"):
        Counter(id="demo", name="Demo Counter", count=0).save()

    # Configure Nitro event-driven routing
    configure_nitro(app)

    # Add manual homepage route
    @app.route("/")
    def home():
        return {
            "message": "Flask Counter with Nitro Event-Driven Routing",
            "routes": {
                "POST /post/Counter:demo.increment": "Increment counter",
                "POST /post/Counter:demo.decrement": "Decrement counter",
                "POST /post/Counter:demo.reset": "Reset counter",
                "GET /get/Counter:demo.status": "Get counter status"
            },
            "example": "curl -X POST http://localhost:8091/post/Counter:demo.increment"
        }

    return app


if __name__ == "__main__":
    app = create_app()

    # Print registered routes
    print("\n" + "="*60)
    print("Flask Counter App with Nitro Event-Driven Routing")
    print("="*60)
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"  {methods:6} {rule.rule}")
    print("\n" + "="*60)
    print("Server starting on http://0.0.0.0:8091")
    print("="*60 + "\n")

    # Run Flask app
    app.run(host="0.0.0.0", port=8091, debug=False)
