"""
Sanic Auth — Login & Registration with Protected Dashboard

Demonstrates:
  1. User registration & login with server-side session management
  2. Protected routes — dashboard only accessible when authenticated
  3. Conditional UI rendering based on auth state (signal-driven show/hide)
  4. Server-side session tokens — login returns a token, all actions validate it
  5. Password hashing (hashlib, demo-quality) — never store plaintext
  6. Multi-region SSE updates for auth state transitions

New patterns vs. prior examples:
  - Server-side session store (dict of token → user_id)
  - Auth-gated actions: method checks session before executing
  - Full-page SSE swap on login/logout (auth-page ↔ dashboard)
  - Form validation with inline error display via SSE signal patch
  - Profile editing on authenticated entity

Run:
    cd nitro && python examples/sanic_auth_app.py
    Then visit http://localhost:8017
"""
import uuid
import hashlib
import secrets
from datetime import datetime, timezone

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import (
    Div, H1, H2, H3, P, Span, Button, Input, Label, A,
)

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Session store (server-side, in-memory for demo)
# ---------------------------------------------------------------------------

_sessions: dict[str, str] = {}  # token → user_id


def _hash_password(password: str) -> str:
    """Simple hash for demo. Use bcrypt/argon2 in production."""
    return hashlib.sha256(password.encode()).hexdigest()


def _get_current_user(token: str):
    """Look up user by session token."""
    user_id = _sessions.get(token)
    if not user_id:
        return None
    return User.get(user_id)


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

class User(Entity, table=True):
    """A registered user."""
    __tablename__ = "auth_user"
    email: str = ""
    display_name: str = ""
    password_hash: str = ""
    created_at: str = ""

    @classmethod
    @post()
    def register(cls, reg_email: str = "", reg_name: str = "",
                 reg_password: str = "", reg_confirm: str = "", request=None):
        """Register a new user account."""
        reg_email = reg_email.strip().lower()
        reg_name = reg_name.strip()
        reg_password = reg_password.strip()
        reg_confirm = reg_confirm.strip()

        # Validation
        if not reg_email or not reg_name or not reg_password:
            publish_sync("sse", SSE.patch_signals({"auth_error": "All fields are required."}))
            return {"error": "missing_fields"}

        if "@" not in reg_email:
            publish_sync("sse", SSE.patch_signals({"auth_error": "Invalid email address."}))
            return {"error": "invalid_email"}

        if len(reg_password) < 4:
            publish_sync("sse", SSE.patch_signals({"auth_error": "Password must be at least 4 characters."}))
            return {"error": "weak_password"}

        if reg_password != reg_confirm:
            publish_sync("sse", SSE.patch_signals({"auth_error": "Passwords do not match."}))
            return {"error": "mismatch"}

        # Check duplicate email
        existing = [u for u in cls.all() if u.email == reg_email]
        if existing:
            publish_sync("sse", SSE.patch_signals({"auth_error": "Email already registered."}))
            return {"error": "duplicate"}

        # Create user
        user = cls(
            id=uuid.uuid4().hex[:8],
            email=reg_email,
            display_name=reg_name,
            password_hash=_hash_password(reg_password),
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        )
        user.save()

        # Auto-login
        token = secrets.token_hex(16)
        _sessions[token] = user.id
        publish_sync("sse", SSE.patch_signals({
            "session_token": token, "auth_error": "",
            "reg_email": "", "reg_name": "", "reg_password": "", "reg_confirm": "",
        }))
        publish_sync("sse", SSE.patch_elements(app_shell(user), selector="#app-shell"))
        return {"id": user.id}

    @classmethod
    @post()
    def login(cls, login_email: str = "", login_password: str = "", request=None):
        """Authenticate and create a session."""
        login_email = login_email.strip().lower()
        login_password = login_password.strip()

        if not login_email or not login_password:
            publish_sync("sse", SSE.patch_signals({"auth_error": "Email and password required."}))
            return {"error": "missing"}

        # Find user
        matches = [u for u in cls.all() if u.email == login_email]
        if not matches or matches[0].password_hash != _hash_password(login_password):
            publish_sync("sse", SSE.patch_signals({"auth_error": "Invalid email or password."}))
            return {"error": "invalid"}

        user = matches[0]
        token = secrets.token_hex(16)
        _sessions[token] = user.id
        publish_sync("sse", SSE.patch_signals({
            "session_token": token, "auth_error": "",
            "login_email": "", "login_password": "",
        }))
        publish_sync("sse", SSE.patch_elements(app_shell(user), selector="#app-shell"))
        return {"id": user.id}

    @classmethod
    @post()
    def logout(cls, session_token: str = "", request=None):
        """Destroy the session and return to login."""
        _sessions.pop(session_token, None)
        publish_sync("sse", SSE.patch_signals({"session_token": "", "auth_error": "", "show_register": False}))
        publish_sync("sse", SSE.patch_elements(app_shell(None), selector="#app-shell"))
        return {"ok": True}

    @post()
    def update_profile(self, new_name: str = "", session_token: str = "", request=None):
        """Update display name (authenticated)."""
        user = _get_current_user(session_token)
        if not user or user.id != self.id:
            publish_sync("sse", SSE.patch_signals({"profile_msg": "Not authorized."}))
            return {"error": "unauthorized"}
        new_name = new_name.strip()
        if not new_name:
            publish_sync("sse", SSE.patch_signals({"profile_msg": "Name cannot be empty."}))
            return {"error": "empty"}
        self.display_name = new_name
        self.save()
        publish_sync("sse", SSE.patch_signals({"profile_msg": "Profile updated!", "new_name": ""}))
        publish_sync("sse", SSE.patch_elements(dashboard_header(self), selector="#dashboard-header"))
        return {"ok": True}


