"""Template content generators for the scaffold module."""

from .minimal import generate_minimal_files
from .auth import generate_auth_files
from .fullstack import generate_fullstack_files

__all__ = [
    "generate_minimal_files",
    "generate_auth_files",
    "generate_fullstack_files",
]
