"""nitro.scaffold — Production app template generator.

Generates complete, runnable Sanic+Nitro projects from composable templates.

Templates:
- ``minimal``   — Settings, health checks, structured logging, one entity.
- ``auth``      — Extends minimal with user auth and cookie sessions.
- ``fullstack``  — Extends auth with CRUD auto-views and i18n.

Quick start::

    from nitro.scaffold import ScaffoldConfig, generate_project

    config = ScaffoldConfig(name="myapp", template="auth")
    files = generate_project(config)
    # files is a dict[str, str]: filename → content
    for filename, content in files.items():
        print(filename)

CLI::

    nitro create myapp --template fullstack
"""

from .config import ScaffoldConfig, TemplateChoice, TEMPLATE_DESCRIPTIONS
from .generator import generate_project

__all__ = [
    "ScaffoldConfig",
    "TemplateChoice",
    "TEMPLATE_DESCRIPTIONS",
    "generate_project",
]
