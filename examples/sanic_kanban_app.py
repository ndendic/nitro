"""
Sanic Kanban — Drag-and-drop task board with Nitro + Datastar SSE

Demonstrates:
  1. Multi-entity design — Column and Task entities with relationships
  2. Drag-and-drop via data-drag plugin (sortable mode with drop zones)
  3. Edit modal — task description, priority, due date, subtasks
  4. User-defined columns — add, rename, reorder, delete columns
  5. publish_sync + SSE.patch_elements for real-time multi-tab sync
  6. on_keys plugin for keyboard submit

Run:
    cd nitro && python examples/sanic_kanban_app.py
    Then visit http://localhost:8003
"""
import uuid
import json
from datetime import datetime, timezone

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, get, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import (
    Div, H1, H2, H3, P, Span, Button, Input, Textarea, Select, Option,
    Label, Form,
)

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

PRIORITY_LABELS = {"low": "Low", "medium": "Medium", "high": "High", "urgent": "Urgent"}
PRIORITY_COLORS = {
    "low": "bg-gray-100 text-gray-600",
    "medium": "bg-blue-100 text-blue-700",
    "high": "bg-amber-100 text-amber-700",
    "urgent": "bg-red-100 text-red-700",
}
PRIORITY_DOT = {
    "low": "bg-gray-400",
    "medium": "bg-blue-500",
    "high": "bg-amber-500",
    "urgent": "bg-red-500",
}

# Default columns
DEFAULT_COLUMNS = [
    {"id": "todo", "name": "To Do", "color": "slate", "position": 0},
    {"id": "doing", "name": "In Progress", "color": "blue", "position": 1},
    {"id": "done", "name": "Done", "color": "emerald", "position": 2},
]

COLUMN_COLOR_MAP = {
    "slate": ("bg-slate-50 border-slate-200", "text-slate-700"),
    "blue": ("bg-blue-50 border-blue-200", "text-blue-700"),
    "emerald": ("bg-emerald-50 border-emerald-200", "text-emerald-700"),
    "purple": ("bg-purple-50 border-purple-200", "text-purple-700"),
    "amber": ("bg-amber-50 border-amber-200", "text-amber-700"),
    "rose": ("bg-rose-50 border-rose-200", "text-rose-700"),
    "cyan": ("bg-cyan-50 border-cyan-200", "text-cyan-700"),
    "indigo": ("bg-indigo-50 border-indigo-200", "text-indigo-700"),
}


class Column(Entity, table=True):
    """A kanban column — user-definable."""
    __tablename__ = "kanban_column"
    name: str = ""
    color: str = "slate"
    position: int = 0

    @classmethod
    @post()
    def add_column(cls, col_name: str = "", col_color: str = "slate", request=None):
        """Create a new column."""
        col_name = col_name.strip()
        if not col_name:
            return {"error": "empty"}
        existing = cls.all()
        max_pos = max((c.position for c in existing), default=-1)
        col = cls(id=uuid.uuid4().hex[:8], name=col_name, color=col_color, position=max_pos + 1)
        col.save()
        _broadcast_board()
        publish_sync("sse", SSE.patch_signals({"col_name": "", "col_color": "slate"}))
        return {"id": col.id}

    @post()
    def rename(self, col_name: str = "", request=None):
        """Rename this column."""
        col_name = col_name.strip()
        if col_name:
            self.name = col_name
            self.save()
            _broadcast_board()
        return {"id": self.id}

    @post()
    def remove_column(self, request=None):
        """Delete column and move its tasks to first column."""
        columns = sorted(Column.all(), key=lambda c: c.position)
        fallback = next((c for c in columns if c.id != self.id), None)
        if fallback:
            for task in Task.all():
                if task.column_id == self.id:
                    task.column_id = fallback.id
                    task.save()
        self.delete()
        _broadcast_board()
        return {"deleted": True}


