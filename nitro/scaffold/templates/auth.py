"""Auth template file generators.

The auth template extends minimal with:
- AuthService-based user registration and login
- MemorySessionStore + cookie session middleware
- Login, register, dashboard, and logout views
"""

from __future__ import annotations

from .minimal import generate_minimal_files


def _auth_views_py(project_name: str) -> str:
    return f'''"""Authentication views for {project_name}."""
from sanic import Sanic
from sanic.response import html as html_response, redirect
from nitro.auth import AuthService, User, require_auth
from nitro.sessions import MemorySessionStore, sanic_sessions
from nitro.html import Page
from rusty_tags import Div, Form, Input, Button, H1, H2, P, A, Label, Span

# Shared auth service and session store — wire these in main.py
auth = AuthService(secret="change-me-in-production")
session_store = MemorySessionStore(ttl=3600)


def register_auth(app: Sanic) -> None:
    """Register auth routes and session middleware on *app*."""
    sanic_sessions(app, session_store, secret="change-me-in-production")

    app.add_route(login_page, "/login", methods=["GET"])
    app.add_route(login_handler, "/login", methods=["POST"])
    app.add_route(register_page, "/register", methods=["GET"])
    app.add_route(register_handler, "/register", methods=["POST"])
    app.add_route(logout_handler, "/logout", methods=["GET"])
    app.add_route(dashboard, "/dashboard", methods=["GET"])


async def login_page(request):
    page = Page(
        Div(
            H1("Sign In"),
            Form(
                Div(
                    Label("Email", for_="email"),
                    Input(type="email", id="email", name="email", required=True,
                          cls="border rounded px-3 py-2 w-full"),
                    cls="mb-4",
                ),
                Div(
                    Label("Password", for_="password"),
                    Input(type="password", id="password", name="password", required=True,
                          cls="border rounded px-3 py-2 w-full"),
                    cls="mb-6",
                ),
                Button("Sign In", type="submit",
                       cls="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"),
                method="POST",
                action="/login",
            ),
            P(A("Don't have an account? Register", href="/register",
                cls="text-blue-600 hover:underline"),
              cls="mt-4 text-center"),
            cls="max-w-md mx-auto mt-16 p-8 border rounded-lg shadow",
        ),
        title="Sign In — {project_name}",
        tailwind4=True,
    )
    return html_response(str(page))


async def login_handler(request):
    email = request.form.get("email", "")
    password = request.form.get("password", "")

    result = auth.authenticate(email, password)
    if not result:
        page = Page(
            Div(
                H1("Sign In"),
                Span("Invalid email or password.", cls="text-red-600"),
                A("Try again", href="/login", cls="block mt-4 text-blue-600"),
                cls="max-w-md mx-auto mt-16 p-8 border rounded-lg shadow",
            ),
            title="Sign In — {project_name}",
            tailwind4=True,
        )
        return html_response(str(page))

    user, access_token, _ = result
    session = request.ctx.session
    session["user_id"] = user.id
    session["user_email"] = user.email
    return redirect("/dashboard")


async def register_page(request):
    page = Page(
        Div(
            H1("Create Account"),
            Form(
                Div(
                    Label("Email", for_="email"),
                    Input(type="email", id="email", name="email", required=True,
                          cls="border rounded px-3 py-2 w-full"),
                    cls="mb-4",
                ),
                Div(
                    Label("Password", for_="password"),
                    Input(type="password", id="password", name="password", required=True,
                          cls="border rounded px-3 py-2 w-full"),
                    cls="mb-6",
                ),
                Button("Register", type="submit",
                       cls="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"),
                method="POST",
                action="/register",
            ),
            P(A("Already have an account? Sign in", href="/login",
                cls="text-blue-600 hover:underline"),
              cls="mt-4 text-center"),
            cls="max-w-md mx-auto mt-16 p-8 border rounded-lg shadow",
        ),
        title="Register — {project_name}",
        tailwind4=True,
    )
    return html_response(str(page))


async def register_handler(request):
    email = request.form.get("email", "")
    password = request.form.get("password", "")

    try:
        user = auth.register(email, password)
    except ValueError as exc:
        page = Page(
            Div(
                H1("Register"),
                Span(str(exc), cls="text-red-600"),
                A("Try again", href="/register", cls="block mt-4 text-blue-600"),
                cls="max-w-md mx-auto mt-16 p-8 border rounded-lg shadow",
            ),
            title="Register — {project_name}",
            tailwind4=True,
        )
        return html_response(str(page))

    session = request.ctx.session
    session["user_id"] = user.id
    session["user_email"] = user.email
    return redirect("/dashboard")


async def logout_handler(request):
    session = request.ctx.session
    session.clear()
    return redirect("/login")


async def dashboard(request):
    session = request.ctx.session
    user_email = session.get("user_email")

    if not user_email:
        return redirect("/login")

    page = Page(
        Div(
            H2(f"Welcome, {{user_email}}"),
            P("You are logged in."),
            A("Logout", href="/logout", cls="text-red-600 hover:underline"),
            cls="container mx-auto p-8",
        ),
        title="Dashboard — {project_name}",
        tailwind4=True,
    )
    return html_response(str(page))
'''


def _main_py_auth(project_name: str) -> str:
    return f'''"""{{project_name}} — Built with Nitro (auth template)."""
from sanic import Sanic
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.health import HealthRegistry, DatabaseCheck, MemoryCheck, sanic_health
from nitro.logging import configure_logging, get_logger, request_logging_middleware
from nitro.auth import AuthService

from settings import AppConfig
from entities import data_init
from auth_views import register_auth

configure_logging(level="DEBUG", pretty=True)
log = get_logger(__name__)

app = Sanic("{project_name}")
configure_nitro(app)

# Settings
config = AppConfig()

# Health checks
health = HealthRegistry(version="1.0.0")
health.register(DatabaseCheck())
health.register(MemoryCheck())
sanic_health(app, health)

# Logging middleware
request_logging_middleware(app)

# Auth + sessions
register_auth(app)


@app.before_server_start
async def setup(app):
    data_init()
    log.info("Server ready", extra={{"port": config.server.port}})


@app.get("/")
async def index(request):
    from sanic.response import redirect
    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.server.port, debug=config.debug)
'''


def generate_auth_files(project_name: str) -> dict[str, str]:
    """Return the file map for the auth template.

    Builds on top of the minimal template by replacing main.py and
    adding auth_views.py.

    Args:
        project_name: Human-readable project name used in generated code.

    Returns:
        Mapping of filename → file content.
    """
    files = generate_minimal_files(project_name)
    # Replace main.py with the auth-aware version
    files["main.py"] = _main_py_auth(project_name)
    # Add auth views
    files["auth_views.py"] = _auth_views_py(project_name)
    return files
