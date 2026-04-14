"""
Sanic Data Table — Server-Side Sorting, Pagination & Search

Demonstrates:
  1. Server-side sorting — click column headers to sort asc/desc
  2. Pagination — page navigation with configurable page size
  3. Search filtering — text search across all columns via SSE
  4. Combined sort + filter + page — all three work together seamlessly
  5. Sortable column headers — visual indicators for sort direction
  6. publish_sync + SSE.patch_elements for multi-region updates

New patterns vs. prior examples:
  - Server-side table state (sort_col, sort_dir, page, page_size, search)
  - Column header click → sort toggle via entity class method
  - Pagination controls with first/prev/next/last navigation
  - Combined state: search resets to page 1, sort preserves page
  - Per-page dropdown for page size selection

Run:
    cd nitro && python examples/sanic_datatable_app.py
    Then visit http://localhost:8018
"""
import uuid
import random
from datetime import datetime, timezone, timedelta

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import (
    Div, H1, H2, P, Span, Button, Input, Select, Option, Table, Thead, Tbody,
    Tr, Th, Td,
)

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Table state (server-side)
# ---------------------------------------------------------------------------

_sort_col: str = "name"
_sort_dir: str = "asc"  # "asc" or "desc"
_page: int = 1
_page_size: int = 10
_search: str = ""

PAGE_SIZES = [5, 10, 25, 50]


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

DEPARTMENTS = ["Engineering", "Marketing", "Sales", "Finance", "HR", "Design", "Operations", "Support"]
STATUSES = {
    "active": ("Active", "bg-emerald-50 text-emerald-700 border-emerald-200"),
    "on_leave": ("On Leave", "bg-amber-50 text-amber-700 border-amber-200"),
    "remote": ("Remote", "bg-blue-50 text-blue-700 border-blue-200"),
    "inactive": ("Inactive", "bg-gray-50 text-gray-500 border-gray-200"),
}

SORTABLE_COLUMNS = {
    "name": "Name",
    "email": "Email",
    "department": "Department",
    "role": "Role",
    "status": "Status",
    "joined": "Joined",
}


class Employee(Entity, table=True):
    """An employee record for the data table demo."""
    __tablename__ = "employee"
    name: str = ""
    email: str = ""
    department: str = ""
    role: str = ""
    status: str = "active"
    joined: str = ""  # ISO date string for sorting

    @classmethod
    @post()
    def sort_by(cls, col: str = "name", request=None):
        """Sort table by column — toggles direction if same column clicked."""
        global _sort_col, _sort_dir
        if col not in SORTABLE_COLUMNS:
            return {"error": "invalid column"}
        if _sort_col == col:
            _sort_dir = "desc" if _sort_dir == "asc" else "asc"
        else:
            _sort_col = col
            _sort_dir = "asc"
        _broadcast_all()
        return {"sort": col, "dir": _sort_dir}

    @classmethod
    @post()
    def search(cls, q: str = "", request=None):
        """Search employees — resets to page 1."""
        global _search, _page
        _search = q.strip().lower()
        _page = 1
        _broadcast_all()
        return {"ok": True}

    @classmethod
    @post()
    def go_page(cls, p: int = 1, request=None):
        """Navigate to a specific page."""
        global _page
        _page = max(1, p)
        _broadcast_all()
        return {"page": _page}

    @classmethod
    @post()
    def set_page_size(cls, size: int = 10, request=None):
        """Change page size — resets to page 1."""
        global _page_size, _page
        _page_size = size if size in PAGE_SIZES else 10
        _page = 1
        _broadcast_all()
        return {"page_size": _page_size}

    @classmethod
    @post()
    def add(cls, name: str = "", email: str = "", department: str = "",
            role: str = "", status: str = "active", request=None):
        """Add a new employee."""
        name = name.strip()
        if not name:
            return {"error": "name required"}
        emp = cls(
            id=uuid.uuid4().hex[:8],
            name=name,
            email=email.strip(),
            department=department.strip(),
            role=role.strip(),
            status=status if status in STATUSES else "active",
            joined=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        emp.save()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({
            "add_name": "", "add_email": "", "add_dept": "",
            "add_role": "", "add_status": "active",
        }))
        return {"id": emp.id}

    @post()
    def remove(self, request=None):
        """Delete this employee."""
        self.delete()
        _broadcast_all()
        return {"deleted": True}