class Task(Entity, table=True):
    """A kanban task with rich metadata."""
    __tablename__ = "kanban_task"
    title: str = ""
    description: str = ""
    priority: str = "medium"
    due_date: str = ""
    column_id: str = ""
    position: int = 0
    subtasks_json: str = "[]"

    @property
    def subtasks(self) -> list:
        try:
            return json.loads(self.subtasks_json)
        except (json.JSONDecodeError, TypeError):
            return []

    @subtasks.setter
    def subtasks(self, value: list):
        self.subtasks_json = json.dumps(value)

    @classmethod
    @post()
    def add(cls, title: str = "", request=None):
        """Create a new task in the first column."""
        title = title.strip()
        if not title:
            return {"error": "empty"}
        columns = sorted(Column.all(), key=lambda c: c.position)
        first_col = columns[0] if columns else None
        if not first_col:
            return {"error": "no columns"}
        existing = cls.all()
        max_pos = max((t.position for t in existing if t.column_id == first_col.id), default=-1)
        task = cls(
            id=uuid.uuid4().hex[:8], title=title,
            column_id=first_col.id, position=max_pos + 1,
        )
        task.save()
        _broadcast_board()
        publish_sync("sse", SSE.patch_signals({"title": ""}))
        return {"id": task.id}

    @post()
    def update_task(self, edit_title: str = "", edit_description: str = "",
                    edit_priority: str = "", edit_due_date: str = "",
                    request=None):
        """Update task details from the edit modal."""
        if edit_title.strip():
            self.title = edit_title.strip()
        self.description = edit_description.strip()
        if edit_priority in PRIORITY_LABELS:
            self.priority = edit_priority
        self.due_date = edit_due_date.strip()
        self.save()
        _broadcast_board()
        publish_sync("sse", SSE.patch_signals({"show_modal": ""}))
        return {"id": self.id}

    @post()
    def add_subtask(self, subtask_title: str = "", request=None):
        """Add a subtask."""
        subtask_title = subtask_title.strip()
        if not subtask_title:
            return {"error": "empty"}
        subs = self.subtasks
        subs.append({"id": uuid.uuid4().hex[:6], "title": subtask_title, "done": False})
        self.subtasks = subs
        self.save()
        _broadcast_board()
        _broadcast_modal(self)
        publish_sync("sse", SSE.patch_signals({"subtask_title": ""}))
        return {"id": self.id}

    @post()
    def toggle_subtask(self, sub_id: str = "", request=None):
        """Toggle a subtask's done status."""
        subs = self.subtasks
        for s in subs:
            if s["id"] == sub_id:
                s["done"] = not s["done"]
                break
        self.subtasks = subs
        self.save()
        _broadcast_board()
        _broadcast_modal(self)
        return {"id": self.id}

    @post()
    def remove_subtask(self, sub_id: str = "", request=None):
        """Remove a subtask."""
        subs = [s for s in self.subtasks if s["id"] != sub_id]
        self.subtasks = subs
        self.save()
        _broadcast_board()
        _broadcast_modal(self)
        return {"id": self.id}

    @post()
    def move_to(self, target_col: str = "", request=None):
        """Move task to a different column."""
        if not target_col:
            return {"error": "no target"}
        existing = Task.all()
        max_pos = max((t.position for t in existing if t.column_id == target_col), default=-1)
        self.column_id = target_col
        self.position = max_pos + 1
        self.save()
        _broadcast_board()
        return {"id": self.id, "column_id": self.column_id}

    @post()
    def remove(self, request=None):
        """Delete this task."""
        self.delete()
        _broadcast_board()
        return {"deleted": True}

    @classmethod
    @post()
    def reorder(cls, zone_data: str = "", request=None):
        """Handle drag-drop reorder. zone_data is JSON: {"zone_id": ["task_id", ...]}"""
        try:
            data = json.loads(zone_data)
        except (json.JSONDecodeError, TypeError):
            return {"error": "invalid data"}
        for col_id, task_ids in data.items():
            for pos, task_id in enumerate(task_ids):
                task = cls.get(task_id)
                if task:
                    task.column_id = col_id
                    task.position = pos
                    task.save()
        _broadcast_board()
        return {"ok": True}


# ---------------------------------------------------------------------------
# Broadcast helpers
# ---------------------------------------------------------------------------

