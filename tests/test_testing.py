"""
Tests for nitro.testing — the testing utilities module.

Covers:
- EntityFactory: build, create, build_batch, create_batch, field auto-generation
- Assertion helpers: entity, HTML, SSE
- MockRequest / MockResponse
- TestApp setup/teardown cycle and context manager
"""

import pytest
import asyncio
from typing import Optional
from sqlmodel import Field
from nitro.domain.entities.base_entity import Entity
from nitro.domain.repository.memory import MemoryRepository
from nitro.testing import (
    EntityFactory,
    assert_entity_saved,
    assert_entity_deleted,
    assert_entity_equal,
    assert_entity_fields,
    assert_html_contains,
    assert_html_tag,
    assert_sse_event,
    MockRequest,
    MockResponse,
    TestApp,
)


# =============================================================================
# Test entity (used throughout)
# =============================================================================

class SampleEntity(Entity, table=True):
    __tablename__ = "test_sample_entity"
    name: str = ""
    age: int = 0
    active: bool = True


class RequiredFieldEntity(Entity, table=True):
    """Entity where some fields are required (no default)."""
    __tablename__ = "test_required_field_entity"
    title: str
    score: int
    weight: float
    enabled: bool


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clean_memory_repo():
    """Clear memory repository before each test."""
    repo = MemoryRepository()
    repo._data.clear()
    repo._expiry.clear()
    yield
    repo._data.clear()
    repo._expiry.clear()


@pytest.fixture
def factory():
    return EntityFactory(SampleEntity)


@pytest.fixture
def required_factory():
    return EntityFactory(RequiredFieldEntity)


# =============================================================================
# 1. EntityFactory — build / create
# =============================================================================

class TestEntityFactoryBuild:
    """EntityFactory.build() returns unsaved instances."""

    def test_build_returns_instance(self, factory):
        entity = factory.build()
        assert isinstance(entity, SampleEntity)

    def test_build_assigns_unique_ids(self, factory):
        a = factory.build()
        b = factory.build()
        assert a.id != b.id

    def test_build_with_overrides(self, factory):
        entity = factory.build(name="Alice", age=30)
        assert entity.name == "Alice"
        assert entity.age == 30

    def test_build_does_not_save(self, factory):
        entity = factory.build()
        # Not saved — MemoryRepository should not contain it
        repo = MemoryRepository()
        assert repo.find(SampleEntity, entity.id) is None

    def test_build_uses_field_defaults(self, factory):
        """Fields with defaults should use those defaults unless overridden."""
        entity = factory.build()
        # SampleEntity has defaults: name="", age=0, active=True
        # Factory should respect those
        assert isinstance(entity.name, str)
        assert isinstance(entity.age, int)
        assert isinstance(entity.active, bool)

    def test_build_required_fields_auto_generated(self, required_factory):
        """Required fields without defaults should be auto-generated."""
        # Use TestApp so repository is patched to MemoryRepository
        app = TestApp([RequiredFieldEntity])
        app.setup()
        try:
            entity = required_factory.build()
            assert entity.title is not None
            assert isinstance(entity.title, str)
            assert entity.score is not None
            assert isinstance(entity.score, int)
            assert entity.weight is not None
            assert isinstance(entity.weight, float)
            assert isinstance(entity.enabled, bool)
        finally:
            app.teardown()


class TestEntityFactoryCreate:
    """EntityFactory.create() saves the entity."""

    def test_create_returns_instance(self, factory):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entity = factory.create(name="Bob")
            assert isinstance(entity, SampleEntity)
        finally:
            app.teardown()

    def test_create_saves_to_repository(self, factory):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entity = factory.create(name="Bob")
            repo = MemoryRepository()
            saved = repo.find(SampleEntity, entity.id)
            assert saved is not None
        finally:
            app.teardown()

    def test_create_with_overrides(self, factory):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entity = factory.create(name="Charlie", age=25)
            assert entity.name == "Charlie"
            assert entity.age == 25
        finally:
            app.teardown()


