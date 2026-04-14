"""
Sanic Project Tracker — Multi-Entity Relationships with Real-time SSE

Demonstrates:
  1. Multi-entity design — Projects contain Tasks (linked by project_id)
  2. Cross-entity filtering — selecting a Project shows its Tasks
  3. Cascading operations — deleting a Project removes its Tasks
  4. Status cycling — click to advance task status (todo → doing → done)
  5. Sidebar + content layout — two-panel responsive UI
  6. publish_sync + SSE.patch_elements for multi-region updates

Run:
    cd nitro && python examples/sanic_tracker_app.py
    Then visit http://localhost:8009
"""
import uuid

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, H2, P, Span, Button, Input

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

_selected_project_id: str | None = None

PROJECT_COLORS = {
    "blue": ("bg-blue-500", "bg-blue-50 border-blue-200", "text-blue-700"),
    "green": ("bg-emerald-500", "bg-emerald-50 border-emerald-200", "text-emerald-700"),
    "purple": ("bg-purple-500", "bg-purple-50 border-purple-200", "text-purple-700"),
    "amber": ("bg-amber-500", "bg-amber-50 border-amber-200", "text-amber-700"),
    "rose": ("bg-rose-500", "bg-rose-50 border-rose-200", "text-rose-700"),
}

COLOR_CYCLE = list(PROJECT_COLORS.keys())

TASK_STATUSES = ["todo", "doing", "done"]
TASK_STATUS_LABELS = {"todo": "To Do", "doing": "Doing", "done": "Done"}
TASK_STATUS_STYLES = {
    "todo": "bg-slate-100 text-slate-600",
    "doing": "bg-blue-100 text-blue-600",
    "done": "bg-emerald-100 text-emerald-600",
}


class Project(Entity, table=True):
    """A project that contains tasks."""
    __tablename__ = "tracker_project"
    name: str = ""
    color: str = "blue"

    @classmethod
    @post()
    def add(cls, name: str = "", request=None):
        """Create a new project."""
        name = name.strip()
        if not name:
            return {"error": "empty"}
        # Pick color based on count
        count = len(cls.all())
        color = COLOR_CYCLE[count % len(COLOR_CYCLE)]
        project = cls(id=uuid.uuid4().hex[:8], name=name, color=color)
        project.save()
        # Auto-select the new project
        global _selected_project_id
        _selected_project_id = project.id
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({"name": ""}))
        return {"id": project.id}

    @post()
    def select(self, request=None):
        """Select this project to view its tasks."""
        global _selected_project_id
        _selected_project_id = self.id
        _broadcast_all()
        return {"id": self.id}

    @post()
    def remove(self, request=None):
        """Delete this project and all its tasks."""
        global _selected_project_id
        # Delete all tasks for this project
        for task in Task.all():
            if task.project_id == self.id:
                task.delete()
        self.delete()
        # If we deleted the selected project, clear selection
        if _selected_project_id == self.id:
            projects = Project.all()
            _selected_project_id = projects[0].id if projects else None
        _broadcast_all()
        return {"deleted": True}


class Task(Entity, table=True):
    """A task belonging to a project."""
    __tablename__ = "tracker_task"
    title: str = ""
    project_id: str = ""
    status: str = "todo"

    @classmethod
    @post()
    def add(cls, title: str = "", request=None):
        """Add a task to the currently selected project."""
        title = title.strip()
        if not title or not _selected_project_id:
            return {"error": "empty or no project"}
        task = cls(
            id=uuid.uuid4().hex[:8],
            title=title,
            project_id=_selected_project_id,
            status="todo",
        )
        task.save()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({"title": ""}))
        return {"id": task.id}

    @post()
    def cycle(self, request=None):
        """Advance status: todo → doing → done → todo."""
        idx = TASK_STATUSES.index(self.status)
        self.status = TASK_STATUSES[(idx + 1) % len(TASK_STATUSES)]
        self.save()
        _broadcast_all()
        return {"id": self.id, "status": self.status}

    @post()
    def remove(self, request=None):
        """Delete this task."""
        self.delete()
        _broadcast_all()
        return {"deleted": True}


# ---------------------------------------------------------------------------
# Broadcast helpers
# ---------------------------------------------------------------------------

