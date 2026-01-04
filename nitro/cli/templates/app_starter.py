"""StarHTML app starter template."""

from pathlib import Path

from nitro.config import NitroConfig, TailwindConfig

APP_TEMPLATE = """\
from nitro import *

...
"""


def generate_app_starter(config: NitroConfig | None = None, **_) -> str:
    """Generate Nitro app starter with theme system."""
    if config is None:
        tailwind = TailwindConfig(
            css_output=Path("output.css"),
        )
        config = NitroConfig(
            project_root=Path.cwd(),
            tailwind=tailwind,
        )

    css_path = str(config.css_output_absolute)
    if not css_path.startswith("/"):
        css_path = "/" + css_path

    return APP_TEMPLATE.format(css_path=css_path)
