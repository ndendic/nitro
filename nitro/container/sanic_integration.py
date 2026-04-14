"""
Sanic lifecycle integration for the Nitro dependency injection container.

One-line setup::

    from sanic import Sanic
    from nitro.container import Container, sanic_container

    app = Sanic("MyApp")
    container = Container()
    sanic_container(app, container)

After calling ``sanic_container()``:

- A fresh :class:`~nitro.container.container.ScopedContainer` is created for each
  incoming request and stored on ``request.ctx.container``.
- The scoped container is cleaned up (``on_destroy`` callbacks fired) after
  each response.
- All Singleton providers are destroyed when the server stops.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sanic import Sanic

    from .container import Container

logger = logging.getLogger("nitro.container.sanic")


def sanic_container(app: "Sanic", container: "Container") -> None:
    """Wire a :class:`~nitro.container.Container` into a Sanic app's lifecycle.

    Registers the following lifecycle hooks:

    - ``before_server_stop`` — destroys all Singleton providers on shutdown.
    - ``on_request`` — creates a per-request :class:`ScopedContainer` stored as
      ``request.ctx.container``.
    - ``on_response`` — cleans up the request-scoped container.

    Args:
        app: Sanic application instance.
        container: Container to manage.

    Example::

        @app.get("/")
        async def index(request):
            db = await request.ctx.container.resolve(DatabasePool)
            ...
    """

    @app.before_server_stop
    async def _destroy_container(app, loop):
        await container.destroy_singletons()
        logger.info("Container singletons destroyed for Sanic app %r", app.name)

    @app.on_request
    async def _create_request_scope(request):
        import uuid

        from .container import ScopedContainer

        scope_id = f"req-{uuid.uuid4().hex[:12]}"
        request.ctx.container = ScopedContainer(container, scope_id)

    @app.on_response
    async def _cleanup_request_scope(request, response):
        scoped = getattr(request.ctx, "container", None)
        if scoped is not None:
            await scoped._cleanup()
