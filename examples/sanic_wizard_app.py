"""
Sanic Form Wizard — Multi-Step Forms with Signal-Driven Navigation

Demonstrates:
  1. Multi-step form — signal-driven step navigation (client-side, no SSE)
  2. Accumulated form state — signals persist values across steps
  3. data-show conditional rendering — steps shown/hidden based on step signal
  4. Review & submit — all data collected client-side, submitted in one action
  5. Mixed reactivity — navigation is client-side, persistence is server-side
  6. publish_sync + SSE.patch_elements for submission list updates

Run:
    cd nitro && python examples/sanic_wizard_app.py
    Then visit http://localhost:8012
"""
import os
os.environ.setdefault("NITRO_DB_URL", "sqlite:///wizard.db")

import uuid
from datetime import datetime, timezone

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, H2, H3, P, Span, Button, Input, Select, Option, Label, Textarea

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

ROLES = {
    "developer": "Developer",
    "designer": "Designer",
    "manager": "Manager",
    "analyst": "Analyst",
    "other": "Other",
}

EXPERIENCE = {
    "junior": ("Junior", "< 2 years"),
    "mid": ("Mid-Level", "2-5 years"),
    "senior": ("Senior", "5-10 years"),
    "lead": ("Lead", "10+ years"),
}

THEMES = {
    "light": "Light",
    "dark": "Dark",
    "system": "System Default",
}


class Registration(Entity, table=True):
    """A completed registration from the wizard."""
    __tablename__ = "wizard_registration"
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    role: str = "developer"
    experience: str = "mid"
    theme: str = "system"
    newsletter: str = "yes"
    bio: str = ""
    submitted_at: str = ""

    @classmethod
    @post()
    def submit(
        cls,
        name: str = "",
        email: str = "",
        phone: str = "",
        company: str = "",
        role: str = "developer",
        experience: str = "mid",
        theme: str = "system",
        newsletter: str = "yes",
        bio: str = "",
        request=None,
    ):
        """Submit a completed registration."""
        name = name.strip()
        email = email.strip()
        if not name or not email:
            return {"error": "Name and email are required"}

        reg = cls(
            id=uuid.uuid4().hex[:8],
            name=name,
            email=email,
            phone=phone.strip(),
            company=company.strip(),
            role=role,
            experience=experience,
            theme=theme,
            newsletter=newsletter,
            bio=bio.strip(),
            submitted_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        )
        reg.save()
        _broadcast_list()
        # Reset form signals
        publish_sync(
            "sse",
            SSE.patch_signals({
                "step": 1,
                "name": "",
                "email": "",
                "phone": "",
                "company": "",
                "role": "developer",
                "experience": "mid",
                "theme": "system",
                "newsletter": "yes",
                "bio": "",
            }),
        )
        return {"id": reg.id}

    @post()
    def remove(self, request=None):
        """Delete a registration."""
        self.delete()
        _broadcast_list()
        return {"deleted": True}


# ---------------------------------------------------------------------------
# Broadcast
# ---------------------------------------------------------------------------

def _broadcast_list():
    publish_sync("sse", SSE.patch_elements(submissions_list(), selector="#submissions"))
    publish_sync("sse", SSE.patch_elements(stats_bar(), selector="#stats-bar"))


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def _input(label_text: str, signal: str, type_="text", placeholder="", **kwargs):
    """Styled form input with label."""
    return Div(
        Label(
            label_text,
            class_="block text-sm font-medium text-gray-700 mb-1.5",
        ),
        Input(
            type=type_,
            placeholder=placeholder,
            bind=signal,
            class_=(
                "w-full px-4 py-2.5 rounded-lg border border-gray-200 "
                "bg-gray-50 focus:bg-white focus:border-blue-400 "
                "focus:ring-2 focus:ring-blue-100 outline-none "
                "transition-all text-sm text-gray-700 placeholder-gray-400"
            ),
            **kwargs,
        ),
        class_="flex flex-col",
    )


def _select(label_text: str, signal: str, options: dict[str, str]):
    """Styled select with label."""
    return Div(
        Label(
            label_text,
            class_="block text-sm font-medium text-gray-700 mb-1.5",
        ),
        Select(
            *[Option(v, value=k) for k, v in options.items()],
            bind=signal,
            class_=(
                "w-full px-4 py-2.5 rounded-lg border border-gray-200 "
                "bg-gray-50 focus:bg-white focus:border-blue-400 "
                "focus:ring-2 focus:ring-blue-100 outline-none "
                "transition-all text-sm text-gray-700"
            ),
        ),
        class_="flex flex-col",
    )