class TestEntityFactoryBatch:
    """EntityFactory batch methods."""

    def test_build_batch_returns_correct_count(self, factory):
        entities = factory.build_batch(5)
        assert len(entities) == 5

    def test_build_batch_all_unsaved(self, factory):
        entities = factory.build_batch(3)
        repo = MemoryRepository()
        for e in entities:
            assert repo.find(SampleEntity, e.id) is None

    def test_build_batch_unique_ids(self, factory):
        entities = factory.build_batch(10)
        ids = [e.id for e in entities]
        assert len(ids) == len(set(ids))

    def test_create_batch_saves_all(self, factory):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entities = factory.create_batch(4)
            repo = MemoryRepository()
            for e in entities:
                assert repo.find(SampleEntity, e.id) is not None
        finally:
            app.teardown()

    def test_create_batch_with_overrides(self, factory):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entities = factory.create_batch(3, name="Same", age=10)
            for e in entities:
                assert e.name == "Same"
                assert e.age == 10
        finally:
            app.teardown()


# =============================================================================
# 2. Entity assertions
# =============================================================================

class TestAssertEntitySaved:

    def test_passes_when_saved(self, factory):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entity = factory.create(name="Saved")
            # Should not raise
            assert_entity_saved(entity)
        finally:
            app.teardown()

    def test_fails_when_not_saved(self, factory):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entity = factory.build(name="Unsaved")
            with pytest.raises(AssertionError):
                assert_entity_saved(entity)
        finally:
            app.teardown()


class TestAssertEntityDeleted:

    def test_passes_when_deleted(self, factory):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entity = factory.create(name="ToDelete")
            entity.delete()
            # Should not raise
            assert_entity_deleted(entity)
        finally:
            app.teardown()

    def test_fails_when_still_exists(self, factory):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entity = factory.create(name="Exists")
            with pytest.raises(AssertionError):
                assert_entity_deleted(entity)
        finally:
            app.teardown()


class TestAssertEntityEqual:

    def test_passes_for_identical_entities(self, factory):
        a = factory.build(name="Alice", age=20)
        b = factory.build(name="Alice", age=20)
        assert_entity_equal(a, b, fields=["name", "age"])

    def test_fails_for_different_entities(self, factory):
        a = factory.build(name="Alice")
        b = factory.build(name="Bob")
        with pytest.raises(AssertionError):
            assert_entity_equal(a, b, fields=["name"])

    def test_compares_all_fields_when_none_specified(self, factory):
        a = factory.build(name="Alice", age=20, active=True)
        b = factory.build(name="Alice", age=20, active=True)
        # ids differ so comparison on all fields including id should fail
        with pytest.raises(AssertionError):
            assert_entity_equal(a, b)


class TestAssertEntityFields:

    def test_passes_when_all_match(self, factory):
        entity = factory.build(name="Test", age=42, active=False)
        assert_entity_fields(entity, name="Test", age=42, active=False)

    def test_fails_on_wrong_value(self, factory):
        entity = factory.build(name="Test", age=10)
        with pytest.raises(AssertionError):
            assert_entity_fields(entity, age=99)

    def test_fails_on_missing_attribute(self, factory):
        entity = factory.build()
        with pytest.raises(AssertionError):
            assert_entity_fields(entity, nonexistent_field="value")


# =============================================================================
# 3. HTML assertions
# =============================================================================

class TestAssertHtmlContains:

    def test_passes_when_text_present(self):
        html = "<div>Hello World</div>"
        assert_html_contains(html, "Hello World")

    def test_passes_for_multiple_texts(self):
        html = "<div><p>Foo</p><p>Bar</p></div>"
        assert_html_contains(html, "Foo", "Bar")

    def test_fails_when_text_absent(self):
        html = "<div>Hello</div>"
        with pytest.raises(AssertionError):
            assert_html_contains(html, "World")

    def test_fails_when_any_text_absent(self):
        html = "<div>Hello</div>"
        with pytest.raises(AssertionError):
            assert_html_contains(html, "Hello", "Missing")


