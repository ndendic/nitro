"""
FastAPI Integration Example - Todo App with Nitro Entity

Demonstrates:
1. Build Todo app with FastAPI in < 50 lines ✓
2. Swap persistence backend in 1 line ✓
3. Entity works as FastAPI response model ✓
4. Entity works as FastAPI request body ✓
5. Events work with FastAPI background tasks ✓

Run: uvicorn examples.fastapi_todo_app:app --reload --port 8080
Then visit: http://localhost:8080/docs
"""

import sys
from pathlib import Path
from typing import List

# Add the local nitro package to the path (for development)
nitro_path = Path(__file__).parent.parent
if str(nitro_path) not in sys.path:
    sys.path.insert(0, str(nitro_path))

from fastapi import FastAPI, BackgroundTasks, HTTPException
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.infrastructure.repository.memory import MemoryRepository
from nitro.infrastructure.events import on, emit_async

# Define Todo Entity - works as both request/response model
class Todo(Entity, table=True):
    title: str
    completed: bool = False

    # Swap backend by changing this line:
    # model_config = {"repository_class": MemoryRepository}
    model_config = {"repository_class": SQLModelRepository}

# Initialize FastAPI and database
app = FastAPI(title="Nitro FastAPI Todo")
SQLModelRepository().init_db()

# Event handler - runs asynchronously
@on("todo.created")
async def log_todo_creation(sender, **kwargs):
    print(f"📝 New todo created: {sender.title}")

@app.get("/", response_model=List[Todo])
async def list_todos():
    """List all todos - Entity as response model."""
    return Todo.all()

@app.post("/", response_model=Todo)
async def create_todo(todo: Todo, background_tasks: BackgroundTasks):
    """Create todo - Entity as request body with event."""
    todo.save()
    background_tasks.add_task(emit_async, "todo.created", todo)
    return todo

@app.get("/{todo_id}", response_model=Todo)
async def get_todo(todo_id: str):
    """Get specific todo."""
    todo = Todo.get(todo_id)
    if not todo:
        raise HTTPException(404, "Todo not found")
    return todo

@app.put("/{todo_id}", response_model=Todo)
async def update_todo(todo_id: str, data: Todo):
    """Update todo."""
    todo = Todo.get(todo_id)
    if not todo:
        raise HTTPException(404, "Todo not found")
    todo.title = data.title
    todo.completed = data.completed
    todo.save()
    return todo

@app.delete("/{todo_id}")
async def delete_todo(todo_id: str):
    """Delete todo."""
    todo = Todo.get(todo_id)
    if not todo:
        raise HTTPException(404, "Todo not found")
    todo.delete()
    return {"message": "Todo deleted"}
