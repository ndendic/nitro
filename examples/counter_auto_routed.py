"""
Proof-of-Concept: Auto-Routed Counter App with Nitro Phase 2

This example demonstrates the 75% code reduction achieved by auto-routing.

BEFORE (Manual Routing): ~190 lines
AFTER (Auto-Routing): ~45 lines

The @action decorator automatically generates:
- POST /counter/{id}/increment?amount=1
- POST /counter/{id}/decrement?amount=1
- POST /counter/{id}/reset
- GET  /counter/{id}/status

No manual route handlers needed!
"""

from fastapi import FastAPI
from nitro import Entity, action
from nitro.adapters.fastapi import configure_nitro
from nitro.infrastructure.repository.sql import SQLModelRepository


# ============================================================================
# ENTITY DEFINITION (with auto-routing)
# ============================================================================

class Counter(Entity, table=True):
    """Counter entity with auto-routed actions."""

    count: int = 0
    name: str = "Counter"

    model_config = {
        "repository_class": SQLModelRepository
    }

    @action(method="POST", summary="Increment counter")
    async def increment(self, amount: int = 1):
        """Increment the counter by the specified amount."""
        self.count += amount
        self.save()
        return {"count": self.count, "message": f"Incremented by {amount}"}

    @action(method="POST", summary="Decrement counter")
    async def decrement(self, amount: int = 1):
        """Decrement the counter by the specified amount."""
        self.count -= amount
        self.save()
        return {"count": self.count, "message": f"Decremented by {amount}"}

    @action(method="POST", summary="Reset counter")
    async def reset(self):
        """Reset the counter to zero."""
        self.count = 0
        self.save()
        return {"count": self.count, "message": "Reset to 0"}

    @action(method="GET", summary="Get counter status")
    def status(self):
        """Get the current counter status."""
        return {
            "id": self.id,
            "name": self.name,
            "count": self.count
        }


# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="Auto-Routed Counter App",
    description="Demonstration of Nitro Phase 2 auto-routing",
    version="1.0.0"
)

# Initialize database
Counter.repository().init_db()

# Create default counter if it doesn't exist
if not Counter.get("demo"):
    counter = Counter(id="demo", name="Demo Counter", count=0)
    counter.save()

# ONE LINE: Auto-register all @action methods as routes!
configure_nitro(app)


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🚀 Auto-Routed Counter App")
    print("="*70)
    print("\nAvailable routes (auto-generated):")
    print("  POST   /counter/{id}/increment?amount=1")
    print("  POST   /counter/{id}/decrement?amount=1")
    print("  POST   /counter/{id}/reset")
    print("  GET    /counter/{id}/status")
    print("\nOpenAPI docs: http://localhost:8090/docs")
    print("="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8090)
