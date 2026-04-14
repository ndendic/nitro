"""
Sanic File Manager — Virtual File Manager with Folder Navigation & CRUD

Demonstrates:
  1. Hierarchical entity relationships — parent_id tree structure
  2. Breadcrumb path computation from entity graph
  3. Recursive operations — delete folder and all descendants
  4. Grid card layout — folders and files as visual cards (vs table rows)
  5. Navigation state — _current_folder drives all views
  6. Mixed click behaviors — folders navigate, files have no drill-down
  7. Inline toolbar forms — new folder / new file without a separate page
  8. publish_sync + SSE.patch_elements for multi-region real-time updates

New patterns vs. prior examples:
  - Parent/child entity relationship via parent_id field
  - Breadcrumb trail computed by walking the entity graph to root
  - Recursive tree deletion (folder + all nested children)
  - Two item types (folder vs file) rendered differently on same grid

Run:
    cd nitro && python examples/sanic_filemanager_app.py
    Then visit http://localhost:8019
"""
import uuid
from datetime import datetime, timezone

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import (
    Div, H1, H2, P, Span, Button, Input, Select, Option,
)

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Navigation state (server-side)
# ---------------------------------------------------------------------------

_current_folder: str = "root"


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

FILE_TYPE_ICONS = {
    "pdf":  "📄",
    "py":   "🐍",
    "md":   "📝",
    "txt":  "📝",
    "jpg":  "🖼️",
    "jpeg": "🖼️",
    "png":  "🖼️",
    "gif":  "🖼️",
    "svg":  "🖼️",
    "xlsx": "📊",
    "xls":  "📊",
    "csv":  "📊",
    "json": "📋",
    "yaml": "📋",
    "toml": "📋",
    "html": "🌐",
    "css":  "🎨",
    "js":   "⚡",
    "ts":   "⚡",
    "zip":  "📦",
    "tar":  "📦",
    "gz":   "📦",
    "mp4":  "🎬",
    "mp3":  "🎵",
}

FILE_TYPE_COLORS = {
    "pdf":  "bg-red-50 border-red-200",
    "py":   "bg-blue-50 border-blue-200",
    "md":   "bg-slate-50 border-slate-200",
    "txt":  "bg-slate-50 border-slate-200",
    "jpg":  "bg-purple-50 border-purple-200",
    "jpeg": "bg-purple-50 border-purple-200",
    "png":  "bg-purple-50 border-purple-200",
    "gif":  "bg-purple-50 border-purple-200",
    "svg":  "bg-pink-50 border-pink-200",
    "xlsx": "bg-emerald-50 border-emerald-200",
    "xls":  "bg-emerald-50 border-emerald-200",
    "csv":  "bg-emerald-50 border-emerald-200",
    "json": "bg-yellow-50 border-yellow-200",
    "yaml": "bg-yellow-50 border-yellow-200",
    "toml": "bg-yellow-50 border-yellow-200",
    "html": "bg-orange-50 border-orange-200",
    "css":  "bg-pink-50 border-pink-200",
    "js":   "bg-amber-50 border-amber-200",
    "ts":   "bg-sky-50 border-sky-200",
    "zip":  "bg-gray-50 border-gray-200",
    "mp4":  "bg-indigo-50 border-indigo-200",
    "mp3":  "bg-indigo-50 border-indigo-200",
}


