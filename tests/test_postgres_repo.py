"""
Tests for nitro.domain.repository.postgres — AsyncPostgresRepository.

Uses aiosqlite as the async backend so tests run without PostgreSQL.
The async SQLAlchemy interface is identical regardless of driver.
"""

import pytest
import pytest_asyncio
from sqlmodel import Field, SQLModel

from nitro.domain.repository.postgres import AsyncPostgresRepository


# ---------------------------------------------------------------------------
# Test entities
# ---------------------------------------------------------------------------


class Item(SQLModel, table=True):
    __tablename__ = "test_pg_items"
    id: str = Field(primary_key=True)
    name: str = ""
    price: float = 0.0
    category: str = "general"
    active: bool = True


class Article(SQLModel, table=True):
    __tablename__ = "test_pg_articles"
    id: str = Field(primary_key=True)
    title: str = ""
    body: str = ""
    author: str = ""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def repo():
    """Provide a fresh AsyncPostgresRepository per test, using aiosqlite."""
    from sqlalchemy.pool import StaticPool

    AsyncPostgresRepository.reset()
    # Bypass the singleton __new__ for SQLite — it needs different pool args
    instance = object.__new__(AsyncPostgresRepository)
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    instance._engine = engine
    instance._session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    instance._url = "sqlite+aiosqlite:///:memory:"
    instance.pool_config = {}

    await instance.init_db()
    yield instance
    await instance.dispose()


# ---------------------------------------------------------------------------
# CRUD basics
# ---------------------------------------------------------------------------


class TestSave:
    @pytest.mark.asyncio
    async def test_save_new(self, repo):
        item = Item(id="i1", name="Widget", price=9.99)
        result = await repo.save(item)
        assert result is True

    @pytest.mark.asyncio
    async def test_save_updates_existing(self, repo):
        item = Item(id="i1", name="Widget", price=9.99)
        await repo.save(item)
        item.price = 19.99
        await repo.save(item)
        found = await repo.get(Item, "i1")
        assert found.price == 19.99

    @pytest.mark.asyncio
    async def test_save_populates_generated_values(self, repo):
        item = Item(id="i1", name="Test")
        await repo.save(item)
        assert item.id == "i1"


class TestGet:
    @pytest.mark.asyncio
    async def test_get_existing(self, repo):
        await repo.save(Item(id="i1", name="Widget"))
        found = await repo.get(Item, "i1")
        assert found is not None
        assert found.name == "Widget"

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self, repo):
        found = await repo.get(Item, "nope")
        assert found is None


class TestFind:
    @pytest.mark.asyncio
    async def test_find_by_id(self, repo):
        await repo.save(Item(id="i1", name="Widget"))
        found = await repo.find(Item, "i1")
        assert found is not None
        assert found.name == "Widget"

    @pytest.mark.asyncio
    async def test_find_missing(self, repo):
        assert await repo.find(Item, "missing") is None


class TestFindBy:
    @pytest.mark.asyncio
    async def test_find_by_field(self, repo):
        await repo.save(Item(id="i1", name="Alpha", category="tools"))
        await repo.save(Item(id="i2", name="Beta", category="food"))
        found = await repo.find_by(Item, category="tools")
        assert found is not None
        assert found.id == "i1"

    @pytest.mark.asyncio
    async def test_find_by_no_match(self, repo):
        await repo.save(Item(id="i1", name="Alpha"))
        assert await repo.find_by(Item, name="Zeta") is None


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_existing(self, repo):
        item = Item(id="i1", name="Widget")
        await repo.save(item)
        result = await repo.delete(item)
        assert result is True
        assert await repo.get(Item, "i1") is None

    @pytest.mark.asyncio
    async def test_delete_missing(self, repo):
        item = Item(id="nope", name="Ghost")
        result = await repo.delete(item)
        assert result is False


class TestExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, repo):
        await repo.save(Item(id="i1", name="Widget"))
        assert await repo.exists(Item, "i1") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, repo):
        assert await repo.exists(Item, "nope") is False


