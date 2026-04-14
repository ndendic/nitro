"""
Sanic Contacts — Server-Side Search & Filter

Demonstrates:
  1. Server-side search — search action re-renders filtered list via SSE
  2. Tag-based filtering — click tags to filter, active tag highlighted
  3. Multi-field entity — name, email, phone, company, tag
  4. Combined search + filter — text search AND tag filter work together
  5. publish_sync + SSE.patch_elements for multi-region updates

Run:
    cd nitro && python examples/sanic_contacts_app.py
    Then visit http://localhost:8011
"""
import uuid

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, H2, H3, P, Span, Button, Input, Select, Option

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

TAGS = {
    "work": ("Work", "bg-blue-500", "bg-blue-50 text-blue-700 border-blue-200"),
    "personal": ("Personal", "bg-violet-500", "bg-violet-50 text-violet-700 border-violet-200"),
    "family": ("Family", "bg-emerald-500", "bg-emerald-50 text-emerald-700 border-emerald-200"),
    "friend": ("Friend", "bg-amber-500", "bg-amber-50 text-amber-700 border-amber-200"),
    "vip": ("VIP", "bg-rose-500", "bg-rose-50 text-rose-700 border-rose-200"),
}

# Server-side filter state
_current_search = ""
_current_tag = ""


class Contact(Entity, table=True):
    """A contact with name, email, phone, company, and tag."""
    __tablename__ = "contact"
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    tag: str = "personal"

    @classmethod
    @post()
    def add(cls, name: str = "", email: str = "", phone: str = "",
            company: str = "", tag: str = "personal", request=None):
        """Add a new contact."""
        name = name.strip()
        if not name:
            return {"error": "name required"}
        contact = cls(
            id=uuid.uuid4().hex[:8],
            name=name,
            email=email.strip(),
            phone=phone.strip(),
            company=company.strip(),
            tag=tag if tag in TAGS else "personal",
        )
        contact.save()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({
            "add_name": "", "add_email": "", "add_phone": "",
            "add_company": "", "add_tag": "personal",
        }))
        return {"id": contact.id}

    @post()
    def remove(self, request=None):
        """Delete this contact."""
        self.delete()
        _broadcast_all()
        return {"deleted": True}

    @classmethod
    @post()
    def search(cls, q: str = "", filter_tag: str = "", request=None):
        """Server-side search + filter. Stores current filter state and re-renders."""
        global _current_search, _current_tag
        _current_search = q.strip().lower()
        _current_tag = filter_tag
        _broadcast_all()
        return {"ok": True}


# ---------------------------------------------------------------------------
# Filter + broadcast helpers
# ---------------------------------------------------------------------------

def _get_filtered_contacts():
    """Return contacts matching current search text and tag filter."""
    contacts = Contact.all()
    if _current_search:
        q = _current_search
        contacts = [
            c for c in contacts
            if q in c.name.lower()
            or q in c.email.lower()
            or q in c.company.lower()
            or q in c.phone.lower()
        ]
    if _current_tag:
        contacts = [c for c in contacts if c.tag == _current_tag]
    contacts.sort(key=lambda c: c.name.lower())
    return contacts


