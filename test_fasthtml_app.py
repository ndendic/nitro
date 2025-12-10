"""
FastHTML Counter Test App - Port 8094
Modified to test the fixed FastHTML adapter.
"""

import sys
from pathlib import Path

# Add parent directory to path to import local nitro
nitro_path = Path(__file__).parent
sys.path.insert(0, str(nitro_path))

from fasthtml.common import *
from nitro import Entity, action
from nitro.adapters.fasthtml import configure_nitro
from nitro.infrastructure.repository.sql import SQLModelRepository


class TestCounter(Entity, table=True):
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
TestCounter.repository().init_db()

# Create demo counter if it doesn't exist
if not TestCounter.get("demo"):
    TestCounter(id="demo", name="Demo Counter", count=0).save()

# Create FastHTML app
app, rt = fast_app()

# Configure Nitro auto-routing (only register this Counter, not all discovered entities)
configure_nitro(rt, entities=[TestCounter], auto_discover=False)

# Manual homepage route
@rt("/")
def homepage():
    """Homepage with counter info."""
    return "FastHTML Counter Test App - Port 8094"


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FastHTML Counter Test App - Port 8094")
    print("="*60)
    print("\nAuto-generated routes:")
    print("  POST   /testcounter/<id>/increment")
    print("  POST   /testcounter/<id>/decrement")
    print("  POST   /testcounter/<id>/reset")
    print("  GET    /testcounter/<id>/status")
    print("  GET    /")
    print("\n" + "="*60)
    print("Server starting on http://0.0.0.0:8094")
    print("="*60 + "\n")

    # Run FastHTML app (reload=False to avoid route duplication)
    serve(port=8094, reload=False)
