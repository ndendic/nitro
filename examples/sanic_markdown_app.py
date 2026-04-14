"""
Sanic Markdown Editor — Live Preview via SSE

Demonstrates:
  1. Textarea content editing with signal binding — Datastar binds multi-line input
  2. Server-side content transformation — markdown → HTML rendered on server, pushed via SSE
  3. Document CRUD — create, list, edit, delete markdown documents
  4. Split-pane layout — editor on left, rendered preview on right
  5. Signal-driven document switching — click sidebar to load different documents

New patterns vs. prior examples:
  - Notes app edits short text; this handles long-form markdown with live rendered preview
  - Server transforms content (markdown → HTML) before pushing to client
  - Three-column responsive layout: sidebar, editor, preview
  - Document switching via signals rather than page navigation

Run:
    cd nitro && python examples/sanic_markdown_app.py
    Then visit http://localhost:8015
"""
import os
os.environ.setdefault("NITRO_DB_URL", "sqlite:///markdown.db")

import uuid

import markdown

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, H3, P, Span, Button, Input, Textarea, HtmlString

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

class Document(Entity, table=True):
    """A markdown document with title, content, and rendered preview."""
    __tablename__ = "document"

    title: str = "Untitled"
    content: str = ""
    preview_html: str = ""

    def render_preview(self):
        """Convert markdown content to HTML."""
        self.preview_html = markdown.markdown(
            self.content,
            extensions=["fenced_code", "tables", "nl2br"],
        )

    @classmethod
    @post()
    def save_doc(cls, doc_id: str = "", title: str = "", content: str = "", request=None):
        """Save document — reads doc_id, title, content from signals."""
        if not doc_id:
            return {"error": "no document selected"}
        doc = cls.get(doc_id)
        if not doc:
            return {"error": "not found"}
        doc.title = title.strip() or doc.title
        doc.content = content
        doc.render_preview()
        doc.save()
        _broadcast(doc_id)
        return {"id": doc.id, "title": doc.title}

    @classmethod
    @post()
    def create_doc(cls, request=None):
        """Create a new blank document."""
        doc_id = f"doc-{uuid.uuid4().hex[:8]}"
        doc = cls(
            id=doc_id,
            title="New Document",
            content="# New Document\n\nStart writing...",
        )
        doc.render_preview()
        doc.save()
        # Switch to the new document via signals
        _broadcast(doc_id)
        publish_sync("sse", SSE.patch_signals({
            "doc_id": doc_id,
            "title": doc.title,
            "content": doc.content,
        }))
        return {"id": doc_id}

    @classmethod
    @post()
    def select_doc(cls, doc_id: str = "", request=None):
        """Switch to a different document — load its content into signals."""
        doc = cls.get(doc_id)
        if not doc:
            return {"error": "not found"}
        publish_sync("sse", SSE.patch_signals({
            "doc_id": doc.id,
            "title": doc.title,
            "content": doc.content,
        }))
        _broadcast(doc.id)
        return {"id": doc.id}

    @classmethod
    @post()
    def delete_doc(cls, doc_id: str = "", request=None):
        """Delete a document and switch to default."""
        doc = cls.get(doc_id)
        if doc and doc.id != "default":
            doc.delete()
        # Switch back to default
        default = cls.get("default")
        if default:
            publish_sync("sse", SSE.patch_signals({
                "doc_id": default.id,
                "title": default.title,
                "content": default.content,
            }))
        _broadcast("default")
        return {"deleted": True}


# ---------------------------------------------------------------------------
# Broadcast
# ---------------------------------------------------------------------------

def _broadcast(active_id: str = "default"):
    """Push sidebar + preview to all connected clients."""
    publish_sync("sse", SSE.patch_elements(
        doc_sidebar(active_id), selector="#doc-sidebar"
    ))
    doc = Document.get(active_id)
    if doc:
        publish_sync("sse", SSE.patch_elements(
            preview_pane(doc), selector="#preview-pane"
        ))


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def doc_sidebar(active_id: str = "default"):
    """Sidebar listing all documents."""
    docs = Document.all()
    items = []
    for doc in sorted(docs, key=lambda d: d.title.lower()):
        is_active = doc.id == active_id
        items.append(
            Button(
                Span(
                    doc.title or "Untitled",
                    class_="text-sm font-medium truncate block text-left",
                ),
                class_=(
                    "w-full px-3 py-2 rounded-lg text-left transition-colors "
                    + ("bg-blue-50 text-blue-700 border border-blue-200"
                       if is_active
                       else "hover:bg-gray-50 text-gray-700")
                ),
                on_click=(
                    f"$doc_id = '{doc.id}'; "
                    + action(Document.select_doc)
                ),
            )
        )

    return Div(
        Div(
            H3(
                "Documents",
                class_="text-xs font-semibold text-gray-500 uppercase tracking-wider",
            ),
            Button(
                "+ New",
                class_=(
                    "text-xs px-3 py-1 rounded-lg font-medium text-white "
                    "bg-blue-500 hover:bg-blue-600 active:scale-95 transition-all"
                ),
                on_click=action(Document.create_doc),
            ),
            class_="flex items-center justify-between mb-3",
        ),
        Div(
            *(items if items else [
                P("No documents yet", class_="text-sm text-gray-400 italic px-3")
            ]),
            class_="flex flex-col gap-1",
        ),
        id="doc-sidebar",
        class_="w-full",
    )


