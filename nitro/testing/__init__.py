"""
nitro.testing — Testing utilities for Nitro applications.

Provides:
- EntityFactory     : Generic factory for building test entity instances
                      with auto-generated random field data
- assert_entity_saved   : Assert an entity exists in its repository
- assert_entity_deleted : Assert an entity no longer exists in its repository
- assert_entity_equal   : Compare two entities field-by-field
- assert_entity_fields  : Assert specific field values on an entity
- assert_html_contains  : Assert an HTML string contains expected text(s)
- assert_html_tag       : Assert a specific HTML tag/attribute combination exists
- assert_sse_event      : Assert an SSE payload has the expected structure
- MockRequest       : Minimal mock request object for action handler tests
- MockResponse      : Collects response data for inspection in tests
- TestApp           : Async context manager — in-memory test environment
                      (patches entity repos, no real database needed)

Quick start::

    import pytest
    from sqlmodel import Field
    from nitro.domain.entities.base_entity import Entity
    from nitro.testing import EntityFactory, assert_entity_saved, TestApp

    class Product(Entity, table=True):
        __tablename__ = "test_product"
        name: str = ""
        price: float = 0.0

    factory = EntityFactory(Product)

    @pytest.mark.asyncio
    async def test_product_created():
        async with TestApp([Product]) as app:
            product = factory.create(name="Widget", price=9.99)
            assert_entity_saved(product)

    def test_entity_fields():
        product = factory.build(name="Widget", price=9.99)
        from nitro.testing import assert_entity_fields
        assert_entity_fields(product, name="Widget", price=9.99)

    def test_html():
        from nitro.testing import assert_html_contains, assert_html_tag
        html = '<button type="submit">Save</button>'
        assert_html_contains(html, "Save")
        assert_html_tag(html, "button", type="submit")
"""

from .factories import EntityFactory
from .assertions import (
    assert_entity_saved,
    assert_entity_deleted,
    assert_entity_equal,
    assert_entity_fields,
    assert_html_contains,
    assert_html_tag,
    assert_sse_event,
)
from .client import MockRequest, MockResponse, TestApp

__all__ = [
    # Factory
    "EntityFactory",
    # Entity assertions
    "assert_entity_saved",
    "assert_entity_deleted",
    "assert_entity_equal",
    "assert_entity_fields",
    # HTML assertions
    "assert_html_contains",
    "assert_html_tag",
    # SSE assertions
    "assert_sse_event",
    # Test client
    "MockRequest",
    "MockResponse",
    "TestApp",
]