class TestAssertHtmlTag:

    def test_passes_for_existing_tag(self):
        html = '<button type="submit">Save</button>'
        assert_html_tag(html, "button")

    def test_passes_with_attribute_check(self):
        html = '<button type="submit">Save</button>'
        assert_html_tag(html, "button", type="submit")

    def test_fails_when_tag_absent(self):
        html = "<div>No buttons here</div>"
        with pytest.raises(AssertionError):
            assert_html_tag(html, "button")

    def test_fails_when_attribute_wrong(self):
        html = '<button type="button">Cancel</button>'
        with pytest.raises(AssertionError):
            assert_html_tag(html, "button", type="submit")

    def test_content_check(self):
        html = '<div id="counter">42</div>'
        assert_html_tag(html, "div", id="counter", _content="42")

    def test_content_check_fails(self):
        html = '<div id="counter">0</div>'
        with pytest.raises(AssertionError):
            assert_html_tag(html, "div", id="counter", _content="99")


# =============================================================================
# 4. SSE assertions
# =============================================================================

class TestAssertSseEvent:

    def test_passes_for_valid_sse_string(self):
        data = "data: hello\n\n"
        assert_sse_event(data)

    def test_passes_for_valid_sse_string_with_event(self):
        data = "event: update\ndata: hello\n\n"
        assert_sse_event(data, event_type="update")

    def test_fails_for_empty_string(self):
        with pytest.raises(AssertionError):
            assert_sse_event("")

    def test_fails_for_invalid_sse_string(self):
        with pytest.raises(AssertionError):
            assert_sse_event("not an sse event at all")

    def test_passes_for_valid_dict(self):
        data = {"type": "patch", "selector": "#content", "elements": "<div/>"}
        assert_sse_event(data)

    def test_passes_for_dict_with_type_check(self):
        data = {"type": "patch", "selector": "#el"}
        assert_sse_event(data, event_type="patch")

    def test_fails_for_dict_wrong_type(self):
        data = {"type": "patch", "selector": "#el"}
        with pytest.raises(AssertionError):
            assert_sse_event(data, event_type="signal")

    def test_fails_for_dict_wrong_selector(self):
        data = {"type": "patch", "selector": "#el"}
        with pytest.raises(AssertionError):
            assert_sse_event(data, selector="#other")

    def test_fails_for_invalid_type(self):
        with pytest.raises(AssertionError):
            assert_sse_event(12345)  # type: ignore


# =============================================================================
# 5. MockRequest / MockResponse
# =============================================================================

class TestMockRequest:

    def test_default_method_is_get(self):
        req = MockRequest()
        assert req.method == "GET"

    def test_method_is_uppercased(self):
        req = MockRequest(method="post")
        assert req.method == "POST"

    def test_path_is_stored(self):
        req = MockRequest(path="/test/path")
        assert req.path == "/test/path"

    def test_signals_accessible(self):
        req = MockRequest(signals={"count": 5})
        assert req.signals["count"] == 5
        assert req.json["count"] == 5  # alias

    def test_form_accessible(self):
        req = MockRequest(form={"email": "test@test.com"})
        assert req.form["email"] == "test@test.com"

    def test_cookies_accessible(self):
        req = MockRequest(cookies={"session": "abc"})
        assert req.cookies["session"] == "abc"

    def test_args_accessible(self):
        req = MockRequest(args={"page": "1"})
        assert req.args["page"] == "1"
        assert req.query_params["page"] == "1"

    def test_get_json_returns_signals(self):
        req = MockRequest(signals={"x": 10})
        assert req.get_json()["x"] == 10

    def test_repr(self):
        req = MockRequest("GET", "/hello")
        assert "GET" in repr(req)
        assert "/hello" in repr(req)