def progress_bar():
    """Step progress indicator — pure client-side via data-class."""
    steps = ["Personal", "Professional", "Preferences", "Review"]

    step_nodes = []
    for i, label in enumerate(steps, 1):
        # Circle with number
        circle = Div(
            Span(str(i), class_="text-xs font-bold"),
            data_class=(
                f"$step >= {i} "
                f"? 'w-8 h-8 rounded-full flex items-center justify-center bg-blue-500 text-white shadow-sm' "
                f": 'w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 text-gray-500'"
            ),
        )
        # Label
        step_label = Span(
            label,
            data_class=(
                f"$step >= {i} "
                f"? 'text-xs font-semibold text-blue-600 mt-1' "
                f": 'text-xs text-gray-400 mt-1'"
            ),
        )
        step_nodes.append(
            Div(circle, step_label, class_="flex flex-col items-center")
        )

        # Connector line between steps
        if i < len(steps):
            step_nodes.append(
                Div(
                    Div(
                        data_class=(
                            f"$step > {i} "
                            f"? 'h-0.5 w-full bg-blue-400 transition-all' "
                            f": 'h-0.5 w-full bg-gray-200 transition-all'"
                        ),
                    ),
                    class_="flex-1 flex items-center px-2 pt-0 -mt-3",
                ),
            )

    return Div(
        *step_nodes,
        class_="flex items-start justify-between mb-8",
    )


def step_personal():
    """Step 1: Personal information."""
    return Div(
        H3("Personal Information", class_="text-lg font-semibold text-gray-800 mb-1"),
        P("Let's start with your basic details.", class_="text-sm text-gray-500 mb-6"),
        Div(
            _input("Full Name", "name", placeholder="Jane Smith"),
            _input("Email", "email", type_="email", placeholder="jane@example.com"),
            _input("Phone", "phone", type_="tel", placeholder="+1 (555) 000-0000"),
            class_="flex flex-col gap-4",
        ),
        # Navigation
        Div(
            Div(),  # spacer
            Button(
                "Next \u2192",
                on_click="$step = 2",
                class_=(
                    "px-6 py-2.5 rounded-lg text-sm font-semibold text-white "
                    "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                    "transition-all shadow-sm"
                ),
            ),
            class_="flex justify-between mt-8",
        ),
        data_show="$step === 1",
    )


def step_professional():
    """Step 2: Professional details."""
    return Div(
        H3("Professional Details", class_="text-lg font-semibold text-gray-800 mb-1"),
        P("Tell us about your work.", class_="text-sm text-gray-500 mb-6"),
        Div(
            _input("Company", "company", placeholder="Acme Inc."),
            _select("Role", "role", ROLES),
            _select("Experience Level", "experience", {k: f"{v[0]} ({v[1]})" for k, v in EXPERIENCE.items()}),
            class_="flex flex-col gap-4",
        ),
        Div(
            Button(
                "\u2190 Back",
                on_click="$step = 1",
                class_=(
                    "px-6 py-2.5 rounded-lg text-sm font-semibold "
                    "text-gray-600 bg-gray-100 hover:bg-gray-200 "
                    "active:scale-95 transition-all"
                ),
            ),
            Button(
                "Next \u2192",
                on_click="$step = 3",
                class_=(
                    "px-6 py-2.5 rounded-lg text-sm font-semibold text-white "
                    "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                    "transition-all shadow-sm"
                ),
            ),
            class_="flex justify-between mt-8",
        ),
        data_show="$step === 2",
    )


