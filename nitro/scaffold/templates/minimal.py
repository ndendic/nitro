"""Minimal template file generators.

The minimal template produces a production-ready Sanic+Nitro starter with:
- Structured logging
- Health checks (database + memory)
- AppSettings-based configuration
- One example entity
"""

from __future__ import annotations


def _main_py(project_name: str) -> str:
    return f'''"""{{project_name}} — Built with Nitro."""
from sanic import Sanic
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.health import HealthRegistry, DatabaseCheck, MemoryCheck, sanic_health
from nitro.logging import configure_logging, get_logger, request_logging_middleware

from settings import AppConfig
from entities import data_init

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
app.middleware("request")(request_logging_middleware)


@app.before_server_start
async def setup(app, loop):
    data_init()
    log.info("Server ready", extra={{"port": config.server.port}})


@app.get("/")
async def index(request):
    from nitro.html import Page
    from rusty_tags import Div, H1, P
    return Page(
        Div(
            H1("{project_name}"),
            P("Powered by Nitro"),
            cls="container mx-auto p-8",
        ),
        title="{project_name}",
        datastar=True,
        tailwind4=True,
    ).to_response()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.server.port, debug=config.debug)
'''


def _settings_py() -> str:
    return '''from nitro.settings import AppSettings, Section, Secret


class ServerSection(Section):
    host: str = "0.0.0.0"
    port: int = 8000


class DatabaseSection(Section):
    url: str = "sqlite:///app.db"
    password: Secret = Secret("")


class AppConfig(AppSettings):
    server: ServerSection = ServerSection()
    db: DatabaseSection = DatabaseSection()
    debug: bool = False
'''


def _entities_py() -> str:
    return '''from nitro import Entity


class Item(Entity, table=True):
    name: str = ""
    description: str = ""
    active: bool = True


def data_init():
    Entity._repository.init_db()
'''


def _env_example() -> str:
    return '''# Application settings
# Copy this file to .env and edit values for your environment

# Server
APP_SERVER__HOST=0.0.0.0
APP_SERVER__PORT=8000

# Database
APP_DB__URL=sqlite:///app.db
APP_DB__PASSWORD=

# Debug mode (false in production)
APP_DEBUG=false
'''


def generate_minimal_files(project_name: str) -> dict[str, str]:
    """Return the file map for the minimal template.

    Args:
        project_name: Human-readable project name used in generated code.

    Returns:
        Mapping of filename → file content.
    """
    return {
        "main.py": _main_py(project_name),
        "settings.py": _settings_py(),
        "entities.py": _entities_py(),
        ".env.example": _env_example(),
    }
