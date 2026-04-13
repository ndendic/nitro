"""Scaffold generator — returns a dict of filename → content.

No filesystem I/O happens here. The CLI layer is responsible for writing files.
"""

from __future__ import annotations

from nitro.scaffold.config import ScaffoldConfig
from nitro.scaffold.templates.minimal import generate_minimal_files
from nitro.scaffold.templates.auth import generate_auth_files
from nitro.scaffold.templates.fullstack import generate_fullstack_files


def generate_project(config: ScaffoldConfig) -> dict[str, str]:
    """Generate all project files for the given scaffold configuration.

    Args:
        config: A :class:`~nitro.scaffold.config.ScaffoldConfig` instance
            specifying the project name and template tier.

    Returns:
        A mapping of ``filename → content`` strings.  Keys may include
        subdirectory paths (e.g. ``"locales/en.json"``).  No filesystem
        writes are performed here.

    Raises:
        ValueError: If the template name is not recognised (caught by
            :class:`~nitro.scaffold.config.ScaffoldConfig` constructor).
    """
    name = config.name
    template = config.template

    dispatch = {
        "minimal": generate_minimal_files,
        "auth": generate_auth_files,
        "fullstack": generate_fullstack_files,
    }

    generator = dispatch[template]
    return generator(name)