def _broadcast_board():
    """Push updated board HTML to all connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(board_columns(), selector="#board"))
    publish_sync("sse", SSE.patch_elements(board_stats(), selector="#board-stats"))


def _broadcast_modal(task: Task):
    """Push updated modal content."""
    publish_sync("sse", SSE.patch_elements(modal_content(task), selector="#modal-content"))


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def subtask_item(task: Task, sub: dict):
    """A single subtask row."""
    done_cls = "line-through text-gray-400" if sub["done"] else "text-gray-700"
    check_cls = ("border-emerald-500 bg-emerald-50 text-emerald-600"
                 if sub["done"]
                 else "border-gray-300 hover:border-emerald-400")
    return Div(
        Button(
            Span("✓" if sub["done"] else "", class_="text-[10px]"),
            class_=f"w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all {check_cls}",
            on_click=action(task.toggle_subtask, sub_id=sub["id"]),
        ),
        Span(sub["title"], class_=f"flex-1 text-sm {done_cls}"),
        Button(
            "×",
            class_="w-5 h-5 rounded text-gray-300 hover:text-red-500 text-sm opacity-0 group-hover:opacity-100 transition-all",
            on_click=action(task.remove_subtask, sub_id=sub["id"]),
        ),
        class_="group flex items-center gap-2 py-1",
    )


def subtask_progress(task: Task):
    """Subtask progress indicator for the card."""
    subs = task.subtasks
    if not subs:
        return Span()
    done = sum(1 for s in subs if s["done"])
    total = len(subs)
    pct = int(done / total * 100) if total else 0
    return Div(
        Div(
            Div(class_=f"h-full bg-emerald-400 rounded-full transition-all", style=f"width:{pct}%"),
            class_="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden",
        ),
        Span(f"{done}/{total}", class_="text-[10px] text-gray-400 ml-1.5"),
        class_="flex items-center gap-1 mt-2",
    )


def priority_badge(priority: str):
    """Small priority indicator."""
    color = PRIORITY_COLORS.get(priority, PRIORITY_COLORS["medium"])
    return Span(
        PRIORITY_LABELS.get(priority, priority),
        class_=f"text-[10px] font-semibold px-1.5 py-0.5 rounded-full {color}",
    )


def task_card(task: Task):
    """A single task card — draggable, clickable for edit modal."""
    is_done = False
    columns = Column.all()
    done_col = next((c for c in columns if c.name.lower() == "done"), None)
    if done_col and task.column_id == done_col.id:
        is_done = True

    title_cls = "line-through text-gray-400" if is_done else "text-gray-800"

    due_el = Span()
    if task.due_date:
        due_el = Span(
            task.due_date,
            class_="text-[10px] text-gray-400",
        )

    return Div(
        # Card header — clickable to open modal
        Div(
            P(task.title, class_=f"text-sm font-medium {title_cls}"),
            on_click=f"$show_modal = '{task.id}'; @get('/api/task/{task.id}')",
            class_="cursor-pointer",
        ),
        # Metadata row
        Div(
            priority_badge(task.priority),
            due_el,
            Div(class_="flex-1"),
            Button(
                "×",
                title="Delete task",
                class_=(
                    "w-6 h-6 rounded text-gray-300 hover:text-red-500 "
                    "hover:bg-red-50 transition-all text-sm flex items-center "
                    "justify-center opacity-0 group-hover:opacity-100"
                ),
                on_click=action(task.remove),
            ),
            class_="flex items-center gap-2 mt-2",
        ),
        # Subtask progress
        subtask_progress(task),
        id=f"task-{task.id}",
        class_=(
            "group bg-white rounded-lg border border-gray-200 p-3 "
            "shadow-sm hover:shadow-md transition-all"
        ),
        data_draggable="",
    )


def column_view(col: Column):
    """A single kanban column with drop zone."""
    tasks = sorted(
        [t for t in Task.all() if t.column_id == col.id],
        key=lambda t: t.position,
    )
    task_count = len(tasks)
    bg_cls, header_cls = COLUMN_COLOR_MAP.get(col.color, COLUMN_COLOR_MAP["slate"])

    return Div(
        # Column header
        Div(
            H2(
                col.name,
                class_=f"text-sm font-bold uppercase tracking-wider {header_cls}",
            ),
            Div(
                Span(
                    str(task_count),
                    class_=(
                        "w-6 h-6 rounded-full bg-white/80 text-xs font-semibold "
                        "flex items-center justify-center text-gray-500 shadow-sm"
                    ),
                ),
                Button(
                    "×",
                    title="Delete column",
                    class_=(
                        "w-6 h-6 rounded text-gray-300 hover:text-red-500 "
                        "text-sm flex items-center justify-center "
                        "opacity-0 group-hover:opacity-100 transition-all"
                    ),
                    on_click=action(col.remove_column),
                ) if len(Column.all()) > 1 else Span(),
                class_="flex items-center gap-1",
            ),
            class_="group flex items-center justify-between mb-4 px-1",
        ),
        # Drop zone with task cards
        Div(
            *(task_card(t) for t in tasks) if tasks else [
                P(
                    "Drop tasks here",
                    class_="text-gray-400 text-center text-sm italic py-6",
                )
            ],
            data_drop_zone=col.id,
            class_="flex flex-col gap-2 min-h-[120px] rounded-lg p-1 transition-colors",
        ),
        class_=f"flex-1 min-w-[240px] rounded-xl border-2 {bg_cls} p-4",
    )


def board_columns():
    """All columns — replaced by SSE on every change."""
    columns = sorted(Column.all(), key=lambda c: c.position)
    return Div(
        *[column_view(col) for col in columns],
        id="board",
        class_="flex gap-4 overflow-x-auto pb-2",
    )


def board_stats():
    """Stats bar — replaced by SSE on every change."""
    tasks = Task.all()
    columns = sorted(Column.all(), key=lambda c: c.position)
    total = len(tasks)

    if total == 0:
        return Div(id="board-stats")

    stats = []
    stats.append(Span(f"{total} total", class_="text-sm font-medium text-gray-600"))
    for col in columns:
        count = sum(1 for t in tasks if t.column_id == col.id)
        _, header_cls = COLUMN_COLOR_MAP.get(col.color, COLUMN_COLOR_MAP["slate"])
        stats.append(Span("·", class_="text-gray-300 mx-1"))
        stats.append(Span(f"{count} {col.name.lower()}", class_=f"text-sm {header_cls}"))

    return Div(
        *stats,
        id="board-stats",
        class_="flex items-center justify-center py-3 flex-wrap",
    )


def modal_content(task: Task):
    """Edit modal inner content — can be updated via SSE."""
    subs = task.subtasks
    columns = sorted(Column.all(), key=lambda c: c.position)

    return Div(
        # Modal header
        Div(
            H3("Edit Task", class_="text-lg font-bold text-gray-900"),
            Button(
                "×",
                class_="w-8 h-8 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 text-xl transition-all",
                on_click="$show_modal = ''",
            ),
            class_="flex items-center justify-between mb-6",
        ),
        # Title
        Div(
            Label("Title", class_="text-sm font-medium text-gray-700 mb-1 block"),
            Input(
                type="text",
                bind="edit_title",
                class_=(
                    "w-full px-3 py-2 rounded-lg border border-gray-200 "
                    "bg-gray-50 focus:bg-white focus:border-blue-400 "
                    "focus:ring-2 focus:ring-blue-100 outline-none transition-all text-sm"
                ),
            ),
            class_="mb-4",
        ),
        # Description
        Div(
            Label("Description", class_="text-sm font-medium text-gray-700 mb-1 block"),
            Textarea(
                bind="edit_description",
                rows="3",
                class_=(
                    "w-full px-3 py-2 rounded-lg border border-gray-200 "
                    "bg-gray-50 focus:bg-white focus:border-blue-400 "
                    "focus:ring-2 focus:ring-blue-100 outline-none transition-all text-sm resize-none"
                ),
            ),
            class_="mb-4",
        ),
        # Priority + Due Date row
        Div(
            Div(
                Label("Priority", class_="text-sm font-medium text-gray-700 mb-1 block"),
                Select(
                    *[Option(label, value=val) for val, label in PRIORITY_LABELS.items()],
                    bind="edit_priority",
                    class_=(
                        "w-full px-3 py-2 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "outline-none transition-all text-sm"
                    ),
                ),
                class_="flex-1",
            ),
            Div(
                Label("Due Date", class_="text-sm font-medium text-gray-700 mb-1 block"),
                Input(
                    type="date",
                    bind="edit_due_date",
                    class_=(
                        "w-full px-3 py-2 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "outline-none transition-all text-sm"
                    ),
                ),
                class_="flex-1",
            ),
            class_="flex gap-4 mb-4",
        ),
        # Move to column
        Div(
            Label("Move to", class_="text-sm font-medium text-gray-700 mb-1 block"),
            Div(
                *[
                    Button(
                        c.name,
                        class_=(
                            "px-3 py-1.5 rounded-lg text-xs font-medium transition-all "
                            + ("bg-blue-500 text-white" if c.id == task.column_id
                               else "bg-gray-100 text-gray-600 hover:bg-gray-200")
                        ),
                        on_click=action(task.move_to, target_col=c.id),
                    )
                    for c in columns
                ],
                class_="flex gap-2 flex-wrap",
            ),
            class_="mb-4",
        ),
        # Subtasks
        Div(
            Label(
                f"Subtasks ({sum(1 for s in subs if s['done'])}/{len(subs)})" if subs else "Subtasks",
                class_="text-sm font-medium text-gray-700 mb-2 block",
            ),
            # Existing subtasks
            Div(
                *[subtask_item(task, s) for s in subs],
                class_="mb-2",
            ) if subs else Span(),
            # Add subtask input
            Div(
                Input(
                    type="text",
                    placeholder="Add subtask...",
                    bind="subtask_title",
                    on_keys_enter=action(task.add_subtask),
                    class_=(
                        "flex-1 px-3 py-1.5 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "outline-none transition-all text-sm"
                    ),
                ),
                Button(
                    "+",
                    class_=(
                        "px-3 py-1.5 rounded-lg bg-gray-100 text-gray-600 "
                        "hover:bg-gray-200 text-sm font-medium transition-all"
                    ),
                    on_click=action(task.add_subtask),
                ),
                class_="flex gap-2",
            ),
            class_="mb-6",
        ),
        # Save button
        Button(
            "Save Changes",
            class_=(
                "w-full py-2.5 rounded-xl font-semibold text-white "
                "bg-blue-500 hover:bg-blue-600 active:scale-[0.98] "
                "transition-all shadow-sm"
            ),
            on_click=action(task.update_task),
        ),
        id="modal-content",
    )


def edit_modal():
    """The modal wrapper — shown/hidden via show_modal signal."""
    return Div(
        # Backdrop
        Div(
            class_=(
                "fixed inset-0 bg-black/40 backdrop-blur-sm z-40 "
                "transition-opacity"
            ),
            on_click="$show_modal = ''",
        ),
        # Modal panel
        Div(
            Div(
                P("Loading...", class_="text-gray-400 text-center py-8"),
                id="modal-content",
            ),
            class_=(
                "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 "
                "bg-white rounded-2xl shadow-2xl p-6 z-50 "
                "w-full max-w-md max-h-[90vh] overflow-y-auto"
            ),
        ),
        id="edit-modal",
        data_show="$show_modal !== ''",
        style="display:none",
    )


def kanban_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Kanban", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Drag tasks between columns — real-time multiplayer sync",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Add task input
            Div(
                Input(
                    type="text",
                    placeholder="Add a new task...",
                    bind="title",
                    on_keys_enter=action(Task.add),
                    class_=(
                        "flex-1 px-4 py-3 rounded-xl border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-gray-700 placeholder-gray-400"
                    ),
                ),
                Button(
                    "Add Task",
                    class_=(
                        "px-6 py-3 rounded-xl font-semibold text-white "
                        "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                        "transition-all shadow-sm"
                    ),
                    on_click=action(Task.add),
                ),
                class_="flex gap-3 mb-4",
                data_signals="{title: '', show_modal: '', edit_title: '', edit_description: '', edit_priority: 'medium', edit_due_date: '', subtask_title: '', col_name: '', col_color: 'slate'}",
            ),

            # Add column controls
            Div(
                Button(
                    "+ Column",
                    class_=(
                        "px-4 py-2 rounded-lg text-sm font-medium "
                        "bg-gray-100 text-gray-600 hover:bg-gray-200 transition-all"
                    ),
                    on_click="$show_col_form = !$show_col_form",
                    data_signals="{show_col_form: false}",
                ),
                # Inline add column form
                Div(
                    Input(
                        type="text",
                        placeholder="Column name...",
                        bind="col_name",
                        on_keys_enter=action(Column.add_column),
                        class_=(
                            "px-3 py-2 rounded-lg border border-gray-200 "
                            "bg-gray-50 focus:bg-white focus:border-blue-400 "
                            "outline-none transition-all text-sm"
                        ),
                    ),
                    Select(
                        *[Option(name.capitalize(), value=name) for name in COLUMN_COLOR_MAP],
                        bind="col_color",
                        class_="px-3 py-2 rounded-lg border border-gray-200 bg-gray-50 text-sm",
                    ),
                    Button(
                        "Add",
                        class_="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 transition-all",
                        on_click=action(Column.add_column),
                    ),
                    class_="flex gap-2",
                    data_show="$show_col_form",
                ),
                class_="flex items-center gap-3 mb-6",
            ),

            # Board columns (replaced by SSE)
            board_columns(),

            # Stats (replaced by SSE)
            board_stats(),

            # Edit modal (hidden by default)
            edit_modal(),

            # Multi-tab sync notice
            Div(
                P(
                    "Open in multiple tabs — drag tasks, see changes sync in real time",
                    class_="text-xs text-gray-400 mt-6 text-center",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-6xl mx-auto px-6 py-12",
        ),
        title="Nitro Kanban",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# Drag-drop handler script
# ---------------------------------------------------------------------------

DRAG_SCRIPT = """
<script type="module">
import { setConfig } from 'https://cdn.jsdelivr.net/gh/ndendic/data-drag@latest/dist/index.js';
setConfig({ mode: 'sortable', signal: 'drag' });