def _broadcast_all():
    """Push both panels to all connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(project_list(), selector="#project-list"))
    publish_sync("sse", SSE.patch_elements(task_panel(), selector="#task-panel"))


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

def project_card(project: Project):
    """A single project in the sidebar."""
    is_selected = project.id == _selected_project_id
    dot_cls, _, text_cls = PROJECT_COLORS.get(project.color, PROJECT_COLORS["blue"])

    # Count tasks by status
    tasks = [t for t in Task.all() if t.project_id == project.id]
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "done")

    selected_ring = "ring-2 ring-blue-400 bg-white shadow-md" if is_selected else "bg-white hover:bg-gray-50"

    return Div(
        # Click to select
        Button(
            Div(
                # Color dot + name
                Div(
                    Span(class_=f"w-3 h-3 rounded-full {dot_cls} shrink-0"),
                    Span(project.name, class_=f"text-sm font-semibold {text_cls} truncate"),
                    class_="flex items-center gap-2 min-w-0",
                ),
                # Task count badge
                Span(
                    f"{done}/{total}" if total else "0",
                    class_="text-xs text-gray-400 font-medium shrink-0",
                ),
                class_="flex items-center justify-between w-full",
            ),
            class_=f"w-full text-left px-3 py-2.5 rounded-lg transition-all {selected_ring}",
            on_click=action(project.select),
        ),
        # Delete button (subtle, appears on hover)
        Button(
            "\u00d7",
            title="Delete project",
            class_=(
                "absolute top-1 right-1 w-5 h-5 rounded text-gray-300 "
                "hover:text-red-500 hover:bg-red-50 transition-all text-sm "
                "flex items-center justify-center opacity-0 group-hover:opacity-100"
            ),
            on_click=action(project.remove),
        ),
        class_="group relative",
    )


def project_list():
    """Sidebar project list — replaced by SSE."""
    projects = Project.all()

    items = [project_card(p) for p in projects] if projects else [
        P("No projects yet", class_="text-gray-400 text-sm italic text-center py-4")
    ]

    return Div(
        *items,
        id="project-list",
        class_="flex flex-col gap-1",
    )


def task_row(task: Task):
    """A single task row with status badge and controls."""
    status_cls = TASK_STATUS_STYLES[task.status]
    title_cls = "line-through text-gray-400" if task.status == "done" else "text-gray-800"

    return Div(
        # Status badge (click to cycle)
        Button(
            TASK_STATUS_LABELS[task.status],
            class_=f"text-xs px-2.5 py-1 rounded-full font-medium {status_cls} hover:opacity-80 transition-opacity shrink-0",
            title="Click to advance status",
            on_click=action(task.cycle),
        ),
        # Title
        P(task.title, class_=f"text-sm {title_cls} flex-1 min-w-0 truncate"),
        # Delete
        Button(
            "\u00d7",
            title="Delete task",
            class_=(
                "w-6 h-6 rounded text-gray-300 hover:text-red-500 "
                "hover:bg-red-50 transition-all text-sm flex items-center "
                "justify-center opacity-0 group-hover:opacity-100 shrink-0"
            ),
            on_click=action(task.remove),
        ),
        class_=(
            "group flex items-center gap-3 px-4 py-3 "
            "border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors"
        ),
    )


def task_panel():
    """Main content panel showing tasks for selected project — replaced by SSE."""
    if not _selected_project_id:
        return Div(
            Div(
                P("Select or create a project", class_="text-gray-400 text-lg"),
                P("Use the sidebar to get started", class_="text-gray-300 text-sm mt-1"),
                class_="text-center py-16",
            ),
            id="task-panel",
        )

    project = Project.get(_selected_project_id)
    if not project:
        return Div(
            P("Project not found", class_="text-gray-400 text-center py-16"),
            id="task-panel",
        )

    tasks = [t for t in Task.all() if t.project_id == project.id]
    by_status = {s: [t for t in tasks if t.status == s] for s in TASK_STATUSES}

    _, panel_cls, header_cls = PROJECT_COLORS.get(project.color, PROJECT_COLORS["blue"])

    # Stats
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "done")
    progress = int((done / total * 100) if total else 0)

    return Div(
        # Project header
        Div(
            H2(project.name, class_=f"text-xl font-bold {header_cls}"),
            Div(
                Span(f"{done}/{total} done", class_="text-sm text-gray-500"),
                # Progress bar
                Div(
                    Div(
                        class_=f"h-full bg-emerald-500 rounded-full transition-all",
                        style=f"width: {progress}%",
                    ),
                    class_="w-24 h-2 bg-gray-200 rounded-full overflow-hidden",
                ),
                class_="flex items-center gap-3",
            ),
            class_="flex items-center justify-between mb-4",
        ),

        # Add task input
        Div(
            Input(
                type="text",
                placeholder="Add a task...",
                bind="title",
                on_keys_enter=action(Task.add),
                class_=(
                    "flex-1 px-4 py-2.5 rounded-lg border border-gray-200 "
                    "bg-gray-50 focus:bg-white focus:border-blue-400 "
                    "focus:ring-2 focus:ring-blue-100 outline-none "
                    "transition-all text-sm text-gray-700 placeholder-gray-400"
                ),
            ),
            Button(
                "Add",
                class_=(
                    "px-5 py-2.5 rounded-lg text-sm font-semibold text-white "
                    "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                    "transition-all shadow-sm"
                ),
                on_click=action(Task.add),
            ),
            class_="flex gap-2 mb-4",
            data_signals="{title: ''}",
        ),

        # Task list grouped by status
        Div(
            *_task_group("todo", by_status["todo"]),
            *_task_group("doing", by_status["doing"]),
            *_task_group("done", by_status["done"]),
            class_="bg-white rounded-xl border border-gray-200 overflow-hidden",
        ) if tasks else Div(
            P(
                "No tasks yet. Add one above!",
                class_="text-gray-400 text-center text-sm italic py-8",
            ),
            class_="bg-white rounded-xl border border-gray-200",
        ),

        id="task-panel",
    )


def _task_group(status: str, tasks: list):
    """Render a status group header + tasks. Returns empty list if no tasks."""
    if not tasks:
        return []

    status_cls = TASK_STATUS_STYLES[status]
    return [
        Div(
            Span(
                TASK_STATUS_LABELS[status],
                class_=f"text-xs font-bold uppercase tracking-wider {status_cls} px-2 py-0.5 rounded-full",
            ),
            Span(str(len(tasks)), class_="text-xs text-gray-400 ml-1"),
            class_="flex items-center gap-1 px-4 py-2 bg-gray-50 border-b border-gray-100",
        ),
        *[task_row(t) for t in tasks],
    ]


def tracker_page():
    """Full page layout — sidebar + content."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Tracker", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Multi-entity project tracker with real-time sync",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Two-panel layout
            Div(
                # Left sidebar — Projects
                Div(
                    Div(
                        H2(
                            "Projects",
                            class_="text-xs font-bold uppercase tracking-wider text-gray-400",
                        ),
                        class_="mb-3",
                    ),

                    # Add project input
                    Div(
                        Input(
                            type="text",
                            placeholder="New project...",
                            bind="name",
                            on_keys_enter=action(Project.add),
                            class_=(
                                "w-full px-3 py-2 rounded-lg border border-gray-200 "
                                "bg-gray-50 focus:bg-white focus:border-blue-400 "
                                "focus:ring-2 focus:ring-blue-100 outline-none "
                                "transition-all text-sm placeholder-gray-400"
                            ),
                        ),
                        class_="mb-3",
                        data_signals="{name: ''}",
                    ),

                    # Project list (replaced by SSE)
                    project_list(),

                    class_=(
                        "w-64 shrink-0 bg-gray-50/50 rounded-2xl "
                        "border border-gray-200 p-4"
                    ),
                ),

                # Right content — Tasks
                Div(
                    task_panel(),
                    class_="flex-1 min-w-0",
                ),

                class_="flex gap-6 items-start",
            ),

            # Footer
            Div(
                P(
                    "Open in multiple tabs — project selection and tasks sync in real time",
                    class_="text-xs text-gray-400 mt-8 text-center",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-5xl mx-auto px-6 py-12",
        ),
        title="Nitro Tracker",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroTracker")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    Project.repository().init_db()
    Task.repository().init_db()


@app.get("/")
async def homepage(request: Request):
    return html(str(tracker_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8009, debug=True, auto_reload=True)