class FileItem(Entity, table=True):
    """A virtual file or folder in the file manager."""
    __tablename__ = "fileitem"
    name: str = ""
    kind: str = "file"       # "folder" or "file"
    parent_id: str = "root"  # ID of parent folder, "root" for top-level
    size: str = ""           # Display string e.g. "2.4 KB", empty for folders
    file_type: str = ""      # Extension e.g. "pdf", "py", empty for folders
    created: str = ""        # ISO date string

    # -----------------------------------------------------------------------
    # Class-level navigation
    # -----------------------------------------------------------------------

    @classmethod
    @post()
    def navigate(cls, folder_id: str = "root", request=None):
        """Navigate into a folder — sets the current viewed folder."""
        global _current_folder
        _current_folder = folder_id
        _broadcast_all()
        return {"folder_id": folder_id}

    @classmethod
    @post()
    def go_up(cls, request=None):
        """Navigate to parent of current folder."""
        global _current_folder
        if _current_folder == "root":
            return {"folder_id": "root"}
        current = cls.get(_current_folder)
        if current:
            _current_folder = current.parent_id
        else:
            _current_folder = "root"
        _broadcast_all()
        return {"folder_id": _current_folder}

    # -----------------------------------------------------------------------
    # CRUD
    # -----------------------------------------------------------------------

    @classmethod
    @post()
    def create_folder(cls, folder_name: str = "", request=None):
        """Create a new folder in the current location."""
        folder_name = folder_name.strip()
        if not folder_name:
            return {"error": "name required"}
        item = cls(
            id=uuid.uuid4().hex[:8],
            name=folder_name,
            kind="folder",
            parent_id=_current_folder,
            size="",
            file_type="",
            created=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        item.save()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({"folder_name": "", "show_new_folder": False}))
        return {"id": item.id}

    @classmethod
    @post()
    def create_file(cls, file_name: str = "", file_type: str = "",
                    file_size: str = "", request=None):
        """Create a new file in the current location."""
        file_name = file_name.strip()
        if not file_name:
            return {"error": "name required"}
        ft = file_type.strip().lower().lstrip(".")
        item = cls(
            id=uuid.uuid4().hex[:8],
            name=file_name,
            kind="file",
            parent_id=_current_folder,
            size=file_size.strip() or "0 B",
            file_type=ft,
            created=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        item.save()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({
            "file_name": "", "file_type": "", "file_size": "",
            "show_new_file": False,
        }))
        return {"id": item.id}

    @post()
    def remove(self, request=None):
        """Delete this item. If folder, recursively delete children."""
        global _current_folder
        _delete_recursive(self.id)
        # If we deleted the current folder, go up
        if _current_folder == self.id:
            _current_folder = "root"
        _broadcast_all()
        return {"deleted": True}

    @post()
    def rename(self, new_name: str = "", request=None):
        """Rename this item."""
        new_name = new_name.strip()
        if new_name:
            self.name = new_name
            self.save()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({"renaming_id": "", "new_name": ""}))
        return {"id": self.id}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _delete_recursive(item_id: str):
    """Delete an item and all its descendants."""
    item = FileItem.get(item_id)
    if not item:
        return
    if item.kind == "folder":
        children = [c for c in FileItem.all() if c.parent_id == item_id]
        for child in children:
            _delete_recursive(child.id)
    item.delete()


def _get_breadcrumb_path(folder_id: str) -> list[tuple[str, str]]:
    """
    Return list of (id, name) tuples from root to folder_id (inclusive).
    First element is always ("root", "Home").
    """
    path = []
    current_id = folder_id
    # Walk up the tree
    while current_id and current_id != "root":
        item = FileItem.get(current_id)
        if not item:
            break
        path.append((current_id, item.name))
        current_id = item.parent_id
    path.reverse()
    return [("root", "Home")] + path


def _get_children(folder_id: str) -> tuple[list, list]:
    """Return (folders, files) in folder_id, each sorted alphabetically."""
    items = [i for i in FileItem.all() if i.parent_id == folder_id]
    folders = sorted([i for i in items if i.kind == "folder"], key=lambda x: x.name.lower())
    files = sorted([i for i in items if i.kind == "file"], key=lambda x: x.name.lower())
    return folders, files


