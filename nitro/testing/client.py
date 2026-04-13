"""
Test client helpers: MockRequest, MockResponse, and TestApp.

Provides a lightweight, framework-agnostic way to dispatch Nitro actions in
tests without starting a real web server.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Sequence, Type


# ---------------------------------------------------------------------------
# MockRequest
# ---------------------------------------------------------------------------

class MockRequest:
    """
    A minimal mock request object compatible with Nitro action handlers.

    Handlers receive ``request`` as a positional argument after ``self`` (for
    instance methods) or as the first argument (for standalone handlers).
    Most handlers only need ``request.json``, ``request.form``, ``request.args``,
    and ``request.cookies`` — this class provides all of those.

    Usage::

        req = MockRequest("POST", "/post/Counter:c1.increment",
                          signals={"amount": 5})
    """

    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        signals: Optional[Dict[str, Any]] = None,
        form: Optional[Dict[str, Any]] = None,
        args: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.method = method.upper()
        self.path = path
        self.signals = signals or {}
        self.form = form or {}
        self.args = args or {}
        self.cookies = cookies or {}
        self.headers = headers or {}

        # Common request attribute names used by different frameworks
        self.query_string: Dict[str, Any] = args or {}
        self.query_params: Dict[str, Any] = args or {}
        self.json: Optional[Dict[str, Any]] = signals  # many handlers use request.json

    def get_json(self) -> Optional[Dict[str, Any]]:
        """Flask-style JSON accessor."""
        return self.signals

    def __repr__(self) -> str:
        return f"<MockRequest {self.method} {self.path}>"


# ---------------------------------------------------------------------------
# MockResponse
# ---------------------------------------------------------------------------

class MockResponse:
    """
    Collects response data written by action handlers.

    Handlers can write to ``response.body``, set ``response.status``, or
    update ``response.headers`` and ``response.cookies``.  In test code you
    inspect these after the action runs.

    Usage::

        resp = MockResponse()
        resp.write("Hello!")
        assert resp.body == "Hello!"
    """

    def __init__(self) -> None:
        self.status: int = 200
        self.headers: Dict[str, str] = {}
        self.cookies: Dict[str, str] = {}
        self._parts: List[str] = []

    def write(self, data: Any) -> None:
        """Append data to the response body."""
        self._parts.append(str(data))

    @property
    def body(self) -> str:
        """The full accumulated response body."""
        return "".join(self._parts)

    def set_cookie(self, key: str, value: str, **kwargs: Any) -> None:
        """Record a cookie (ignores options for simplicity)."""
        self.cookies[key] = value

    def set_header(self, key: str, value: str) -> None:
        """Record a response header."""
        self.headers[key] = value

    def __repr__(self) -> str:
        return f"<MockResponse status={self.status} body={self.body[:40]!r}>"


# ---------------------------------------------------------------------------
# TestApp
# ---------------------------------------------------------------------------

class TestApp:
    """
    Sets up an in-memory test environment for a collection of entity classes.

    Replaces the SQLModelRepository singleton with a fresh MemoryRepository
    so tests never touch a real database.

    Usage (async context manager)::

        async with TestApp([MyEntity, OtherEntity]) as app:
            entity = MyEntity(name="test")
            entity.save()
            result = await app.request("POST", "MyEntity:id.do_thing",
                                       signals={"amount": 1})

    Or explicit setup/teardown::

        app = TestApp([MyEntity])
        app.setup()
        try:
            ...
        finally:
            app.teardown()
    """

    # Tell pytest this is not a test suite even though the name starts with "Test"
    __test__ = False

    def __init__(self, entity_classes: Sequence[Type]) -> None:
        self.entity_classes = list(entity_classes)
        self._repo = None
        self._original_repo_class = None

    # ------------------------------------------------------------------
    # Setup / teardown
    # ------------------------------------------------------------------

    def setup(self) -> None:
        """
        Initialize the in-memory test environment.

        - Creates a fresh ``MemoryRepository`` and patches Entity._repository
          substitute so that ``save()``, ``exists()``, ``all()``, etc. all use
          the in-memory store.
        - Registers all given entity classes so action dispatching works.
        """
        from nitro.domain.repository.memory import MemoryRepository

        self._repo = MemoryRepository()
        # Clear any existing data from previous tests
        self._repo._data.clear()
        self._repo._expiry.clear()

        # Patch entity classes to use MemoryRepository
        for cls in self.entity_classes:
            _patch_entity_class(cls, self._repo)

    def teardown(self) -> None:
        """
        Clear all test data and restore original repository references.
        """
        if self._repo is not None:
            self._repo._data.clear()
            self._repo._expiry.clear()

        for cls in self.entity_classes:
            _unpatch_entity_class(cls)

        self._repo = None

    # ------------------------------------------------------------------
    # Request dispatch
    # ------------------------------------------------------------------

    async def request(
        self,
        method: str,
        action_string: str,
        signals: Optional[Dict[str, Any]] = None,
        form: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Dispatch a Nitro action string, returning the handler result.

        Args:
            method:        HTTP method string (ignored for dispatch, kept for
                           parity with real requests).
            action_string: Nitro action string, e.g. ``"Counter:c1.increment"``.
            signals:       Dict of Datastar signal values.
            form:          Form data (also available on the MockRequest).

        Returns:
            Whatever the action handler returns.
        """
        from nitro.adapters.catch_all import dispatch_action

        req = MockRequest(method=method, path=f"/{method.lower()}/{action_string}",
                          signals=signals, form=form)
        return await dispatch_action(action_string, sender="test-client",
                                     signals=signals or {}, request=req)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "TestApp":
        self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.teardown()


# ---------------------------------------------------------------------------
# Internal patching helpers
# ---------------------------------------------------------------------------

# Map entity class → its original repository() classmethod so we can restore
_original_repository_methods: Dict[str, Any] = {}


def _patch_entity_class(cls: Type, repo: Any) -> None:
    """Replace cls.repository() to return *repo*."""
    key = id(cls)
    if key not in _original_repository_methods:
        _original_repository_methods[key] = cls.__dict__.get("repository")

    # Create a classmethod that always returns our test repo
    captured_repo = repo

    @classmethod  # type: ignore[misc]
    def repository(klass):  # noqa: N805
        return captured_repo

    cls.repository = repository  # type: ignore[method-assign]


def _unpatch_entity_class(cls: Type) -> None:
    """Restore cls.repository() to its original implementation."""
    key = id(cls)
    original = _original_repository_methods.pop(key, None)
    if original is not None:
        cls.repository = original  # type: ignore[method-assign]
    elif hasattr(cls, "repository"):
        # Restore the base class method by deleting the override
        try:
            delattr(cls, "repository")
        except AttributeError:
            pass