# ---------------------------------------------------------------------------
# Query methods
# ---------------------------------------------------------------------------


class TestAll:
    @pytest.mark.asyncio
    async def test_all_empty(self, repo):
        items = await repo.all(Item)
        assert items == []

    @pytest.mark.asyncio
    async def test_all_returns_list(self, repo):
        await repo.save(Item(id="i1", name="A"))
        await repo.save(Item(id="i2", name="B"))
        items = await repo.all(Item)
        assert len(items) == 2


class TestCount:
    @pytest.mark.asyncio
    async def test_count_zero(self, repo):
        assert await repo.count(Item) == 0

    @pytest.mark.asyncio
    async def test_count_multiple(self, repo):
        await repo.save(Item(id="i1", name="A"))
        await repo.save(Item(id="i2", name="B"))
        await repo.save(Item(id="i3", name="C"))
        assert await repo.count(Item) == 3


class TestWhere:
    @pytest.mark.asyncio
    async def test_where_filters(self, repo):
        await repo.save(Item(id="i1", name="A", category="food"))
        await repo.save(Item(id="i2", name="B", category="tools"))
        await repo.save(Item(id="i3", name="C", category="food"))
        results = await repo.where(Item, Item.category == "food")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_where_with_order_and_limit(self, repo):
        for i in range(5):
            await repo.save(Item(id=f"i{i}", name=f"Item {i}", price=float(i)))
        results = await repo.where(
            Item, Item.price > 1.0, order_by="price", limit=2
        )
        assert len(results) == 2
        assert results[0].price < results[1].price

    @pytest.mark.asyncio
    async def test_where_with_offset(self, repo):
        for i in range(5):
            await repo.save(Item(id=f"i{i}", name=f"Item {i}", price=float(i)))
        results = await repo.where(Item, Item.price >= 0, offset=3)
        assert len(results) == 2


class TestFilter:
    @pytest.mark.asyncio
    async def test_filter_exact(self, repo):
        await repo.save(Item(id="i1", name="Alpha", category="tools"))
        await repo.save(Item(id="i2", name="Beta", category="food"))
        results = await repo.filter(Item, category="tools")
        assert len(results) == 1
        assert results[0].name == "Alpha"

    @pytest.mark.asyncio
    async def test_filter_invalid_field_raises(self, repo):
        with pytest.raises(ValueError, match="Invalid fields"):
            await repo.filter(Item, nonexistent="x")

    @pytest.mark.asyncio
    async def test_filter_sorting(self, repo):
        await repo.save(Item(id="i1", name="B", price=20.0))
        await repo.save(Item(id="i2", name="A", price=10.0))
        results = await repo.filter(
            Item, sorting_field="price", sort_direction="desc"
        )
        assert results[0].price == 20.0

    @pytest.mark.asyncio
    async def test_filter_pagination(self, repo):
        for i in range(10):
            await repo.save(Item(id=f"i{i:02}", name=f"Item {i}"))
        results = await repo.filter(Item, limit=3, offset=2)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_filter_as_dict(self, repo):
        await repo.save(Item(id="i1", name="Widget"))
        results = await repo.filter(Item, as_dict=True)
        assert isinstance(results[0], dict)
        assert results[0]["name"] == "Widget"

    @pytest.mark.asyncio
    async def test_filter_fuzzy(self, repo):
        await repo.save(Item(id="i1", name="Foobar"))
        await repo.save(Item(id="i2", name="Baz"))
        results = await repo.filter(Item, exact_match=False, name="oob")
        assert len(results) == 1
        assert results[0].id == "i1"

    @pytest.mark.asyncio
    async def test_filter_invalid_sort_field(self, repo):
        with pytest.raises(ValueError, match="does not exist"):
            await repo.filter(Item, sorting_field="fake")


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_across_string_fields(self, repo):
        await repo.save(Article(id="a1", title="Python Guide", body="Learn Python", author="Alice"))
        await repo.save(Article(id="a2", title="Rust Manual", body="Learn Rust", author="Bob"))
        results = await repo.search(Article, search_value="Python")
        assert len(results) == 1
        assert results[0].id == "a1"

    @pytest.mark.asyncio
    async def test_search_no_value_returns_all(self, repo):
        await repo.save(Article(id="a1", title="A", body="", author=""))
        await repo.save(Article(id="a2", title="B", body="", author=""))
        results = await repo.search(Article)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_with_sorting(self, repo):
        await repo.save(Article(id="a1", title="Zebra", body="", author=""))
        await repo.save(Article(id="a2", title="Alpha", body="", author=""))
        results = await repo.search(Article, sorting_field="title")
        assert results[0].title == "Alpha"

    @pytest.mark.asyncio
    async def test_search_as_dict(self, repo):
        await repo.save(Article(id="a1", title="Test", body="x", author="y"))
        results = await repo.search(Article, as_dict=True)
        assert isinstance(results[0], dict)


