"""
Sanic integration helper for the Nitro storage module.

Attaches a storage backend to the Sanic application context and
provides a file upload handler helper.

Example::

    from sanic import Sanic
    from nitro.storage import MemoryBackend, sanic_storage

    app = Sanic("MyApp")
    sanic_storage(app, MemoryBackend())

    @app.post("/upload")
    async def upload(request):
        backend = request.app.ctx.storage
        f = request.files.get("file")
        result = await backend.put(f.name, f.body, content_type=f.type)
        return json(result.to_dict())
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import StorageBackend

if TYPE_CHECKING:
    pass  # Sanic types only needed for type-checking


def sanic_storage(app: object, backend: StorageBackend) -> None:
    """Attach a storage backend to a Sanic app.

    After calling this, the backend is available as ``request.app.ctx.storage``
    in every request handler.

    Args:
        app: A Sanic application instance.
        backend: The storage backend to use.
    """
    app.ctx.storage = backend  # type: ignore[attr-defined]

    @app.listener("after_server_stop")  # type: ignore[attr-defined]
    async def _close_storage(app_: object, loop: object) -> None:
        await backend.close()