// On drop complete, collect zone item order and POST to server
document.addEventListener('pointerup', () => {
    setTimeout(() => {
        const zones = document.querySelectorAll('[data-drop-zone]');
        const zoneData = {};
        let changed = false;
        zones.forEach(zone => {
            const zoneId = zone.getAttribute('data-drop-zone');
            const items = [...zone.querySelectorAll('[data-draggable]')].map(el => el.id.replace('task-', ''));
            zoneData[zoneId] = items;
            if (items.length > 0) changed = true;
        });
        if (changed) {
            fetch('/post/Task.reorder', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'zone_data=' + encodeURIComponent(JSON.stringify(zoneData))
            });
        }
    }, 100);
});

// Open modal: watch signal changes
const checkModal = () => {
    const ds = document.querySelector('[data-signals]');
    if (!ds) return;
    try {
        const signals = JSON.parse(ds.getAttribute('data-signals') || '{}');
        // We rely on Datastar's own reactivity for modal show/hide
    } catch(e) {}
};
</script>
"""


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroKanban")
configure_nitro(app)


@app.before_server_start
async def setup(app, loop=None):
    Column.repository().init_db()
    Task.repository().init_db()
    # Seed default columns if none exist
    if not Column.all():
        for col_data in DEFAULT_COLUMNS:
            Column(
                id=col_data["id"], name=col_data["name"],
                color=col_data["color"], position=col_data["position"],
            ).save()


@app.get("/")
async def homepage(request: Request):
    page_html = str(kanban_page())
    # Inject drag config script before closing body
    page_html = page_html.replace("</body>", DRAG_SCRIPT + "</body>")
    return html(page_html)


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


@app.get("/api/task/<task_id>")
async def get_task_for_modal(request: Request, task_id: str):
    """Return task data as SSE patches to populate the edit modal."""
    task = Task.get(task_id)
    if not task:
        return html("", status=404)
    # Push modal content + signal values via SSE
    publish_sync("sse", SSE.patch_elements(modal_content(task), selector="#modal-content"))
    publish_sync("sse", SSE.patch_signals({
        "edit_title": task.title,
        "edit_description": task.description,
        "edit_priority": task.priority,
        "edit_due_date": task.due_date,
        "subtask_title": "",
    }))
    return html("ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003, debug=True, auto_reload=True)