def _broadcast_all():
    """Push all dynamic regions to connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(contact_list(), selector="#contact-list"))
    publish_sync("sse", SSE.patch_elements(stats_bar(), selector="#stats-bar"))
    publish_sync("sse", SSE.patch_elements(tag_filters(), selector="#tag-filters"))


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

def stats_bar():
    """Contact count and tag distribution — replaced by SSE."""
    all_contacts = Contact.all()
    total = len(all_contacts)

    if total == 0:
        return Div(
            Span("No contacts yet", class_="text-sm text-gray-400 italic"),
            id="stats-bar",
            class_="flex items-center gap-3 flex-wrap py-2",
        )

    filtered = _get_filtered_contacts()
    shown = len(filtered)
    is_filtered = _current_search or _current_tag

    # Tag counts from filtered results
    tag_counts = {}
    for c in filtered:
        tag_counts[c.tag] = tag_counts.get(c.tag, 0) + 1

    count_text = (
        f"{shown} of {total} contact{'s' if total != 1 else ''}"
        if is_filtered
        else f"{total} contact{'s' if total != 1 else ''}"
    )

    parts = [
        Span(count_text, class_="text-sm font-semibold text-gray-700"),
    ]

    for tag_key, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        if tag_key in TAGS:
            label, _, badge_cls = TAGS[tag_key]
            parts.append(Span("\u00b7", class_="text-gray-300"))
            parts.append(
                Span(
                    f"{count} {label.lower()}",
                    class_=f"text-xs px-2 py-0.5 rounded-full font-medium border {badge_cls}",
                )
            )

    return Div(
        *parts,
        id="stats-bar",
        class_="flex items-center gap-2 flex-wrap py-2",
    )


def tag_filters():
    """Tag filter button row — active tag is highlighted. Replaced by SSE."""
    buttons = []

    # "All" button
    is_all_active = not _current_tag
    buttons.append(
        Button(
            "All",
            on_click="$filter_tag = ''; " + action(Contact.search),
            class_=(
                "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all "
                + (
                    "bg-gray-800 text-white shadow-sm"
                    if is_all_active
                    else "bg-gray-100 text-gray-600 hover:bg-gray-200"
                )
            ),
        )
    )

    # Tag buttons
    for tag_key, (label, bar_color, badge_cls) in TAGS.items():
        is_active = _current_tag == tag_key
        buttons.append(
            Button(
                label,
                on_click=f"$filter_tag = '{tag_key}'; " + action(Contact.search),
                class_=(
                    "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border "
                    + (
                        f"{badge_cls} shadow-sm"
                        if is_active
                        else "bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                    )
                ),
            )
        )

    return Div(
        *buttons,
        id="tag-filters",
        class_="flex items-center gap-2 flex-wrap",
    )


def contact_card(contact: Contact):
    """A single contact card with name, email, phone, company, tag badge, delete button."""
    tag_label, _, badge_cls = TAGS.get(contact.tag, ("Other", "bg-gray-500", "bg-gray-50 text-gray-700 border-gray-200"))

    initials = "".join(p[0].upper() for p in contact.name.split()[:2]) if contact.name else "?"
    # Pick avatar color from tag
    avatar_colors = {
        "work": "bg-blue-100 text-blue-600",
        "personal": "bg-violet-100 text-violet-600",
        "family": "bg-emerald-100 text-emerald-600",
        "friend": "bg-amber-100 text-amber-600",
        "vip": "bg-rose-100 text-rose-600",
    }
    avatar_cls = avatar_colors.get(contact.tag, "bg-gray-100 text-gray-600")

    rows = []

    if contact.email:
        rows.append(
            Div(
                Span("\u2709", class_="text-gray-400 w-4 shrink-0"),
                Span(contact.email, class_="text-sm text-gray-600 truncate"),
                class_="flex items-center gap-2",
            )
        )

    if contact.phone:
        rows.append(
            Div(
                Span("\u260e", class_="text-gray-400 w-4 shrink-0"),
                Span(contact.phone, class_="text-sm text-gray-600"),
                class_="flex items-center gap-2",
            )
        )

    if contact.company:
        rows.append(
            Div(
                Span("\U0001F3E2", class_="text-gray-400 w-4 shrink-0"),
                Span(contact.company, class_="text-sm text-gray-600 truncate"),
                class_="flex items-center gap-2",
            )
        )

    return Div(
        # Header row: avatar + name + tag + delete
        Div(
            # Avatar
            Div(
                Span(initials, class_="text-sm font-bold"),
                class_=f"w-10 h-10 rounded-full flex items-center justify-center shrink-0 {avatar_cls}",
            ),
            # Name + tag
            Div(
                P(contact.name, class_="text-base font-semibold text-gray-900 truncate leading-tight"),
                Span(
                    tag_label,
                    class_=f"text-xs px-2 py-0.5 rounded-full font-medium border {badge_cls} mt-0.5 inline-block",
                ),
                class_="flex-1 min-w-0",
            ),
            # Delete button
            Button(
                "\u00d7",
                title="Delete contact",
                class_=(
                    "w-7 h-7 rounded-lg text-gray-300 hover:text-red-500 "
                    "hover:bg-red-50 transition-all text-lg leading-none "
                    "flex items-center justify-center shrink-0 "
                    "opacity-0 group-hover:opacity-100"
                ),
                on_click=action(contact.remove),
            ),
            class_="flex items-center gap-3 mb-3",
        ),
        # Contact detail rows
        Div(
            *rows,
            class_="flex flex-col gap-1.5",
        ) if rows else Span(""),
        class_=(
            "group bg-white rounded-xl border border-gray-200 p-4 "
            "hover:border-gray-300 hover:shadow-sm transition-all"
        ),
    )


def contact_list():
    """Grid of contact cards for current filter — replaced by SSE."""
    contacts = _get_filtered_contacts()
    all_contacts = Contact.all()

    if not all_contacts:
        return Div(
            Div(
                P("\U0001f465", class_="text-5xl mb-3"),
                P("No contacts yet.", class_="text-gray-500 font-medium"),
                P("Add your first contact using the form above.", class_="text-gray-400 text-sm mt-1"),
                class_="text-center py-16",
            ),
            id="contact-list",
        )

    if not contacts:
        filter_desc = []
        if _current_search:
            filter_desc.append(f'"{_current_search}"')
        if _current_tag and _current_tag in TAGS:
            filter_desc.append(TAGS[_current_tag][0])
        filter_text = " + ".join(filter_desc) if filter_desc else "current filter"

        return Div(
            Div(
                P("\U0001f50d", class_="text-5xl mb-3"),
                P(f"No contacts match {filter_text}.", class_="text-gray-500 font-medium"),
                P("Try a different search or filter.", class_="text-gray-400 text-sm mt-1"),
                class_="text-center py-16",
            ),
            id="contact-list",
        )

    return Div(
        *[contact_card(c) for c in contacts],
        id="contact-list",
        class_="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4",
    )


def add_contact_form():
    """Inline form to add a new contact."""
    return Div(
        H3(
            "Add Contact",
            class_="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3",
        ),
        Div(
            # Row 1: name + email
            Div(
                Input(
                    type="text",
                    placeholder="Name *",
                    bind="add_name",
                    class_=(
                        "flex-1 px-4 py-2.5 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm text-gray-700 placeholder-gray-400 min-w-0"
                    ),
                ),
                Input(
                    type="email",
                    placeholder="Email",
                    bind="add_email",
                    class_=(
                        "flex-1 px-4 py-2.5 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm text-gray-700 placeholder-gray-400 min-w-0"
                    ),
                ),
                class_="flex gap-2",
            ),
            # Row 2: phone + company + tag + add button
            Div(
                Input(
                    type="tel",
                    placeholder="Phone",
                    bind="add_phone",
                    class_=(
                        "w-36 px-4 py-2.5 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm text-gray-700 placeholder-gray-400"
                    ),
                ),
                Input(
                    type="text",
                    placeholder="Company",
                    bind="add_company",
                    class_=(
                        "flex-1 px-4 py-2.5 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm text-gray-700 placeholder-gray-400 min-w-0"
                    ),
                ),
                Select(
                    *[Option(TAGS[t][0], value=t) for t in TAGS],
                    bind="add_tag",
                    class_=(
                        "px-3 py-2.5 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm text-gray-700"
                    ),
                ),
                Button(
                    "Add",
                    class_=(
                        "px-5 py-2.5 rounded-lg text-sm font-semibold text-white "
                        "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                        "transition-all shadow-sm shrink-0"
                    ),
                    on_click=action(Contact.add),
                ),
                class_="flex gap-2 flex-wrap items-center",
            ),
            class_="flex flex-col gap-2",
        ),
        class_="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm mb-6",
    )


def contacts_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Contacts", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Server-side search & tag filtering with real-time sync",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Main content wrapper with signals
            Div(
                # Search + filter bar
                Div(
                    # Search input
                    Div(
                        Span(
                            "\U0001f50d",
                            class_="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none",
                        ),
                        Input(
                            type="text",
                            placeholder="Search contacts...",
                            bind="q",
                            on_keyup=action(Contact.search),
                            class_=(
                                "w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 "
                                "bg-white focus:border-blue-400 focus:ring-2 focus:ring-blue-100 "
                                "outline-none transition-all text-sm text-gray-700 placeholder-gray-400"
                            ),
                        ),
                        class_="relative flex-1",
                    ),
                    class_="flex gap-3 mb-4",
                ),

                # Tag filter row
                tag_filters(),

                # Stats bar
                stats_bar(),

                class_="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm mb-6 flex flex-col gap-1",
            ),

            # Add contact form
            add_contact_form(),

            # Contact list (replaced by SSE)
            contact_list(),

            # Footer
            Div(
                P(
                    "Open in multiple tabs \u2014 contacts sync in real time",
                    class_="text-xs text-gray-400 text-center mt-8",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-5xl mx-auto px-6 py-12",
            data_signals=(
                "{ q: '', filter_tag: '', "
                "add_name: '', add_email: '', add_phone: '', add_company: '', add_tag: 'personal' }"
            ),
        ),
        title="Nitro Contacts",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroContacts")
configure_nitro(app)


@app.before_server_start
async def setup(app, loop=None):
    Contact.repository().init_db()
    if not Contact.all():
        seed_contacts = [
            ("Alice Chen", "alice@acmecorp.com", "555-0101", "Acme Corp", "work"),
            ("Bob Martinez", "bob.m@example.com", "555-0102", "TechCo", "friend"),
            ("Carol Smith", "carol@familymail.net", "555-0103", "", "family"),
            ("David Park", "david.park@startupxyz.io", "555-0104", "Startup XYZ", "work"),
            ("Emma Wilson", "emma@gmail.com", "555-0105", "", "personal"),
            ("Frank Nguyen", "frank@megacorp.com", "555-0106", "MegaCorp", "vip"),
            ("Grace Lee", "grace.lee@example.org", "555-0107", "Nonprofit Org", "work"),
            ("Henry Brown", "henry@personal.net", "555-0108", "", "friend"),
            ("Isabelle Torres", "isabelle@familydomain.com", "555-0109", "", "family"),
            ("James Kim", "james.kim@enterprise.io", "555-0110", "Enterprise Inc", "vip"),
        ]
        for name, email, phone, company, tag in seed_contacts:
            Contact(
                id=uuid.uuid4().hex[:8],
                name=name,
                email=email,
                phone=phone,
                company=company,
                tag=tag,
            ).save()


@app.get("/")
async def homepage(request: Request):
    return html(str(contacts_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8011, debug=True, auto_reload=True)
