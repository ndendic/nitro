"""
nitro.container — Lightweight async-ready dependency injection for Nitro apps.

Provides:
- Container          : Core DI container with Singleton, Factory, and Scoped providers
- ScopedContainer    : Short-lived container for per-request or per-operation scopes
- Singleton          : Provider that creates one instance and reuses it
- Factory            : Provider that creates a new instance on every resolve
- Scoped             : Provider that creates one instance per scope context
- inject             : Decorator for auto-wiring dependencies via type hints
- sanic_container    : Sanic lifecycle hook registration

Quick start::

    from nitro.container import Container, Singleton, Factory, Scoped, inject

    container = Container()

    # Register providers
    container.register(DatabasePool, Singleton(lambda: DatabasePool("sqlite:///app.db")))
    container.register(RequestLogger, Factory(lambda: RequestLogger()))
    container.register(UnitOfWork, Scoped(lambda: UnitOfWork()))

    # Resolve
    db = await container.resolve(DatabasePool)          # same instance every time
    logger = await container.resolve(RequestLogger)     # new instance

    # Auto-wiring via type hints
    @inject(container)
    async def handle_request(db: DatabasePool, logger: RequestLogger):
        ...

    await handle_request()

    # Scoped context (e.g. per request)
    async with container.scope() as scoped:
        uow = await scoped.resolve(UnitOfWork)

    # Override for testing
    container.override(DatabasePool, Factory(lambda: MockDatabase()))

    # Sanic integration
    from nitro.container import sanic_container
    from sanic import Sanic

    app = Sanic("MyApp")
    sanic_container(app, container)   # auto request scope + shutdown cleanup

Lifecycle hooks::

    container.register(
        DatabasePool,
        Singleton(
            factory=lambda: DatabasePool("sqlite:///app.db"),
            on_init=lambda db: db.connect(),
            on_destroy=lambda db: db.close(),
        )
    )
"""

from .container import Container, ScopedContainer
from .decorators import inject
from .providers import Factory, Scoped, Singleton
from .sanic_integration import sanic_container

__all__ = [
    "Container",
    "ScopedContainer",
    "Singleton",
    "Factory",
    "Scoped",
    "inject",
    "sanic_container",
]