def step_preferences():
    """Step 3: Preferences."""
    return Div(
        H3("Preferences", class_="text-lg font-semibold text-gray-800 mb-1"),
        P("Customize your experience.", class_="text-sm text-gray-500 mb-6"),
        Div(
            _select("Theme", "theme", THEMES),
            _select("Newsletter", "newsletter", {"yes": "Yes, keep me updated", "no": "No thanks"}),
            # Bio textarea
            Div(
                Label("Bio", class_="block text-sm font-medium text-gray-700 mb-1.5"),
                Textarea(
                    bind="bio",
                    placeholder="A few words about yourself...",
                    rows="3",
                    class_=(
                        "w-full px-4 py-2.5 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm text-gray-700 placeholder-gray-400 resize-none"
                    ),
                ),
                class_="flex flex-col",
            ),
            class_="flex flex-col gap-4",
        ),
        Div(
            Button(
                "\u2190 Back",
                on_click="$step = 2",
                class_=(
                    "px-6 py-2.5 rounded-lg text-sm font-semibold "
                    "text-gray-600 bg-gray-100 hover:bg-gray-200 "
                    "active:scale-95 transition-all"
                ),
            ),
            Button(
                "Review \u2192",
                on_click="$step = 4",
                class_=(
                    "px-6 py-2.5 rounded-lg text-sm font-semibold text-white "
                    "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                    "transition-all shadow-sm"
                ),
            ),
            class_="flex justify-between mt-8",
        ),
        data_show="$step === 3",
    )