def _broadcast_all():
    """Push all dynamic regions to connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(breadcrumb_bar(), selector="#breadcrumb"))
    publish_sync("sse", SSE.patch_elements(file_grid(), selector="#file-grid"))
    publish_sync("sse", SSE.patch_elements(stats_bar(), selector="#stats-bar"))


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

def breadcrumb_bar():
    """Breadcrumb path from root to current folder, each segment clickable."""
    path = _get_breadcrumb_path(_current_folder)
    crumbs = []
    for i, (folder_id, name) in enumerate(path):
        is_last = i == len(path) - 1
        if is_last:
            crumbs.append(
                Span(
                    name,
                    class_="text-sm font-semibold text-gray-900",
                )
            )
        else:
            crumbs.append(
                Button(
                    name,
                    on_click=f"$nav_folder_id = '{folder_id}'; " + action(FileItem.navigate),
                    class_=(
                        "text-sm text-blue-600 hover:text-blue-800 hover:underline "
                        "transition-colors font-medium"
                    ),
                )
            )
            crumbs.append(
                Span("/", class_="text-gray-300 mx-1.5 text-sm")
            )

    return Div(
        *crumbs,
        id="breadcrumb",
        class_="flex items-center flex-wrap gap-0.5",
    )


def toolbar():
    """Toolbar with New Folder and New File buttons plus inline forms."""
    return Div(
        # New Folder button and form
        Div(
            Button(
                Span("📁", class_="mr-1.5"),
                "New Folder",
                on_click="$show_new_folder = !$show_new_folder; $show_new_file = false",
                class_=(
                    "flex items-center px-3.5 py-2 rounded-lg text-sm font-medium "
                    "bg-white border border-gray-200 text-gray-700 shadow-sm "
                    "hover:bg-gray-50 hover:border-gray-300 transition-all"
                ),
            ),
            # Inline new folder form
            Div(
                Input(
                    type="text",
                    placeholder="Folder name...",
                    bind="folder_name",
                    class_=(
                        "px-3 py-1.5 rounded-lg border border-gray-200 bg-gray-50 "
                        "focus:bg-white focus:border-blue-400 focus:ring-2 focus:ring-blue-100 "
                        "outline-none transition-all text-sm w-44"
                    ),
                ),
                Button(
                    "Create",
                    on_click=action(FileItem.create_folder),
                    class_=(
                        "px-3 py-1.5 rounded-lg text-sm font-semibold text-white "
                        "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                        "transition-all shadow-sm"
                    ),
                ),
                Button(
                    "×",
                    on_click="$show_new_folder = false",
                    class_=(
                        "px-2 py-1.5 rounded-lg text-sm text-gray-400 "
                        "hover:text-gray-600 hover:bg-gray-100 transition-all"
                    ),
                ),
                class_="flex items-center gap-2",
                data_show="$show_new_folder",
                style="display:none",
            ),
            class_="flex items-center gap-2",
        ),

        # New File button and form
        Div(
            Button(
                Span("📄", class_="mr-1.5"),
                "New File",
                on_click="$show_new_file = !$show_new_file; $show_new_folder = false",
                class_=(
                    "flex items-center px-3.5 py-2 rounded-lg text-sm font-medium "
                    "bg-white border border-gray-200 text-gray-700 shadow-sm "
                    "hover:bg-gray-50 hover:border-gray-300 transition-all"
                ),
            ),
            # Inline new file form
            Div(
                Input(
                    type="text",
                    placeholder="Filename...",
                    bind="file_name",
                    class_=(
                        "px-3 py-1.5 rounded-lg border border-gray-200 bg-gray-50 "
                        "focus:bg-white focus:border-blue-400 focus:ring-2 focus:ring-blue-100 "
                        "outline-none transition-all text-sm w-36"
                    ),
                ),
                Input(
                    type="text",
                    placeholder="Type (py, md...)",
                    bind="file_type",
                    class_=(
                        "px-3 py-1.5 rounded-lg border border-gray-200 bg-gray-50 "
                        "focus:bg-white focus:border-blue-400 focus:ring-2 focus:ring-blue-100 "
                        "outline-none transition-all text-sm w-28"
                    ),
                ),
                Input(
                    type="text",
                    placeholder="Size (2.4 KB)",
                    bind="file_size",
                    class_=(
                        "px-3 py-1.5 rounded-lg border border-gray-200 bg-gray-50 "
                        "focus:bg-white focus:border-blue-400 focus:ring-2 focus:ring-blue-100 "
                        "outline-none transition-all text-sm w-28"
                    ),
                ),
                Button(
                    "Create",
                    on_click=action(FileItem.create_file),
                    class_=(
                        "px-3 py-1.5 rounded-lg text-sm font-semibold text-white "
                        "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                        "transition-all shadow-sm"
                    ),
                ),
                Button(
                    "×",
                    on_click="$show_new_file = false",
                    class_=(
                        "px-2 py-1.5 rounded-lg text-sm text-gray-400 "
                        "hover:text-gray-600 hover:bg-gray-100 transition-all"
                    ),
                ),
                class_="flex items-center gap-2 flex-wrap",
                data_show="$show_new_file",
                style="display:none",
            ),
            class_="flex items-center gap-2",
        ),

        class_="flex items-center gap-3 flex-wrap",
    )


def folder_card(item: FileItem):
    """A folder card — clicking navigates into it."""
    return Div(
        # Icon + name row
        Div(
            Span("📁", class_="text-2xl"),
            Div(
                Span(
                    item.name,
                    class_="text-sm font-semibold text-gray-800 truncate block",
                ),
                Span(
                    item.created,
                    class_="text-xs text-gray-400 mt-0.5",
                ),
                class_="flex-1 min-w-0",
            ),
            class_="flex items-center gap-3",
        ),
        # Delete button (shown on hover)
        Div(
            Button(
                "×",
                title="Delete folder",
                on_click=action(item.remove),
                class_=(
                    "w-6 h-6 rounded-md text-gray-300 hover:text-red-500 "
                    "hover:bg-red-50 transition-all text-base leading-none "
                    "flex items-center justify-center "
                    "opacity-0 group-hover:opacity-100"
                ),
            ),
            class_="flex items-center justify-end mt-2",
        ),
        # Navigate on click (not on delete button)
        on_click=f"$nav_folder_id = '{item.id}'; " + action(FileItem.navigate),
        class_=(
            "group bg-white rounded-xl border border-gray-200 p-4 "
            "hover:border-blue-300 hover:shadow-md hover:bg-blue-50/30 "
            "cursor-pointer transition-all select-none"
        ),
    )


def file_icon(file_type: str) -> str:
    """Return appropriate emoji icon for a file type."""
    return FILE_TYPE_ICONS.get(file_type.lower(), "📄")


def file_card(item: FileItem):
    """A file card — shows icon, name, size, date."""
    icon = file_icon(item.file_type)
    color_cls = FILE_TYPE_COLORS.get(item.file_type.lower(), "bg-gray-50 border-gray-200")

    return Div(
        # Icon
        Div(
            Span(icon, class_="text-3xl"),
            class_=f"w-12 h-12 rounded-lg border {color_cls} flex items-center justify-center shrink-0",
        ),
        # Name and metadata
        Div(
            Span(
                item.name,
                class_="text-sm font-medium text-gray-800 truncate block",
                title=item.name,
            ),
            Div(
                Span(
                    item.file_type.upper() if item.file_type else "FILE",
                    class_="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-gray-100 text-gray-500",
                ),
                Span(item.size, class_="text-xs text-gray-400"),
                class_="flex items-center gap-2 mt-1",
            ),
            Span(item.created, class_="text-xs text-gray-400 mt-0.5 block"),
            class_="flex-1 min-w-0 mt-3",
        ),
        # Delete button
        Div(
            Button(
                "×",
                title="Delete file",
                on_click=action(item.remove),
                class_=(
                    "w-6 h-6 rounded-md text-gray-300 hover:text-red-500 "
                    "hover:bg-red-50 transition-all text-base leading-none "
                    "flex items-center justify-center "
                    "opacity-0 group-hover:opacity-100"
                ),
            ),
            class_="flex items-center justify-end",
        ),
        class_=(
            "group bg-white rounded-xl border border-gray-200 p-4 "
            "hover:border-gray-300 hover:shadow-md "
            "transition-all flex flex-col"
        ),
    )


def empty_state():
    """Shown when a folder has no contents."""
    return Div(
        Span("📂", class_="text-5xl mb-4"),
        P("This folder is empty", class_="text-gray-500 font-medium"),
        P(
            "Use the toolbar above to create folders and files",
            class_="text-gray-400 text-sm mt-1",
        ),
        class_="col-span-full flex flex-col items-center justify-center py-20 text-center",
    )


def file_grid():
    """Main content grid — folders first, then files. Replaced by SSE on every change."""
    folders, files = _get_children(_current_folder)
    total = len(folders) + len(files)

    if total == 0:
        content = [empty_state()]
    else:
        content = [folder_card(f) for f in folders] + [file_card(f) for f in files]

    return Div(
        *content,
        id="file-grid",
        class_="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4",
    )


def stats_bar():
    """Stats bar: item count summary. Replaced by SSE on every change."""
    folders, files = _get_children(_current_folder)
    n_folders = len(folders)
    n_files = len(files)
    total = n_folders + n_files

    if total == 0:
        text = "Empty folder"
    else:
        parts = []
        if n_folders:
            parts.append(f"{n_folders} folder{'s' if n_folders != 1 else ''}")
        if n_files:
            parts.append(f"{n_files} file{'s' if n_files != 1 else ''}")
        text = f"{total} item{'s' if total != 1 else ''} ({', '.join(parts)})"

    return Div(
        Span(text, class_="text-sm text-gray-500"),
        id="stats-bar",
    )


def filemanager_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro File Manager", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Virtual file system with folder navigation and real-time sync",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Main card
            Div(
                # Top bar: breadcrumbs + up button
                Div(
                    Div(
                        # Up button
                        Button(
                            "← Up",
                            on_click=action(FileItem.go_up),
                            class_=(
                                "px-3 py-1.5 rounded-lg text-sm font-medium "
                                "text-gray-500 hover:text-gray-700 hover:bg-gray-100 "
                                "transition-all shrink-0"
                            ),
                        ),
                        # Breadcrumb
                        breadcrumb_bar(),
                        class_="flex items-center gap-2 flex-1 min-w-0",
                    ),
                    class_="flex items-center gap-4 px-5 py-3 border-b border-gray-100 bg-gray-50/50 rounded-t-xl",
                ),

                # Toolbar
                Div(
                    toolbar(),
                    class_="px-5 py-3 border-b border-gray-100",
                ),

                # File grid (replaced by SSE)
                Div(
                    file_grid(),
                    class_="px-5 py-5",
                ),

                # Stats bar (replaced by SSE)
                Div(
                    stats_bar(),
                    class_="px-5 py-3 border-t border-gray-100 bg-gray-50/50 rounded-b-xl",
                ),

                class_="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden",
            ),

            # Footer tip
            Div(
                P(
                    "Open in multiple tabs — all changes sync in real time. "
                    "Click folders to navigate, hover items to delete.",
                    class_="text-xs text-gray-400 text-center mt-6",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-5xl mx-auto px-6 py-12",
            data_signals=(
                "{ nav_folder_id: 'root', "
                "show_new_folder: false, folder_name: '', "
                "show_new_file: false, file_name: '', file_type: '', file_size: '', "
                "renaming_id: '', new_name: '' }"
            ),
        ),
        title="Nitro File Manager",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroFileManager")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    FileItem.repository().init_db()
    if not FileItem.all():
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        def folder(name, parent_id="root"):
            item = FileItem(
                id=uuid.uuid4().hex[:8],
                name=name, kind="folder",
                parent_id=parent_id,
                size="", file_type="",
                created=today,
            )
            item.save()
            return item.id

        def file(name, file_type, size, parent_id="root"):
            item = FileItem(
                id=uuid.uuid4().hex[:8],
                name=name, kind="file",
                parent_id=parent_id,
                size=size, file_type=file_type,
                created=today,
            )
            item.save()

        # Top-level folders
        docs_id = folder("Documents")
        projects_id = folder("Projects")
        images_id = folder("Images")

        # Documents/
        file("report.pdf",   "pdf",  "45 KB",   parent_id=docs_id)
        file("notes.md",     "md",   "2.1 KB",  parent_id=docs_id)
        file("budget.xlsx",  "xlsx", "128 KB",  parent_id=docs_id)

        # Projects/
        file("app.py",       "py",   "8.3 KB",  parent_id=projects_id)
        file("README.md",    "md",   "1.5 KB",  parent_id=projects_id)
        file("config.json",  "json", "0.4 KB",  parent_id=projects_id)

        # Images/
        file("photo.jpg",    "jpg",  "2.1 MB",  parent_id=images_id)
        file("logo.png",     "png",  "45 KB",   parent_id=images_id)

        # Top-level files
        file("todo.txt",     "txt",  "0.3 KB")
        file("ideas.md",     "md",   "1.2 KB")


@app.get("/")
async def homepage(request: Request):
    return html(str(filemanager_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8019, debug=True, auto_reload=True)