# ---------------------------------------------------------------------------
# Filter + sort + paginate helpers
# ---------------------------------------------------------------------------

def _get_filtered_sorted():
    """Return all employees matching search, sorted by current column."""
    employees = Employee.all()

    # Filter
    if _search:
        q = _search
        employees = [
            e for e in employees
            if q in e.name.lower()
            or q in e.email.lower()
            or q in e.department.lower()
            or q in e.role.lower()
            or q in e.status.lower()
        ]

    # Sort
    reverse = _sort_dir == "desc"
    employees.sort(key=lambda e: getattr(e, _sort_col, "").lower(), reverse=reverse)

    return employees


def _get_page(employees):
    """Return the current page slice and pagination metadata."""
    global _page
    total = len(employees)
    total_pages = max(1, (total + _page_size - 1) // _page_size)
    _page = min(_page, total_pages)  # clamp
    start = (_page - 1) * _page_size
    end = start + _page_size
    return employees[start:end], total, total_pages


def _broadcast_all():
    """Push all dynamic regions to connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(data_table(), selector="#data-table"))
    publish_sync("sse", SSE.patch_elements(pagination_controls(), selector="#pagination"))
    publish_sync("sse", SSE.patch_elements(table_stats(), selector="#table-stats"))


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

def sort_icon(col: str):
    """Return sort direction indicator for a column header."""
    if _sort_col != col:
        return Span("↕", class_="text-gray-300 ml-1 text-xs")
    arrow = "↑" if _sort_dir == "asc" else "↓"
    return Span(arrow, class_="text-blue-500 ml-1 text-xs font-bold")


def column_header(col: str, label: str):
    """Clickable column header with sort indicator."""
    is_active = _sort_col == col
    return Th(
        Button(
            Span(label),
            sort_icon(col),
            on_click=f"$col = '{col}'; " + action(Employee.sort_by),
            class_=(
                "flex items-center gap-0.5 text-left w-full px-1 py-1 "
                "rounded transition-colors hover:bg-gray-100 "
                + ("font-bold text-gray-900" if is_active else "font-semibold text-gray-600")
            ),
        ),
        class_="px-4 py-3 text-left text-xs uppercase tracking-wider",
    )


def status_badge(status: str):
    """Colored badge for employee status."""
    label, cls = STATUSES.get(status, ("Unknown", "bg-gray-50 text-gray-500 border-gray-200"))
    return Span(
        label,
        class_=f"text-xs px-2.5 py-0.5 rounded-full font-medium border {cls}",
    )


def employee_row(emp: Employee):
    """A single table row for an employee."""
    initials = "".join(p[0].upper() for p in emp.name.split()[:2]) if emp.name else "?"
    dept_colors = {
        "Engineering": "bg-blue-100 text-blue-600",
        "Marketing": "bg-purple-100 text-purple-600",
        "Sales": "bg-green-100 text-green-600",
        "Finance": "bg-yellow-100 text-yellow-600",
        "HR": "bg-pink-100 text-pink-600",
        "Design": "bg-indigo-100 text-indigo-600",
        "Operations": "bg-orange-100 text-orange-600",
        "Support": "bg-teal-100 text-teal-600",
    }
    avatar_cls = dept_colors.get(emp.department, "bg-gray-100 text-gray-600")

    return Tr(
        # Name + avatar
        Td(
            Div(
                Div(
                    Span(initials, class_="text-xs font-bold"),
                    class_=f"w-8 h-8 rounded-full flex items-center justify-center shrink-0 {avatar_cls}",
                ),
                Span(emp.name, class_="text-sm font-medium text-gray-900"),
                class_="flex items-center gap-3",
            ),
            class_="px-4 py-3",
        ),
        # Email
        Td(
            Span(emp.email, class_="text-sm text-gray-600"),
            class_="px-4 py-3",
        ),
        # Department
        Td(
            Span(emp.department, class_="text-sm text-gray-700"),
            class_="px-4 py-3",
        ),
        # Role
        Td(
            Span(emp.role, class_="text-sm text-gray-600"),
            class_="px-4 py-3",
        ),
        # Status
        Td(
            status_badge(emp.status),
            class_="px-4 py-3",
        ),
        # Joined
        Td(
            Span(emp.joined, class_="text-sm text-gray-500"),
            class_="px-4 py-3",
        ),
        # Delete
        Td(
            Button(
                "×",
                title="Remove employee",
                class_=(
                    "w-7 h-7 rounded-lg text-gray-300 hover:text-red-500 "
                    "hover:bg-red-50 transition-all text-lg leading-none "
                    "flex items-center justify-center "
                    "opacity-0 group-hover:opacity-100"
                ),
                on_click=action(emp.remove),
            ),
            class_="px-4 py-3 text-right",
        ),
        class_="group border-b border-gray-100 hover:bg-gray-50/50 transition-colors",
    )


def data_table():
    """The main data table — replaced by SSE on sort/filter/page changes."""
    employees = _get_filtered_sorted()
    page_employees, total, total_pages = _get_page(employees)

    if not Employee.all():
        return Div(
            Div(
                P("📊", class_="text-5xl mb-3"),
                P("No employees yet.", class_="text-gray-500 font-medium"),
                P("Add your first employee using the form below.", class_="text-gray-400 text-sm mt-1"),
                class_="text-center py-16",
            ),
            id="data-table",
        )

    if not page_employees:
        return Div(
            Div(
                P("🔍", class_="text-5xl mb-3"),
                P(f'No employees match "{_search}".', class_="text-gray-500 font-medium"),
                P("Try a different search term.", class_="text-gray-400 text-sm mt-1"),
                class_="text-center py-16",
            ),
            id="data-table",
        )

    return Div(
        Div(
            Table(
                Thead(
                    Tr(
                        *[column_header(col, label) for col, label in SORTABLE_COLUMNS.items()],
                        Th(
                            Span(""),
                            class_="px-4 py-3 w-12",
                        ),
                        class_="bg-gray-50/80",
                    ),
                ),
                Tbody(
                    *[employee_row(e) for e in page_employees],
                ),
                class_="w-full",
            ),
            class_="overflow-x-auto",
        ),
        id="data-table",
        class_="bg-white rounded-xl border border-gray-200 overflow-hidden",
    )


def table_stats():
    """Summary stats showing filtered count and current range."""
    employees = _get_filtered_sorted()
    total_all = len(Employee.all())
    total_filtered = len(employees)
    _, _, total_pages = _get_page(employees)

    start = (_page - 1) * _page_size + 1
    end = min(_page * _page_size, total_filtered)

    if total_filtered == 0:
        text = f"0 of {total_all} employees"
    elif total_filtered == total_all:
        text = f"Showing {start}–{end} of {total_all}"
    else:
        text = f"Showing {start}–{end} of {total_filtered} (filtered from {total_all})"

    return Div(
        Span(text, class_="text-sm text-gray-500"),
        id="table-stats",
    )


def pagination_controls():
    """Page navigation — first, prev, page numbers, next, last. Replaced by SSE."""
    employees = _get_filtered_sorted()
    _, total, total_pages = _get_page(employees)

    if total_pages <= 1:
        return Div(id="pagination", class_="flex items-center gap-1")

    def page_btn(label, page_num, disabled=False, is_current=False):
        if disabled:
            return Button(
                label,
                class_=(
                    "px-3 py-1.5 rounded-lg text-xs font-medium "
                    "text-gray-300 cursor-not-allowed"
                ),
                disabled="true",
            )
        if is_current:
            return Button(
                label,
                class_=(
                    "px-3 py-1.5 rounded-lg text-xs font-semibold "
                    "bg-blue-500 text-white shadow-sm"
                ),
            )
        return Button(
            label,
            on_click=f"$p = {page_num}; " + action(Employee.go_page),
            class_=(
                "px-3 py-1.5 rounded-lg text-xs font-medium "
                "text-gray-600 hover:bg-gray-100 transition-colors"
            ),
        )

    buttons = []
    # First / Prev
    buttons.append(page_btn("«", 1, disabled=(_page <= 1)))
    buttons.append(page_btn("‹", _page - 1, disabled=(_page <= 1)))

    # Page numbers — show window around current page
    window = 2
    start_p = max(1, _page - window)
    end_p = min(total_pages, _page + window)

    if start_p > 1:
        buttons.append(page_btn("1", 1))
        if start_p > 2:
            buttons.append(Span("…", class_="px-1 text-xs text-gray-400"))

    for p in range(start_p, end_p + 1):
        buttons.append(page_btn(str(p), p, is_current=(p == _page)))

    if end_p < total_pages:
        if end_p < total_pages - 1:
            buttons.append(Span("…", class_="px-1 text-xs text-gray-400"))
        buttons.append(page_btn(str(total_pages), total_pages))

    # Next / Last
    buttons.append(page_btn("›", _page + 1, disabled=(_page >= total_pages)))
    buttons.append(page_btn("»", total_pages, disabled=(_page >= total_pages)))

    return Div(
        *buttons,
        id="pagination",
        class_="flex items-center gap-1",
    )


def page_size_selector():
    """Dropdown to change rows per page."""
    return Div(
        Span("Rows:", class_="text-xs text-gray-500"),
        Select(
            *[
                Option(
                    str(s), value=str(s),
                    selected="selected" if s == _page_size else None,
                )
                for s in PAGE_SIZES
            ],
            bind="page_size",
            on_change=action(Employee.set_page_size),
            class_=(
                "px-2 py-1.5 rounded-lg border border-gray-200 bg-gray-50 "
                "text-xs text-gray-700 outline-none focus:border-blue-400 "
                "focus:ring-2 focus:ring-blue-100 transition-all"
            ),
        ),
        class_="flex items-center gap-2",
    )


def add_employee_form():
    """Inline form to add a new employee."""
    return Div(
        Div(
            Div(
                Input(
                    type="text",
                    placeholder="Name *",
                    bind="add_name",
                    class_=(
                        "flex-1 px-3 py-2 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm min-w-0"
                    ),
                ),
                Input(
                    type="email",
                    placeholder="Email",
                    bind="add_email",
                    class_=(
                        "flex-1 px-3 py-2 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm min-w-0"
                    ),
                ),
                Select(
                    Option("Department", value="", disabled="disabled"),
                    *[Option(d, value=d) for d in DEPARTMENTS],
                    bind="add_dept",
                    class_=(
                        "px-3 py-2 rounded-lg border border-gray-200 bg-gray-50 "
                        "text-sm outline-none focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 transition-all"
                    ),
                ),
                Input(
                    type="text",
                    placeholder="Role",
                    bind="add_role",
                    class_=(
                        "flex-1 px-3 py-2 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm min-w-0"
                    ),
                ),
                Select(
                    *[Option(STATUSES[s][0], value=s) for s in STATUSES],
                    bind="add_status",
                    class_=(
                        "px-3 py-2 rounded-lg border border-gray-200 bg-gray-50 "
                        "text-sm outline-none focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 transition-all"
                    ),
                ),
                Button(
                    "+ Add Employee",
                    class_=(
                        "px-4 py-2 rounded-lg text-sm font-semibold text-white "
                        "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                        "transition-all shadow-sm shrink-0 whitespace-nowrap"
                    ),
                    on_click=action(Employee.add),
                ),
                class_="flex gap-2 flex-wrap items-center",
            ),
            class_="flex flex-col gap-2",
        ),
        class_="bg-white rounded-xl border border-gray-200 p-4 shadow-sm",
    )


def datatable_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Data Table", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Server-side sorting, pagination & search with real-time sync",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Main content with signals
            Div(
                # Search bar
                Div(
                    Div(
                        Span(
                            "🔍",
                            class_="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none",
                        ),
                        Input(
                            type="text",
                            placeholder="Search employees...",
                            bind="q",
                            on_keyup=action(Employee.search),
                            class_=(
                                "w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 "
                                "bg-white focus:border-blue-400 focus:ring-2 focus:ring-blue-100 "
                                "outline-none transition-all text-sm placeholder-gray-400"
                            ),
                        ),
                        class_="relative flex-1",
                    ),
                    class_="mb-4",
                ),

                # Data table (replaced by SSE)
                data_table(),

                # Bottom bar: stats + page size + pagination
                Div(
                    table_stats(),
                    Div(
                        page_size_selector(),
                        pagination_controls(),
                        class_="flex items-center gap-4",
                    ),
                    class_="flex items-center justify-between flex-wrap gap-3 mt-4",
                ),

                # Add employee form
                Div(
                    P("Add Employee", class_="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3"),
                    add_employee_form(),
                    class_="mt-6",
                ),

                # Footer
                Div(
                    P(
                        "Open in multiple tabs — table syncs in real time. Click column headers to sort.",
                        class_="text-xs text-gray-400 text-center mt-8",
                    ),
                ),

                # SSE connection
                Div(data_init="@get('/sse')", style="display:none"),

                class_="max-w-6xl mx-auto px-6 py-12",
                data_signals=(
                    "{ q: '', col: 'name', p: 1, page_size: 10, size: 10, "
                    "add_name: '', add_email: '', add_dept: '', add_role: '', add_status: 'active' }"
                ),
            ),
            class_="min-h-screen bg-gray-50/50",
        ),
        title="Nitro Data Table",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroDataTable")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    Employee.repository().init_db()
    if not Employee.all():
        roles = [
            ("Software Engineer", "Engineering"),
            ("Senior Engineer", "Engineering"),
            ("Product Manager", "Marketing"),
            ("Marketing Lead", "Marketing"),
            ("Sales Rep", "Sales"),
            ("Account Executive", "Sales"),
            ("Financial Analyst", "Finance"),
            ("Controller", "Finance"),
            ("HR Manager", "HR"),
            ("Recruiter", "HR"),
            ("UX Designer", "Design"),
            ("Visual Designer", "Design"),
            ("Ops Manager", "Operations"),
            ("DevOps Engineer", "Operations"),
            ("Support Lead", "Support"),
            ("Support Agent", "Support"),
            ("Staff Engineer", "Engineering"),
            ("Content Writer", "Marketing"),
            ("Sales Director", "Sales"),
            ("CFO", "Finance"),
            ("People Ops", "HR"),
            ("Brand Designer", "Design"),
            ("SRE", "Operations"),
            ("Tech Support", "Support"),
            ("Intern", "Engineering"),
        ]
        first_names = [
            "Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace",
            "Henry", "Isabelle", "James", "Karen", "Liam", "Mia", "Noah",
            "Olivia", "Peter", "Quinn", "Rachel", "Sam", "Tara", "Uma",
            "Victor", "Wendy", "Xavier", "Yuki",
        ]
        last_names = [
            "Chen", "Martinez", "Smith", "Park", "Wilson", "Nguyen", "Lee",
            "Brown", "Torres", "Kim", "Johnson", "Davis", "Garcia", "Miller",
            "Anderson", "Taylor", "Thomas", "Jackson", "White", "Harris",
            "Thompson", "Moore", "Martin", "Clark", "Lewis",
        ]
        statuses = ["active", "active", "active", "active", "remote", "remote", "on_leave", "inactive"]

        rng = random.Random(42)  # deterministic seed
        base_date = datetime(2020, 1, 1, tzinfo=timezone.utc)

        for i, (role, dept) in enumerate(roles):
            fn = first_names[i]
            ln = last_names[i]
            joined = base_date + timedelta(days=rng.randint(0, 2000))
            Employee(
                id=uuid.uuid4().hex[:8],
                name=f"{fn} {ln}",
                email=f"{fn.lower()}.{ln.lower()}@example.com",
                department=dept,
                role=role,
                status=rng.choice(statuses),
                joined=joined.strftime("%Y-%m-%d"),
            ).save()


@app.get("/")
async def homepage(request: Request):
    return html(str(datatable_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8018, debug=True, auto_reload=True)
