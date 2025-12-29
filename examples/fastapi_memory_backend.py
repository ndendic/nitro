"""
FastAPI with Memory Backend - Demonstrating Persistence Swap

This example shows how easy it is to swap persistence backends.
The ONLY difference from fastapi_todo_app.py is ONE LINE in the Entity definition.

Run: uvicorn examples.fastapi_memory_backend:app --reload --port 8081
Then visit: http://localhost:8081/docs
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
from nitro.infrastructure.repository.memory import MemoryRepository
from nitro.infrastructure.events import on, emit_async

# Define Todo Entity with MemoryRepository (ONLY CHANGE!)
class Todo(Entity, table=True):
    title: str
    completed: bool = False

    # 👉 THIS IS THE ONLY LINE THAT CHANGED:
    model_config = {"repository_class": MemoryRepository}
    # Previously was: {"repository_class": SQLModelRepository}

# Rest of the code is IDENTICAL to fastapi_todo_app.py
app = FastAPI(title="Nitro FastAPI Todo (Memory Backend)")

@on("todo.created")
async def log_todo_creation(sender, **kwargs):
    print(f"📝 New todo created: {sender.title}")

@app.get("/", response_model=List[Todo])
async def list_todos():
    return Todo.all()

@app.post("/", response_model=Todo)
async def create_todo(todo: Todo, background_tasks: BackgroundTasks):
    todo.save()
    background_tasks.add_task(emit_async, "todo.created", todo)
    return todo

@app.get("/{todo_id}", response_model=Todo)
async def get_todo(todo_id: str):
    todo = Todo.get(todo_id)
    if not todo:
        raise HTTPException(404, "Todo not found")
    return todo

@app.put("/{todo_id}", response_model=Todo)
async def update_todo(todo_id: str, data: Todo):
    todo = Todo.get(todo_id)
    if not todo:
        raise HTTPException(404, "Todo not found")
    todo.title = data.title
    todo.completed = data.completed
    todo.save()
    return todo

@app.delete("/{todo_id}")
async def delete_todo(todo_id: str):
    todo = Todo.get(todo_id)
    if not todo:
        raise HTTPException(404, "Todo not found")
    todo.delete()
    return {"message": "Todo deleted"}