# ---------------------------------------------------------------------------
# Bulk operations
# ---------------------------------------------------------------------------


class TestBulkCreate:
    @pytest.mark.asyncio
    async def test_bulk_create(self, repo):
        data = [
            {"id": f"i{i}", "name": f"Item {i}", "price": float(i)}
            for i in range(5)
        ]
        records = await repo.bulk_create(Item, data)
        assert len(records) == 5
        assert await repo.count(Item) == 5


class TestBulkUpsert:
    @pytest.mark.asyncio
    async def test_bulk_upsert_updates_existing(self, repo):
        await repo.save(Item(id="i1", name="Old", price=1.0))
        records = await repo.bulk_upsert(
            Item, [{"id": "i1", "name": "New", "price": 99.0}]
        )
        assert len(records) == 1
        found = await repo.get(Item, "i1")
        assert found.name == "New"
        assert found.price == 99.0


class TestDeleteWhere:
    @pytest.mark.asyncio
    async def test_delete_where(self, repo):
        await repo.save(Item(id="i1", name="A", category="food"))
        await repo.save(Item(id="i2", name="B", category="tools"))
        await repo.save(Item(id="i3", name="C", category="food"))
        deleted = await repo.delete_where(Item, Item.category == "food")
        assert deleted == 2
        assert await repo.count(Item) == 1


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdate:
    @pytest.mark.asyncio
    async def test_update_by_id(self, repo):
        await repo.save(Item(id="i1", name="Old", price=5.0))
        result = await repo.update(Item, "i1", {"name": "New", "price": 50.0})
        assert result["name"] == "New"
        assert result["price"] == 50.0

    @pytest.mark.asyncio
    async def test_update_missing_raises(self, repo):
        with pytest.raises(Exception, match="not found"):
            await repo.update(Item, "nope", {"name": "X"})


# ---------------------------------------------------------------------------
# Schema & flush
# ---------------------------------------------------------------------------


class TestSchema:
    @pytest.mark.asyncio
    async def test_schema_returns_string(self, repo):
        text = await repo.schema()
        assert "test_pg_items" in text
        assert "id" in text


class TestFlush:
    @pytest.mark.asyncio
    async def test_flush_model(self, repo):
        await repo.save(Item(id="i1", name="A"))
        await repo.save(Item(id="i2", name="B"))
        await repo.flush(Item)
        assert await repo.count(Item) == 0

    @pytest.mark.asyncio
    async def test_flush_all(self, repo):
        await repo.save(Item(id="i1", name="A"))
        await repo.save(Article(id="a1", title="T", body="B", author="X"))
        await repo.flush()
        assert await repo.count(Item) == 0
        assert await repo.count(Article) == 0


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_drop_and_recreate(self, repo):
        await repo.save(Item(id="i1", name="A"))
        await repo.drop_db()
        await repo.init_db()
        assert await repo.count(Item) == 0

    @pytest.mark.asyncio
    async def test_reset_singleton(self, repo):
        AsyncPostgresRepository.reset()
        assert AsyncPostgresRepository._instance is None
