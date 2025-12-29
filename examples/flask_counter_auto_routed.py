"""
Flask Counter Example with Auto-Routing

Demonstrates Nitro's auto-routing system with Flask.
Entity methods decorated with @action are automatically
registered as Flask routes.

Routes auto-generated:
    POST   /counter/<id>/increment
    POST   /counter/<id>/decrement
    POST   /counter/<id>/reset
    GET    /counter/<id>/status
"""

import sys
from pathlib import Path

# Add parent directory to path to import local nitro
nitro_path = Path(__file__).parent.parent
sys.path.insert(0, str(nitro_path))

from flask import Flask
from nitro import Entity, action
from nitro.adapters.flask import configure_nitro
from nitro.infrastructure.repository.sql import SQLModelRepository


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


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)

    # Initialize database
    Counter.repository().init_db()

    # Create demo counter if it doesn't exist
    if not Counter.get("demo"):
        Counter(id="demo", name="Demo Counter", count=0).save()

    # Configure Nitro auto-routing
    configure_nitro(app)

    # Add manual homepage route
    @app.route("/")
    def home():
        return {
            "message": "Flask Counter with Nitro Auto-Routing",
            "routes": {
                "POST /counter/<id>/increment": "Increment counter",
                "POST /counter/<id>/decrement": "Decrement counter",
                "POST /counter/<id>/reset": "Reset counter",
                "GET /counter/<id>/status": "Get counter status"
            },
            "example": "curl -X POST http://localhost:8091/counter/demo/increment"
        }

    return app


if __name__ == "__main__":
    app = create_app()

    # Print registered routes
    print("\n" + "="*60)
    print("Flask Counter App with Nitro Auto-Routing")
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
