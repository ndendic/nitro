"""
Counter example using the event-driven action system.

Run: python examples/counter_auto_routed.py

Demonstrates:
- Entity with decorated methods (@post, @get)
- Automatic Blinker event registration via __init_subclass__
- action() helper for generating Datastar action strings
- Sanic catch-all endpoints for dispatch
"""
import os
os.environ.setdefault("NITRO_DB_URL", "sqlite:///counter_ar.db")

from sanic import Sanic
from sqlmodel import Field
from nitro import Entity, get, post, action
from nitro.adapters.sanic_adapter import configure_nitro

app = Sanic("CounterExample")


class Counter(Entity, table=True):
    __tablename__ = "counter"
    id: str = Field(primary_key=True)
    count: int = 0

    @post()
    async def increment(self, amount: int = 1):
        self.count += amount
        self.save()
        return {"count": self.count}

    @post()
    async def decrement(self, amount: int = 1):
        self.count -= amount
        self.save()
        return {"count": self.count}

    @get()
    def status(self):
        return {"count": self.count, "id": self.id}

    @get()
    @classmethod
    def list_all(cls):
        return [c.model_dump() for c in cls.all()]


# UI helpers using action()
def counter_widget(counter: Counter):
    """Example of generating Datastar action strings from Python."""
    print(f"Increment: {action(counter.increment)}")
    print(f"Decrement: {action(counter.decrement)}")
    print(f"Status:    {action(counter.status)}")
    print(f"List all:  {action(Counter.list_all)}")


# Register catch-all endpoints
configure_nitro(app)

if __name__ == "__main__":
    Counter.repository().init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)
