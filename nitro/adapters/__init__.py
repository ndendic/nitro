"""
Nitro Adapters - Integration with web frameworks

This module provides framework-specific adapters for auto-routing:
- Sanic adapter (recommended)
- FastAPI adapter
- Flask adapter
- Starlette adapter
- FastHTML adapter (deprecated — use Starlette)

Each adapter provides a configure_nitro(app) function that registers
catch-all routes for event-driven action dispatch.
"""

__all__: list[str] = []