# ---------------------------------------------------------------------------
# Components — Auth forms
# ---------------------------------------------------------------------------

def input_field(label_text: str, bind: str, type_: str = "text", placeholder: str = ""):
    """Reusable form input with label."""
    return Div(
        Label(label_text, class_="text-xs font-semibold text-gray-600 mb-1 block"),
        Input(
            type=type_,
            placeholder=placeholder,
            bind=bind,
            class_=(
                "w-full px-3 py-2.5 rounded-xl border border-gray-200 "
                "bg-gray-50 focus:bg-white focus:border-blue-400 "
                "focus:ring-2 focus:ring-blue-100 outline-none "
                "transition-all text-sm"
            ),
        ),
        class_="mb-3",
    )


def error_banner():
    """Inline error message — shown when auth_error signal is set."""
    return Div(
        Div(
            Span(
                "⚠",
                class_="text-red-400 mr-2",
            ),
            Span(
                data_text="$auth_error",
                class_="text-red-600 text-sm font-medium",
            ),
            class_="flex items-center",
        ),
        id="error-banner",
        class_=(
            "bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-4"
        ),
        data_show="$auth_error !== ''",
        style="display:none",
    )


def login_form():
    """Login form panel."""
    return Div(
        H2("Welcome back", class_="text-xl font-bold text-gray-900 mb-1"),
        P("Sign in to your account", class_="text-sm text-gray-500 mb-6"),
        error_banner(),
        input_field("Email", "login_email", type_="email", placeholder="you@example.com"),
        input_field("Password", "login_password", type_="password", placeholder="Your password"),
        Button(
            "Sign In",
            class_=(
                "w-full py-2.5 rounded-xl font-semibold text-white "
                "bg-gray-900 hover:bg-gray-800 active:scale-[0.98] "
                "transition-all mt-2"
            ),
            on_click=action(User.login),
        ),
        Div(
            Span("Don't have an account?", class_="text-sm text-gray-500"),
            Button(
                "Register",
                class_="text-sm text-blue-600 font-semibold hover:underline ml-1",
                on_click="$show_register = true; $auth_error = ''",
            ),
            class_="flex items-center justify-center mt-4",
        ),
        data_show="!$show_register",
        class_="p-8",
    )


