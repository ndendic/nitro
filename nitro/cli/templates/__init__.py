"""Template system for StarUI files."""

from .app_starter import generate_app_starter
from .boost_base import generate_boost_base, generate_boost_components
from .boost_main import generate_boost_main
from .css_input import generate_css_input
from .env_example import generate_env_example

__all__ = [
    "generate_css_input",
    "generate_app_starter",
    "generate_boost_base",
    "generate_boost_components",
    "generate_boost_main",
    "generate_env_example",
]
