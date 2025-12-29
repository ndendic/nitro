"""
Nitro Adapters - Integration with web frameworks

This module provides framework-specific adapters for auto-routing:
- FastAPI adapter
- Flask adapter (Phase 2.1.4)
- FastHTML adapter (Phase 2.1.4)
- Starlette adapter (Phase 2.1.4)

Each adapter extends NitroDispatcher to provide framework-specific
route registration and parameter handling.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .fastapi import FastAPIDispatcher, configure_nitro as configure_fastapi

__all__ = ["FastAPIDispatcher", "configure_fastapi"]