def editor_pane(doc: Document):
    """The markdown editor — title input + textarea + action buttons."""
    return Div(
        # Title input
        Input(
            type="text",
            bind="title",
            placeholder="Document title...",
            class_=(
                "w-full text-xl font-bold text-gray-900 bg-transparent "
                "border-0 border-b-2 border-gray-200 focus:border-blue-500 "
                "focus:outline-none pb-2 mb-4 transition-colors"
            ),
        ),
        # Markdown textarea
        Textarea(
            bind="content",
            placeholder="Write your markdown here...",
            rows="20",
            class_=(
                "w-full p-4 text-sm font-mono text-gray-800 bg-gray-50 "
                "border border-gray-200 rounded-xl resize-none "
                "focus:outline-none focus:ring-2 focus:ring-blue-200 "
                "focus:border-blue-400 transition-all leading-relaxed "
                "h-[calc(100vh-340px)]"
            ),
        ),
        # Save / Delete buttons
        Div(
            Button(
                "Save & Preview",
                class_=(
                    "px-5 py-2 rounded-lg font-semibold text-white "
                    "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                    "transition-all shadow-sm"
                ),
                on_click=action(Document.save_doc),
            ),
            Button(
                "Delete",
                class_=(
                    "px-4 py-2 rounded-lg font-medium text-red-600 "
                    "bg-red-50 hover:bg-red-100 active:scale-95 transition-all"
                ),
                on_click=action(Document.delete_doc),
                data_show="$doc_id !== 'default'",
            ),
            class_="flex items-center gap-3 mt-3",
        ),
        id="editor-pane",
    )


def preview_pane(doc: Document):
    """The rendered markdown preview — replaced by SSE after each save."""
    preview_content = doc.preview_html if doc.preview_html else (
        '<p class="text-gray-400 italic">Preview appears here after saving...</p>'
    )
    return Div(
        H3(
            "Preview",
            class_="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3",
        ),
        Div(
            HtmlString(preview_content),
            class_=(
                "prose prose-sm max-w-none p-4 bg-white border border-gray-200 "
                "rounded-xl h-[calc(100vh-300px)] overflow-y-auto"
            ),
        ),
        id="preview-pane",
    )


def editor_page(doc: Document):
    """Full page layout — sidebar + editor + preview."""
    return Page(
        Div(
            # Header
            Div(
                H1(
                    "Markdown Editor",
                    class_="text-2xl font-bold text-gray-900",
                ),
                P(
                    "Write markdown, save to render — live preview via SSE",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-6",
            ),

            # Main content — 3-column layout with signals
            Div(
                # Sidebar
                Div(
                    doc_sidebar(doc.id),
                    class_="w-52 shrink-0 border-r border-gray-200 pr-4",
                ),

                # Editor
                Div(
                    editor_pane(doc),
                    class_="flex-1 px-4 min-w-0",
                ),

                # Preview
                Div(
                    preview_pane(doc),
                    class_="flex-1 pl-4 border-l border-gray-200 min-w-0",
                ),

                class_="flex gap-0 min-h-[60vh]",
                data_signals=(
                    "{"
                    f"doc_id: '{_escape_js(doc.id)}', "
                    f"title: '{_escape_js(doc.title)}', "
                    f"content: `{_escape_template(doc.content)}`"
                    "}"
                ),
            ),

            # Footer
            Div(
                P(
                    "Open in multiple tabs — edits sync across browsers",
                    class_="text-xs text-gray-400 mt-6 text-center",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-7xl mx-auto px-6 py-8",
        ),
        title="Markdown Editor",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _escape_js(text: str) -> str:
    """Escape for single-quoted JS string."""
    return text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")


def _escape_template(text: str) -> str:
    """Escape for JS template literal (backtick string) inside an HTML attribute."""
    return (text.replace("\\", "\\\\").replace("`", "\\`")
            .replace("${", "\\${").replace('"', "\\x22"))


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroMarkdown")
configure_nitro(app)

DEFAULT_CONTENT = """# Welcome to the Markdown Editor

This is a **live preview** markdown editor built with Nitro + Sanic + Datastar.

## Features

- **Server-side rendering** — markdown is converted to HTML on the server
- **SSE push** — preview updates are pushed to your browser via Server-Sent Events
- **Multi-document** — create and switch between documents
- **No JavaScript frameworks** — just Python, HTML, and Datastar reactivity

## Try it out

Edit this text and click **Save & Preview** to see the rendered output.

### Code blocks

```python
from nitro import Entity, post, action

class Document(Entity, table=True):
    title: str = "Untitled"
    content: str = ""
```

### Tables

| Feature | Status |
|---------|--------|
| Markdown rendering | Done |
| Live preview | Done |
| Multi-document | Done |

> "The best way to predict the future is to create it." — Peter Drucker
"""


@app.before_server_start
async def setup(app):
    Document.repository().init_db()
    if not Document.get("default"):
        doc = Document(id="default", title="Welcome", content=DEFAULT_CONTENT)
        doc.render_preview()
        doc.save()


@app.get("/")
async def homepage(request: Request):
    doc = Document.get("default")
    if not doc:
        doc = Document(id="default", title="Welcome", content=DEFAULT_CONTENT)
        doc.render_preview()
        doc.save()
    return html(str(editor_page(doc)))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8015, debug=True, auto_reload=True)