def register_form():
    """Registration form panel."""
    return Div(
        H2("Create account", class_="text-xl font-bold text-gray-900 mb-1"),
        P("Get started with a free account", class_="text-sm text-gray-500 mb-6"),
        error_banner(),
        input_field("Display Name", "reg_name", placeholder="Your name"),
        input_field("Email", "reg_email", type_="email", placeholder="you@example.com"),
        input_field("Password", "reg_password", type_="password", placeholder="At least 4 characters"),
        input_field("Confirm Password", "reg_confirm", type_="password", placeholder="Re-enter password"),
        Button(
            "Create Account",
            class_=(
                "w-full py-2.5 rounded-xl font-semibold text-white "
                "bg-blue-500 hover:bg-blue-600 active:scale-[0.98] "
                "transition-all mt-2"
            ),
            on_click=action(User.register),
        ),
        Div(
            Span("Already have an account?", class_="text-sm text-gray-500"),
            Button(
                "Sign in",
                class_="text-sm text-blue-600 font-semibold hover:underline ml-1",
                on_click="$show_register = false; $auth_error = ''",
            ),
            class_="flex items-center justify-center mt-4",
        ),
        data_show="$show_register",
        style="display:none",
        class_="p-8",
    )


def auth_page():
    """Login / Register page — shown when not authenticated."""
    return Div(
        Div(
            # Logo area
            Div(
                Div(
                    Span("N", class_="text-white text-xl font-bold"),
                    class_=(
                        "w-12 h-12 rounded-2xl bg-gradient-to-br "
                        "from-blue-500 to-violet-500 flex items-center "
                        "justify-center shadow-lg"
                    ),
                ),
                H1("Nitro Auth", class_="text-2xl font-bold text-gray-900 mt-4"),
                P(
                    "Secure authentication demo",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),
            # Card with both forms
            Div(
                login_form(),
                register_form(),
                class_=(
                    "bg-white rounded-2xl border border-gray-200 "
                    "shadow-lg overflow-hidden"
                ),
            ),
            # Footer
            P(
                "Demo app — passwords are hashed but stored in-memory",
                class_="text-xs text-gray-400 mt-6 text-center",
            ),
            class_="w-full max-w-sm",
        ),
        id="auth-page",
        class_=(
            "min-h-screen flex items-center justify-center "
            "bg-gradient-to-br from-gray-50 to-gray-100 px-4"
        ),
    )


# ---------------------------------------------------------------------------
# Components — Dashboard (protected)
# ---------------------------------------------------------------------------

def dashboard_header(user: User):
    """Dashboard top bar with user info and logout."""
    return Div(
        Div(
            # Avatar
            Div(
                Span(
                    user.display_name[0].upper() if user.display_name else "?",
                    class_="text-white text-sm font-bold",
                ),
                class_=(
                    "w-9 h-9 rounded-full bg-gradient-to-br "
                    "from-blue-500 to-violet-500 flex items-center "
                    "justify-center"
                ),
            ),
            Div(
                P(user.display_name, class_="text-sm font-semibold text-gray-900"),
                P(user.email, class_="text-xs text-gray-500"),
            ),
            class_="flex items-center gap-3",
        ),
        Button(
            "Sign Out",
            class_=(
                "px-4 py-2 rounded-xl text-sm font-medium "
                "text-gray-600 hover:text-red-600 hover:bg-red-50 "
                "transition-all"
            ),
            on_click=action(User.logout),
        ),
        id="dashboard-header",
        class_="flex items-center justify-between mb-8",
    )


def stat_card(label: str, value: str, color: str = "blue"):
    """A simple stat card for the dashboard."""
    color_map = {
        "blue": "from-blue-500 to-blue-600",
        "violet": "from-violet-500 to-violet-600",
        "emerald": "from-emerald-500 to-emerald-600",
    }
    gradient = color_map.get(color, color_map["blue"])
    return Div(
        Div(
            P(label, class_="text-xs font-medium text-white/80"),
            P(value, class_="text-2xl font-bold text-white mt-1"),
            class_="p-5",
        ),
        class_=f"rounded-2xl bg-gradient-to-br {gradient} shadow-md",
    )


def profile_section(user: User):
    """Profile editing section."""
    return Div(
        H3("Profile", class_="text-sm font-semibold text-gray-900 mb-4"),
        Div(
            Div(
                Label("Display Name", class_="text-xs font-medium text-gray-600 mb-1 block"),
                Div(
                    Input(
                        type="text",
                        placeholder=user.display_name,
                        bind="new_name",
                        class_=(
                            "flex-1 px-3 py-2 rounded-xl border border-gray-200 "
                            "bg-gray-50 focus:bg-white focus:border-blue-400 "
                            "outline-none transition-all text-sm"
                        ),
                    ),
                    Button(
                        "Update",
                        class_=(
                            "px-4 py-2 rounded-xl text-sm font-medium "
                            "bg-gray-900 text-white hover:bg-gray-800 "
                            "active:scale-[0.98] transition-all"
                        ),
                        on_click=action(user.update_profile),
                    ),
                    class_="flex gap-2",
                ),
            ),
            Div(
                Label("Email", class_="text-xs font-medium text-gray-600 mb-1 block"),
                P(user.email, class_="text-sm text-gray-700 py-2"),
            ),
            Div(
                Label("Member Since", class_="text-xs font-medium text-gray-600 mb-1 block"),
                P(user.created_at, class_="text-sm text-gray-700 py-2"),
            ),
            class_="space-y-4",
        ),
        # Profile update message
        Div(
            Span(
                data_text="$profile_msg",
                class_="text-sm text-emerald-600 font-medium",
            ),
            data_show="$profile_msg !== ''",
            style="display:none",
            class_="mt-3",
        ),
        class_=(
            "bg-white rounded-2xl border border-gray-200 "
            "shadow-sm p-6"
        ),
    )


def activity_section():
    """Placeholder activity feed."""
    items = [
        ("Logged in", "Just now"),
        ("Account created", "Today"),
    ]
    return Div(
        H3("Recent Activity", class_="text-sm font-semibold text-gray-900 mb-4"),
        Div(
            *[
                Div(
                    Div(
                        class_="w-2 h-2 rounded-full bg-blue-400 mt-1.5 shrink-0",
                    ),
                    Div(
                        P(text, class_="text-sm text-gray-700"),
                        P(time, class_="text-xs text-gray-400"),
                    ),
                    class_="flex gap-3",
                )
                for text, time in items
            ],
            class_="space-y-3",
        ),
        class_=(
            "bg-white rounded-2xl border border-gray-200 "
            "shadow-sm p-6"
        ),
    )


def dashboard(user: User):
    """Full dashboard — shown when authenticated."""
    total_users = len(User.all())
    active_sessions = len(_sessions)

    return Div(
        Div(
            dashboard_header(user),

            # Welcome
            Div(
                H1(
                    f"Hello, {user.display_name}",
                    class_="text-2xl font-bold text-gray-900",
                ),
                P(
                    "Welcome to your protected dashboard",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="mb-8",
            ),

            # Stats row
            Div(
                stat_card("Total Users", str(total_users), "blue"),
                stat_card("Active Sessions", str(active_sessions), "violet"),
                stat_card("Your ID", user.id, "emerald"),
                class_="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8",
            ),

            # Two columns: profile + activity
            Div(
                profile_section(user),
                activity_section(),
                class_="grid grid-cols-1 md:grid-cols-2 gap-4",
            ),

            # Footer
            P(
                "Open in multiple tabs — login/logout syncs across all sessions",
                class_="text-xs text-gray-400 mt-8 text-center",
            ),

            class_="max-w-4xl mx-auto px-6 py-12",
        ),
        id="dashboard-page",
        class_="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100",
    )


# ---------------------------------------------------------------------------
# App shell — switches between auth and dashboard
# ---------------------------------------------------------------------------

def app_shell(user=None):
    """Top-level shell. Renders auth page or dashboard based on user."""
    if user:
        return Div(
            dashboard(user),
            id="app-shell",
        )
    return Div(
        auth_page(),
        id="app-shell",
    )


def full_page(user=None):
    """Complete HTML page with signals and SSE."""
    return Page(
        Div(
            app_shell(user),
            Div(
                data_signals=(
                    "{session_token: '', show_register: false, auth_error: '', "
                    "login_email: '', login_password: '', "
                    "reg_email: '', reg_name: '', reg_password: '', reg_confirm: '', "
                    "new_name: '', profile_msg: ''}"
                ),
                data_init="@get('/sse')",
                style="display:none",
            ),
        ),
        title="Nitro Auth",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroAuth")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    User.repository().init_db()


@app.get("/")
async def homepage(request: Request):
    return html(str(full_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8017, debug=True, auto_reload=True)
