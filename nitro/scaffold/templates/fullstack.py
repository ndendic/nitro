"""Fullstack template file generators.

The fullstack template extends auth with:
- CRUD auto-views via nitro.crud.register_crud_routes
- i18n via nitro.i18n.configure_i18n
- Locale JSON catalogs (English + Serbian)
"""

from __future__ import annotations

from .auth import generate_auth_files


def _main_py_fullstack(project_name: str) -> str:
    return f'''"""{{project_name}} — Built with Nitro (fullstack template)."""
from sanic import Sanic
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.health import HealthRegistry, DatabaseCheck, MemoryCheck, sanic_health
from nitro.logging import configure_logging, get_logger, request_logging_middleware
from nitro.crud import register_crud_routes, CRUDConfig
from nitro.i18n import configure_i18n

from settings import AppConfig
from entities import Item, data_init
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

# i18n — load locale catalogs from the locales/ directory
configure_i18n(app, "locales/", default_locale="en")

# CRUD auto-views for Item entity
register_crud_routes(app, Item, config=CRUDConfig(title="Items", icon="package"))


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


def _locales_en() -> str:
    return '''{
  "nav.home": "Home",
  "nav.dashboard": "Dashboard",
  "nav.items": "Items",
  "nav.logout": "Logout",
  "auth.login": "Sign In",
  "auth.register": "Register",
  "auth.email": "Email",
  "auth.password": "Password",
  "auth.welcome": "Welcome, {email}!",
  "items.title": "Items",
  "items.create": "Create Item",
  "items.name": "Name",
  "items.description": "Description",
  "items.active": "Active",
  "common.save": "Save",
  "common.cancel": "Cancel",
  "common.delete": "Delete",
  "common.edit": "Edit"
}
'''


def _locales_sr() -> str:
    return '''{
  "nav.home": "Početna",
  "nav.dashboard": "Kontrolna tabla",
  "nav.items": "Stavke",
  "nav.logout": "Odjava",
  "auth.login": "Prijava",
  "auth.register": "Registracija",
  "auth.email": "E-mail",
  "auth.password": "Lozinka",
  "auth.welcome": "Dobrodošli, {email}!",
  "items.title": "Stavke",
  "items.create": "Kreiraj stavku",
  "items.name": "Naziv",
  "items.description": "Opis",
  "items.active": "Aktivno",
  "common.save": "Sačuvaj",
  "common.cancel": "Otkaži",
  "common.delete": "Obriši",
  "common.edit": "Izmeni"
}
'''


def generate_fullstack_files(project_name: str) -> dict[str, str]:
    """Return the file map for the fullstack template.

    Builds on top of the auth template by replacing main.py and
    adding locale catalog files.

    Args:
        project_name: Human-readable project name used in generated code.

    Returns:
        Mapping of filename → file content.
    """
    files = generate_auth_files(project_name)
    # Replace main.py with the fullstack version
    files["main.py"] = _main_py_fullstack(project_name)
    # Add locale catalogs
    files["locales/en.json"] = _locales_en()
    files["locales/sr.json"] = _locales_sr()
    return files
