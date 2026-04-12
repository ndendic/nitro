"""
Sanic Todo — Reactive CRUD with Nitro + Datastar SSE

Extends the counter pattern to demonstrate:
  1. Entity CRUD — add, toggle, delete via @post decorated methods
  2. List rendering — server pushes the entire todo list on every change
  3. Signal-driven input — Datastar binds input to signal, server reads it
  4. publish_sync + SSE.patch_elements API (not deprecated emit_elements)
  5. Multi-tab sync — all connected browsers see changes instantly

Run:
    cd nitro && python examples/sanic_todo_app.py
    Then visit http://localhost:8002
"""
import uuid

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, get, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, P, Span, Button, Input

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

class Todo(Entity, table=True):
    """A todo item with event-driven CRUD."""
    __tablename__ = "todo"
    title: str = ""
    completed: bool = False

    @classmethod
    @post()
    def add(cls, title: str = "", request=None):
        """Create a new todo from the title signal."""
        title = title.strip()
        if not title:
            return {"error": "empty"}
        todo = cls(id=uuid.uuid4().hex[:8], title=title)
        todo.save()
        _broadcast_todos()
        publish_sync("sse", SSE.patch_signals({"title": ""}))
        return {"id": todo.id}

    @post()
    def toggle(self, request=None):
        """Toggle completed status."""
        self.completed = not self.completed
        self.save()
        _broadcast_todos()
        return {"completed": self.completed}

    @post()
    def remove(self, request=None):
        """Delete this todo."""
        self.delete()
        _broadcast_todos()
        return {"deleted": True}

    @get()
    def status(self):
        return {"id": self.id, "title": self.title, "completed": self.completed}


# ---------------------------------------------------------------------------
# Broadcast helper — new API
# ---------------------------------------------------------------------------

def _broadcast_todos():
    """Push updated todo list + stats to all connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(todo_list(), selector="#todo-list"))
    publish_sync("sse", SSE.patch_elements(todo_stats(), selector="#todo-stats"))


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

def todo_item(todo: Todo):
    """A single todo row with toggle + delete."""
    completed_cls = "line-through text-gray-400" if todo.completed else "text-gray-800"
    check_icon = "✓" if todo.completed else ""

    return Div(
        # Checkbox toggle
        Button(
            Span(check_icon, class_="text-xs"),
            class_=(
                "w-6 h-6 rounded-full border-2 flex items-center justify-center "
                "transition-all shrink-0 " +
                ("border-emerald-500 bg-emerald-50 text-emerald-600"
                 if todo.completed
                 else "border-gray-300 hover:border-emerald-400")
            ),
            on_click=action(todo.toggle),
        ),
        # Title
        Span(
            todo.title,
            class_=f"flex-1 px-3 {completed_cls} transition-colors",
        ),
        # Delete
        Button(
            "×",
            class_=(
                "w-7 h-7 rounded-lg text-gray-400 hover:text-red-500 "
                "hover:bg-red-50 transition-all text-lg leading-none "
                "opacity-0 group-hover:opacity-100"
            ),
            on_click=action(todo.remove),
        ),
        class_=(
            "group flex items-center py-3 px-4 rounded-xl "
            "hover:bg-gray-50 transition-all"
        ),
    )


def todo_list():
    """Full todo list — replaced by SSE on every change."""
    todos = Todo.all()
    if not todos:
        return Div(
            P(
                "No todos yet — add one above!",
                class_="text-gray-400 text-center py-8 italic",
            ),
            id="todo-list",
        )
    return Div(
        *[todo_item(t) for t in todos],
        id="todo-list",
        class_="divide-y divide-gray-100",
    )


def todo_stats():
    """Stats footer — replaced by SSE on every change."""
    todos = Todo.all()
    total = len(todos)
    done = sum(1 for t in todos if t.completed)
    remaining = total - done

    if total == 0:
        return Div(id="todo-stats")

    return Div(
        Span(f"{remaining} remaining", class_="text-sm text-gray-500"),
        Span("·", class_="text-gray-300 mx-2"),
        Span(f"{done} completed", class_="text-sm text-gray-500"),
        id="todo-stats",
        class_="flex items-center justify-center pt-4 mt-2 border-t border-gray-100",
    )


def todo_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1(
                    "Nitro Todo",
                    class_="text-3xl font-bold text-gray-900",
                ),
                P(
                    "Reactive CRUD — add, toggle, delete with real-time sync",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Add todo input (signals declared on container)
            Div(
                Input(
                    type="text",
                    placeholder="What needs to be done?",
                    bind="title",
                    on_keys_enter=action(Todo.add),
                    class_=(
                        "flex-1 px-4 py-3 rounded-xl border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-gray-700 placeholder-gray-400"
                    ),
                ),
                Button(
                    "Add",
                    class_=(
                        "px-6 py-3 rounded-xl font-semibold text-white "
                        "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                        "transition-all shadow-sm"
                    ),
                    on_click=action(Todo.add),
                ),
                class_="flex gap-3 mb-6",
                data_signals="{title: ''}",
            ),

            # Todo list (replaced by SSE patches)
            todo_list(),

            # Stats (replaced by SSE patches)
            todo_stats(),

            # Info footer
            Div(
                P(
                    "Open in multiple tabs — they all sync",
                    class_="text-xs text-gray-400 mt-6 text-center",
                ),
            ),

            # SSE connection — opens once when Datastar initializes
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-lg mx-auto px-6 py-12",
        ),
        title="Nitro Todo",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroTodo")
configure_nitro(app)


@app.before_server_start
async def setup(app, loop=None):
    Todo.repository().init_db()


@app.get("/")
async def homepage(request: Request):
    return html(str(todo_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002, debug=True, auto_reload=True)