def _review_field(label: str, signal: str, mapping: dict[str, str] | None = None):
    """A review row showing label + signal value."""
    if mapping:
        # For mapped values, show the label from the mapping
        # We use data-text with a ternary chain
        conditions = " : ".join(
            f"${signal} === '{k}' ? '{v}'" for k, v in mapping.items()
        )
        value_node = Span(
            data_text=f"{conditions} : ${signal}",
            class_="text-sm font-medium text-gray-900",
        )
    else:
        value_node = Span(
            data_text=f"${signal} || '—'",
            class_="text-sm font-medium text-gray-900",
        )
    return Div(
        Span(label, class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
        value_node,
        class_="flex flex-col gap-0.5 py-2",
    )


def step_review():
    """Step 4: Review all data before submitting."""
    return Div(
        H3("Review Your Details", class_="text-lg font-semibold text-gray-800 mb-1"),
        P("Please confirm everything looks correct.", class_="text-sm text-gray-500 mb-6"),

        # Review grid
        Div(
            # Personal
            H3("Personal", class_="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2 col-span-full"),
            _review_field("Name", "name"),
            _review_field("Email", "email"),
            _review_field("Phone", "phone"),
            class_="grid grid-cols-3 gap-x-6 divide-x-0 border-b border-gray-100 pb-4 mb-4",
        ),
        Div(
            H3("Professional", class_="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2 col-span-full"),
            _review_field("Company", "company"),
            _review_field("Role", "role", ROLES),
            _review_field("Experience", "experience", {k: v[0] for k, v in EXPERIENCE.items()}),
            class_="grid grid-cols-3 gap-x-6 border-b border-gray-100 pb-4 mb-4",
        ),
        Div(
            H3("Preferences", class_="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2 col-span-full"),
            _review_field("Theme", "theme", THEMES),
            _review_field("Newsletter", "newsletter", {"yes": "Subscribed", "no": "Not subscribed"}),
            _review_field("Bio", "bio"),
            class_="grid grid-cols-3 gap-x-6 pb-4 mb-4",
        ),

        # Navigation
        Div(
            Button(
                "\u2190 Back",
                on_click="$step = 3",
                class_=(
                    "px-6 py-2.5 rounded-lg text-sm font-semibold "
                    "text-gray-600 bg-gray-100 hover:bg-gray-200 "
                    "active:scale-95 transition-all"
                ),
            ),
            Button(
                "Submit \u2713",
                on_click=action(Registration.submit),
                class_=(
                    "px-8 py-2.5 rounded-lg text-sm font-semibold text-white "
                    "bg-emerald-500 hover:bg-emerald-600 active:scale-95 "
                    "transition-all shadow-sm"
                ),
            ),
            class_="flex justify-between mt-8",
        ),
        data_show="$step === 4",
    )


def stats_bar():
    """Summary stats for submissions."""
    regs = Registration.all()
    count = len(regs)
    roles = {}
    for r in regs:
        roles[r.role] = roles.get(r.role, 0) + 1
    top_role = max(roles, key=roles.get) if roles else None
    top_role_label = ROLES.get(top_role, "—") if top_role else "—"

    return Div(
        Div(
            Span("Registrations", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
            Span(str(count), class_="text-2xl font-bold tabular-nums text-gray-900 mt-0.5"),
            class_="flex flex-col",
        ),
        Div(
            Span("Top Role", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
            Span(top_role_label, class_="text-lg font-semibold text-gray-900 mt-0.5"),
            class_="flex flex-col",
        ),
        Div(
            Span("Newsletter", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
            Span(
                f"{sum(1 for r in regs if r.newsletter == 'yes')}/{count}" if count else "—",
                class_="text-lg font-semibold text-gray-900 mt-0.5 tabular-nums",
            ),
            class_="flex flex-col",
        ),
        id="stats-bar",
        class_="flex gap-8 bg-white rounded-xl border border-gray-200 p-5 shadow-sm",
    )


def registration_row(reg: Registration):
    """A single registration entry."""
    role_label = ROLES.get(reg.role, reg.role)
    exp_label = EXPERIENCE.get(reg.experience, (reg.experience,))[0]
    initial = reg.name[0].upper() if reg.name else "?"

    # Color by role
    role_colors = {
        "developer": "bg-blue-500",
        "designer": "bg-pink-500",
        "manager": "bg-violet-500",
        "analyst": "bg-emerald-500",
        "other": "bg-gray-500",
    }
    color = role_colors.get(reg.role, "bg-gray-500")

    return Div(
        # Avatar
        Div(
            Span(initial, class_="text-white text-sm font-bold"),
            class_=f"w-9 h-9 rounded-full {color} flex items-center justify-center shrink-0",
        ),
        # Info
        Div(
            Div(
                Span(reg.name, class_="text-sm font-semibold text-gray-800"),
                Span(
                    f"{role_label} \u00b7 {exp_label}",
                    class_="text-xs text-gray-400 ml-2",
                ),
                class_="flex items-baseline gap-1",
            ),
            Div(
                Span(reg.email, class_="text-xs text-gray-500"),
                Span(f" \u00b7 {reg.company}" if reg.company else "", class_="text-xs text-gray-400"),
                class_="flex items-center",
            ),
            class_="flex flex-col min-w-0",
        ),
        # Timestamp
        Span(reg.submitted_at, class_="text-xs text-gray-400 shrink-0 hidden sm:inline"),
        # Delete
        Button(
            "\u00d7",
            title="Delete registration",
            class_=(
                "w-6 h-6 rounded text-gray-300 hover:text-red-500 "
                "hover:bg-red-50 transition-all text-sm flex items-center "
                "justify-center opacity-0 group-hover:opacity-100 shrink-0"
            ),
            on_click=action(reg.remove),
        ),
        class_=(
            "group flex items-center gap-3 px-4 py-3 "
            "border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors"
        ),
    )


def submissions_list():
    """List of all registrations — replaced by SSE."""
    regs = Registration.all()
    regs.sort(key=lambda r: r.submitted_at, reverse=True)

    if not regs:
        return Div(
            P(
                "No registrations yet. Complete the wizard above!",
                class_="text-gray-400 text-center text-sm italic py-8",
            ),
            id="submissions",
        )

    return Div(
        *[registration_row(r) for r in regs],
        id="submissions",
        class_="bg-white rounded-xl border border-gray-200 overflow-hidden",
    )


def wizard_page():
    """Full page layout — progress + form steps + submissions list."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Wizard", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Multi-step form with signal-driven navigation",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Wizard card
            Div(
                # Progress bar
                progress_bar(),

                # All steps (shown/hidden by data-show)
                step_personal(),
                step_professional(),
                step_preferences(),
                step_review(),

                class_="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm",
                data_signals=(
                    "{"
                    "step: 1, "
                    "name: '', "
                    "email: '', "
                    "phone: '', "
                    "company: '', "
                    "role: 'developer', "
                    "experience: 'mid', "
                    "theme: 'system', "
                    "newsletter: 'yes', "
                    "bio: ''"
                    "}"
                ),
            ),

            # Submissions section
            Div(
                Div(
                    H2(
                        "Registrations",
                        class_="text-xs font-bold uppercase tracking-wider text-gray-400",
                    ),
                    class_="mb-3",
                ),
                stats_bar(),
                Div(class_="h-4"),
                submissions_list(),
                class_="mt-10",
            ),

            # Footer
            Div(
                P(
                    "Steps are client-side (signals) \u2014 only Submit hits the server",
                    class_="text-xs text-gray-400 mt-8 text-center",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-2xl mx-auto px-6 py-12",
        ),
        title="Nitro Wizard",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroWizard")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    Registration.repository().init_db()


@app.get("/")
async def homepage(request: Request):
    return html(str(wizard_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8012, debug=True, auto_reload=True)
