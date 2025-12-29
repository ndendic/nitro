"""
FastHTML Integration Example - Todo App with Nitro Entity

This example demonstrates:
1. Using Nitro Entity with FastHTML
2. Entity persistence with SQLModelRepository
3. RustyTags HTML generation
4. CRUD operations in FastHTML routes

Run: python examples/fasthtml_todo_app.py
Then visit: http://localhost:5001
"""

from fasthtml.common import *
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from rusty_tags import Div, H1, H2, P, Form, Input, Button, Ul, Li, Span, Br, A
from nitro.infrastructure.html import Page


# Define Todo Entity
class Todo(Entity, table=True):
    """Todo entity with persistence."""
    title: str
    completed: bool = False

    def toggle(self) -> None:
        """Toggle completed status."""
        self.completed = not self.completed
        self.save()


# Initialize database
repo = SQLModelRepository()
repo.init_db()

# Create FastHTML app
app, rt = fast_app()


@rt("/")
def homepage():
    """Homepage with todo list."""
    todos = Todo.all()

    page_content = Page(
        Div(
            H1("FastHTML + Nitro Todo App", class_="text-4xl font-bold text-purple-600 mb-4"),
            H2("Todo List", class_="text-2xl mb-6"),

            # Add todo form
            Form(
                Div(
                    Input(
                        type="text",
                        name="title",
                        placeholder="Enter a new todo...",
                        class_="border rounded px-4 py-2 mr-2 flex-1",
                        required=True
                    ),
                    Button(
                        "Add Todo",
                        type="submit",
                        class_="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded"
                    ),
                    class_="flex mb-6"
                ),
                method="POST",
                action="/add"
            ),

            # Todo list
            Div(
                Ul(
                    *[Li(
                        Div(
                            Span(
                                "✓ " if todo.completed else "○ ",
                                class_="mr-2 font-bold text-xl"
                            ),
                            Span(
                                todo.title,
                                class_="line-through text-gray-500" if todo.completed else ""
                            ),
                            Div(
                                A(
                                    "Toggle",
                                    href=f"/toggle/{todo.id}",
                                    class_="text-blue-500 hover:underline mr-2"
                                ),
                                A(
                                    "Delete",
                                    href=f"/delete/{todo.id}",
                                    class_="text-red-500 hover:underline"
                                ),
                                class_="ml-auto"
                            ),
                            class_="flex items-center mb-2 p-3 border rounded hover:bg-gray-50"
                        )
                    ) for todo in todos],
                    class_="space-y-2"
                ) if todos else P("No todos yet. Add one above!", class_="text-gray-500 italic"),
                class_="mb-6"
            ),

            # Stats
            Br(),
            Div(
                P(f"Total todos: {len(todos)}", class_="text-sm text-gray-600"),
                P(f"Completed: {len([t for t in todos if t.completed])}", class_="text-sm text-gray-600"),
                P(f"Remaining: {len([t for t in todos if not t.completed])}", class_="text-sm text-gray-600"),
                class_="border-t pt-4 mt-4"
            ),

            class_="container mx-auto p-8 max-w-2xl"
        ),
        title="FastHTML + Nitro Todo App",
        tailwind4=True
    )

    return str(page_content)


@rt("/add", methods=["POST"])
def post(title: str):
    """Add a new todo."""
    if title.strip():
        todo = Todo(id=str(len(Todo.all()) + 1), title=title.strip())
        todo.save()
    return RedirectResponse("/", status_code=303)


@rt("/toggle/{todo_id}")
def toggle_todo(todo_id: str):
    """Toggle todo completion status."""
    todo = Todo.get(todo_id)
    if todo:
        todo.toggle()
    return RedirectResponse("/", status_code=303)


@rt("/delete/{todo_id}")
def delete_todo(todo_id: str):
    """Delete a todo."""
    todo = Todo.get(todo_id)
    if todo:
        todo.delete()
    return RedirectResponse("/", status_code=303)


@rt("/api/todos")
def get_todos():
    """API endpoint to get all todos as JSON."""
    todos = Todo.all()
    return {
        "todos": [
            {
                "id": todo.id,
                "title": todo.title,
                "completed": todo.completed
            }
            for todo in todos
        ],
        "total": len(todos),
        "completed": len([t for t in todos if t.completed]),
        "remaining": len([t for t in todos if not t.completed])
    }


@rt("/api/todo/{todo_id}")
def get_todo(todo_id: str):
    """API endpoint to get a specific todo."""
    todo = Todo.get(todo_id)
    if todo:
        return {
            "id": todo.id,
            "title": todo.title,
            "completed": todo.completed
        }
    return {"error": "Todo not found"}, 404


if __name__ == "__main__":
    print("✓ Database initialized")
    print("✓ FastHTML + Nitro Todo app started")
    print("✓ Visit: http://localhost:5002")
    serve(port=5002)
