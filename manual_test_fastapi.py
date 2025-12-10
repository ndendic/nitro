"""Manual test of FastAPI adapter to diagnose issues."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from nitro import Entity, action
from nitro.adapters.fastapi import configure_nitro
from nitro.infrastructure.repository.sql import SQLModelRepository


class TestCounter(Entity, table=True):
    """Test counter."""
    count: int = 0
    name: str = "Test Counter"  # Add default value

    model_config = {
        "repository_class": SQLModelRepository
    }

    @action(method="POST")
    def increment(self, amount: int = 1):
        """Increment."""
        self.count += amount
        self.save()
        return {"count": self.count}


# Setup
TestCounter.repository().init_db()
counter = TestCounter(id="test1", count=0, name="test1")
counter.save()

# Create app
app = FastAPI()
configure_nitro(app, entities=[TestCounter], auto_discover=False)

# Test
client = TestClient(app)
print("Testing POST /testcounter/test1/increment?amount=5")
try:
    response = client.post("/testcounter/test1/increment?amount=5")
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