class TestMockResponse:

    def test_initial_status_200(self):
        resp = MockResponse()
        assert resp.status == 200

    def test_write_accumulates_body(self):
        resp = MockResponse()
        resp.write("Hello ")
        resp.write("World")
        assert resp.body == "Hello World"

    def test_set_cookie(self):
        resp = MockResponse()
        resp.set_cookie("session", "tok123")
        assert resp.cookies["session"] == "tok123"

    def test_set_header(self):
        resp = MockResponse()
        resp.set_header("Content-Type", "text/html")
        assert resp.headers["Content-Type"] == "text/html"

    def test_repr(self):
        resp = MockResponse()
        resp.write("test")
        assert "200" in repr(resp)


# =============================================================================
# 6. TestApp setup / teardown
# =============================================================================

class TestTestApp:

    def test_setup_clears_memory_repo(self):
        repo = MemoryRepository()
        # pre-populate
        from sqlmodel import SQLModel
        class _Dummy:
            id = "pre"
        repo._data[("SampleEntity", "pre")] = _Dummy()

        app = TestApp([SampleEntity])
        app.setup()
        assert ("SampleEntity", "pre") not in repo._data
        app.teardown()

    def test_teardown_clears_data(self):
        app = TestApp([SampleEntity])
        app.setup()
        repo = MemoryRepository()
        repo._data[("SampleEntity", "x")] = object()
        app.teardown()
        assert ("SampleEntity", "x") not in repo._data

    def test_entity_save_uses_memory_repo(self):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entity = SampleEntity(name="Patched", age=7)
            entity.save()
            repo = MemoryRepository()
            assert repo.find(SampleEntity, entity.id) is not None
        finally:
            app.teardown()

    def test_entity_exists_uses_memory_repo(self):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entity = SampleEntity(name="E", age=1)
            entity.save()
            assert SampleEntity.exists(entity.id)
        finally:
            app.teardown()

    def test_entity_delete_works(self):
        app = TestApp([SampleEntity])
        app.setup()
        try:
            entity = SampleEntity(name="Del", age=3)
            entity.save()
            assert SampleEntity.exists(entity.id)
            entity.delete()
            assert not SampleEntity.exists(entity.id)
        finally:
            app.teardown()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with TestApp([SampleEntity]) as app:
            assert app._repo is not None
            entity = SampleEntity(name="CM", age=5)
            entity.save()
            repo = MemoryRepository()
            assert repo.find(SampleEntity, entity.id) is not None

    @pytest.mark.asyncio
    async def test_teardown_after_context_manager(self):
        entity_id = None
        async with TestApp([SampleEntity]) as app:
            entity = SampleEntity(name="After", age=2)
            entity.save()
            entity_id = entity.id

        # After context exits, data should be cleared
        repo = MemoryRepository()
        assert repo.find(SampleEntity, entity_id) is None


# =============================================================================
# 7. Integration: Factory + TestApp + assertions together
# =============================================================================

class TestIntegration:

    @pytest.mark.asyncio
    async def test_create_batch_and_verify(self):
        factory = EntityFactory(SampleEntity)
        async with TestApp([SampleEntity]) as app:
            entities = factory.create_batch(5, name="Item", active=True)
            assert len(entities) == 5
            for e in entities:
                assert_entity_saved(e)
                assert_entity_fields(e, name="Item", active=True)

    @pytest.mark.asyncio
    async def test_delete_and_verify(self):
        factory = EntityFactory(SampleEntity)
        async with TestApp([SampleEntity]) as app:
            entity = factory.create(name="ToDelete")
            assert_entity_saved(entity)
            entity.delete()
            assert_entity_deleted(entity)

    def test_html_assertions_standalone(self):
        html = '<div class="card"><h2>Title</h2><p>Content here</p></div>'
        assert_html_contains(html, "Title", "Content here")
        assert_html_tag(html, "div")
        assert_html_tag(html, "h2", _content="Title")

    def test_sse_and_html_combined(self):
        sse = "event: update\ndata: <div id='content'>New content</div>\n\n"
        assert_sse_event(sse, event_type="update")
        html_fragment = "data: <div id='content'>New content</div>"
        assert_html_contains(html_fragment, "New content")
