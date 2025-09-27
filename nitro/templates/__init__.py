"""Template system for StarUI files."""

from .app_starter import generate_app_starter
from .css_input import generate_css_input

__all__ = [
    "generate_css_input",
    "generate_app_starter",
]
