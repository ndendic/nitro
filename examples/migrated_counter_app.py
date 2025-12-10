"""
Migrated Counter App - From StarModel to Nitro

This is a migration of StarModel's simple.py counter example to Nitro.
Shows minimal changes needed for migration.

Original: ../StarModel/simple.py
Migrated: This file

Run: uvicorn examples.migrated_counter_app:app --reload --port 8082
Then visit: http://localhost:8082
"""

import sys
from pathlib import Path

# Add the local nitro package to the path (for development)
nitro_path = Path(__file__).parent.parent
if str(nitro_path) not in sys.path:
    sys.path.insert(0, str(nitro_path))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository
from rusty_tags import Main, H1, Div, Button, Span, Form, Input
from nitro.infrastructure.html import Page

# MIGRATION STEP 1: State → Entity
# MIGRATION STEP 2: Add model_config for repository
# Note: table=False for MemoryRepository, table=True for SQLModelRepository
class Counter(Entity, table=False):
    count: int = 0
    update_count: int = 0

    model_config = {"repository_class": MemoryRepository}

    # MIGRATION STEP 3: Add explicit .save() calls
    def increment(self, amount: int = 1):
        self.count += amount
        self.update_count += 1
        self.save()

    def decrement(self, amount: int = 1):
        self.count -= amount
        self.update_count += 1
        self.save()

    def reset(self):
        self.count = 0
        self.update_count += 1
        self.save()

# FastAPI app
app = FastAPI(title="Migrated Counter App - Nitro")

@app.get("/", response_class=HTMLResponse)
def index():
    """Main counter page."""
    # Get or create counter (using default session ID)
    counter = Counter.get("session-1") or Counter(id="session-1")

    page = Page(
        Main(
            H1("🔢 Counter Demo (Migrated from StarModel)", class_="text-4xl font-bold text-blue-600 mb-6"),

            # Counter display
            Div(
                Div(
                    Span(str(counter.count), class_="text-7xl font-bold text-blue-600"),
                    class_="text-center mb-4"
                ),
                Div(
                    f"Total updates: ",
                    Span(str(counter.update_count), class_="font-semibold"),
                    class_="text-gray-600"
                ),
                class_="bg-white p-8 rounded-lg shadow-lg text-center mb-6"
            ),

            # Counter controls
            Div(
                Div(
                    Button(
                        "-100",
                        onclick="fetch('/decrement?amount=100').then(() => location.reload())",
                        class_="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
                    ),
                    Button(
                        "-10",
                        onclick="fetch('/decrement?amount=10').then(() => location.reload())",
                        class_="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
                    ),
                    Button(
                        "-1",
                        onclick="fetch('/decrement?amount=1').then(() => location.reload())",
                        class_="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
                    ),
                    Button(
                        "Reset",
                        onclick="fetch('/reset').then(() => location.reload())",
                        class_="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
                    ),
                    Button(
                        "+1",
                        onclick="fetch('/increment?amount=1').then(() => location.reload())",
                        class_="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
                    ),
                    Button(
                        "+10",
                        onclick="fetch('/increment?amount=10').then(() => location.reload())",
                        class_="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
                    ),
                    Button(
                        "+100",
                        onclick="fetch('/increment?amount=100').then(() => location.reload())",
                        class_="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
                    ),
                    class_="flex gap-2 justify-center flex-wrap mb-6"
                ),
                class_="mb-6"
            ),

            # Migration info
            Div(
                H1("✅ Migration Complete!", class_="text-2xl font-bold text-green-600 mb-4"),
                Div(
                    "This counter was migrated from StarModel with minimal changes:",
                    class_="text-gray-700 mb-2"
                ),
                Div(
                    "1. Changed imports from 'starmodel' to 'nitro'",
                    class_="text-sm text-gray-600"
                ),
                Div(
                    "2. Renamed 'State' to 'Entity'",
                    class_="text-sm text-gray-600"
                ),
                Div(
                    "3. Added model_config for MemoryRepository",
                    class_="text-sm text-gray-600"
                ),
                Div(
                    "4. Added explicit .save() calls",
                    class_="text-sm text-gray-600"
                ),
                class_="bg-green-50 p-6 rounded-lg border border-green-200 mt-8"
            ),

            class_="container mx-auto p-8 max-w-3xl"
        ),
        title="Migrated Counter - Nitro",
        tailwind4=True
    )

    return str(page)

@app.get("/increment")
def increment_endpoint(amount: int = 1):
    """Increment counter."""
    counter = Counter.get("session-1")
    if counter:
        counter.increment(amount)
    return {"count": counter.count if counter else 0}

@app.get("/decrement")
def decrement_endpoint(amount: int = 1):
    """Decrement counter."""
    counter = Counter.get("session-1")
    if counter:
        counter.decrement(amount)
    return {"count": counter.count if counter else 0}

@app.get("/reset")
def reset_endpoint():
    """Reset counter."""
    counter = Counter.get("session-1")
    if counter:
        counter.reset()
    return {"count": 0}
