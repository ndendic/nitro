"""
Sanic Notes — CRUD Notes with Edit-in-Place

Demonstrates:
  1. Rich entity CRUD — create, update title/body, delete
  2. Textarea binding — Datastar binds multi-line input to signals
  3. Edit-in-place toggle — signals control view/edit modes
  4. Class-level action with signal params — save_edit reads editing ID from signals
  5. publish_sync + SSE.patch_elements API (not deprecated emit_elements)
  6. SSE signal patching to reset client state after save

Run:
    cd nitro && python examples/sanic_notes_app.py
    Then visit http://localhost:8006
"""
import os
os.environ.setdefault("NITRO_DB_URL", "sqlite:///notes.db")

import uuid
from datetime import datetime

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, get, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, H2, P, Span, Button, Input, Textarea

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

class Note(Entity, table=True):
    """A note with title, body, and timestamp."""
    __tablename__ = "note"
    title: str = ""
    body: str = ""
    updated_at: str = ""

    @classmethod
    @post()
    def create_note(cls, new_title: str = "", request=None):
        """Create a new note from the title signal."""
        title = new_title.strip()
        if not title:
            return {"error": "empty title"}
        note = cls(
            id=uuid.uuid4().hex[:8],
            title=title,
            body="",
            updated_at=datetime.now().strftime("%H:%M"),
        )
        note.save()
        _broadcast()
        publish_sync("sse", SSE.patch_signals({"new_title": ""}))
        return {"id": note.id}

    @classmethod
    @post()
    def save_edit(cls, editing: str = "", edit_title: str = "", edit_body: str = "", request=None):
        """Save edits — reads note ID from the 'editing' signal."""
        if not editing:
            return {"error": "no note selected"}
        note = cls.get(editing)
        if not note:
            return {"error": "not found"}
        note.title = edit_title.strip() or note.title
        note.body = edit_body
        note.updated_at = datetime.now().strftime("%H:%M")
        note.save()
        _broadcast()
        publish_sync("sse", SSE.patch_signals({"editing": "", "edit_title": "", "edit_body": ""}))
        return {"id": note.id}

    @post()
    def remove(self, request=None):
        """Delete this note."""
        self.delete()
        _broadcast()
        publish_sync("sse", SSE.patch_signals({"editing": ""}))
        return {"deleted": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _broadcast():
    """Push updated notes HTML to all connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(notes_list(), selector="#notes-list"))
    publish_sync("sse", SSE.patch_elements(notes_stats(), selector="#notes-stats"))


def get_all_notes():
    """All notes sorted by most recently updated."""
    notes = Note.all()
    notes.sort(key=lambda n: n.updated_at, reverse=True)
    return notes


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

def note_card(note: Note):
    """A single note card with view + edit actions."""
    preview = (note.body[:120] + "..." if len(note.body) > 120 else note.body) if note.body else "Empty note"

    # Build the JS expression to populate the editor signals
    edit_expr = (
        f"$editing = '{note.id}'; "
        f"$edit_title = '{_escape_js(note.title)}'; "
        f"$edit_body = `{_escape_template(note.body)}`"
    )

    return Div(
        # Header row: title + actions
        Div(
            H2(note.title, class_="text-base font-semibold text-gray-900 truncate"),
            Div(
                Button(
                    "Edit",
                    class_=(
                        "px-3 py-1 rounded-lg text-xs font-medium "
                        "text-indigo-600 hover:bg-indigo-50 transition-all"
                    ),
                    on_click=edit_expr,
                ),
                Button(
                    "\u00d7",
                    class_=(
                        "w-7 h-7 rounded-lg text-gray-400 hover:text-red-500 "
                        "hover:bg-red-50 transition-all text-lg leading-none "
                        "opacity-0 group-hover:opacity-100"
                    ),
                    on_click=action(note.remove),
                ),
                class_="flex items-center gap-1 shrink-0",
            ),
            class_="flex items-start justify-between gap-3 mb-2",
        ),
        # Body preview
        P(preview, class_="text-sm text-gray-500 line-clamp-2 leading-relaxed whitespace-pre-line"),
        # Timestamp
        Span(
            f"Updated {note.updated_at}" if note.updated_at else "",
            class_="text-xs text-gray-400 mt-2 block",
        ),
        class_=(
            "group bg-white rounded-xl border border-gray-200 p-4 "
            "hover:border-indigo-200 hover:shadow-sm transition-all cursor-default"
        ),
    )


def note_editor():
    """Inline editor — shown when $editing signal is non-empty.

    Uses Datastar data-show to conditionally display. The signals
    edit_title and edit_body are set when Edit is clicked on a card.
    Save uses class-level save_edit which reads the editing signal.
    """
    return Div(
        Div(
            H2("Edit Note", class_="text-sm font-bold uppercase tracking-wider text-indigo-400"),
            Button(
                "Cancel",
                class_=(
                    "px-3 py-1 rounded-lg text-xs font-medium "
                    "text-gray-500 hover:bg-gray-100 transition-all"
                ),
                on_click="$editing = ''; $edit_title = ''; $edit_body = ''",
            ),
            class_="flex items-center justify-between mb-3",
        ),
        Input(
            type="text",
            bind="edit_title",
            placeholder="Note title",
            class_=(
                "w-full px-4 py-2.5 rounded-lg border border-gray-200 "
                "bg-gray-50 focus:bg-white focus:border-indigo-400 "
                "focus:ring-2 focus:ring-indigo-100 outline-none "
                "transition-all text-gray-700 mb-3"
            ),
        ),
        Textarea(
            bind="edit_body",
            placeholder="Write your note...",
            rows="6",
            class_=(
                "w-full px-4 py-3 rounded-lg border border-gray-200 "
                "bg-gray-50 focus:bg-white focus:border-indigo-400 "
                "focus:ring-2 focus:ring-indigo-100 outline-none "
                "transition-all text-gray-700 resize-y mb-3 "
                "font-mono text-sm leading-relaxed"
            ),
        ),
        Div(
            Button(
                "Save",
                class_=(
                    "px-5 py-2.5 rounded-lg font-semibold text-white "
                    "bg-indigo-500 hover:bg-indigo-600 active:scale-95 "
                    "transition-all shadow-sm"
                ),
                on_click=action(Note.save_edit),
            ),
            class_="flex justify-end",
        ),
        id="note-editor",
        class_="bg-indigo-50/50 rounded-xl border border-indigo-200 p-4 mb-4",
        data_show="$editing !== ''",
    )


def notes_list():
    """All notes — replaced by SSE on every change."""
    notes = get_all_notes()

    if not notes:
        return Div(
            P(
                "No notes yet. Create your first one!",
                class_="text-gray-400 text-center text-sm italic py-12",
            ),
            id="notes-list",
            class_="flex flex-col gap-3",
        )

    return Div(
        *(note_card(n) for n in notes),
        id="notes-list",
        class_="flex flex-col gap-3",
    )


def notes_stats():
    """Note count — replaced by SSE."""
    notes = get_all_notes()
    total = len(notes)

    if total == 0:
        return Div(id="notes-stats")

    total_chars = sum(len(n.body) for n in notes)
    return Div(
        Span(f"{total} note{'s' if total != 1 else ''}", class_="text-sm text-gray-500"),
        Span("\u00b7", class_="text-gray-300 mx-2"),
        Span(f"{total_chars:,} characters", class_="text-sm text-indigo-500"),
        id="notes-stats",
        class_="flex items-center justify-center py-3",
    )


def notes_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Notes", class_="text-3xl font-bold text-gray-900"),
                P(
                    "CRUD notes with edit-in-place and real-time sync",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Create note form
            Div(
                Input(
                    type="text",
                    placeholder="New note title...",
                    bind="new_title",
                    on_keys_enter=action(Note.create_note),
                    class_=(
                        "flex-1 px-4 py-3 rounded-xl border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-indigo-400 "
                        "focus:ring-2 focus:ring-indigo-100 outline-none "
                        "transition-all text-gray-700 placeholder-gray-400"
                    ),
                ),
                Button(
                    "+ New Note",
                    class_=(
                        "px-6 py-3 rounded-xl font-semibold text-white "
                        "bg-indigo-500 hover:bg-indigo-600 active:scale-95 "
                        "transition-all shadow-sm shrink-0"
                    ),
                    on_click=action(Note.create_note),
                ),
                class_="flex gap-3 mb-6",
            ),

            # Inline editor (shown when editing)
            note_editor(),

            # Notes list (replaced by SSE)
            notes_list(),

            # Stats (replaced by SSE)
            notes_stats(),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-2xl mx-auto px-6 py-12",
            data_signals="{ new_title: '', editing: '', edit_title: '', edit_body: '' }",
        ),
        title="Nitro Notes",
        datastar=True,
        tailwind4=True,
    )


def _escape_js(s: str) -> str:
    """Escape a string for use inside JS single quotes."""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")


def _escape_template(s: str) -> str:
    """Escape a string for use inside JS template literals (backticks)."""
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroNotes")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    Note.repository().init_db()
    if not Note.all():
        Note(
            id="welcome",
            title="Welcome to Nitro Notes",
            body="This is a demo of CRUD notes with Nitro + Sanic + Datastar.\n\nClick Edit to modify this note, or create a new one above.",
            updated_at=datetime.now().strftime("%H:%M"),
        ).save()
        Note(
            id="features",
            title="Features",
            body="- Create and delete notes\n- Edit title and body inline\n- Real-time sync across tabs via SSE\n- Automatic timestamps\n- Responsive Tailwind UI",
            updated_at=datetime.now().strftime("%H:%M"),
        ).save()


@app.get("/")
async def homepage(request: Request):
    return html(str(notes_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8006, debug=True, auto_reload=True)
