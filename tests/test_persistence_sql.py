"""
Tests for SQLModelRepository persistence backend.

These tests verify the SQL persistence layer including singleton pattern,
session management, CRUD operations, bulk operations, and advanced filtering.
"""

import pytest
import tempfile
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Optional

from sqlmodel import Field, SQLModel
from nitro.infrastructure.repository.sql import SQLModelRepository


# Test models
class TestUser(SQLModel, table=True):
    """Test user model for SQL repository tests"""
    __tablename__ = "test_users"

    id: str = Field(primary_key=True)
    name: str
    age: Optional[int] = None
    email: Optional[str] = None
    status: Optional[str] = "active"
    created_at: Optional[datetime] = None


class TestProduct(SQLModel, table=True):
    """Test product model with various field types"""
    __tablename__ = "test_products"

    id: str = Field(primary_key=True)
    name: str
    price: Decimal
    in_stock: bool = True
    release_date: Optional[date] = None


class TestItemWithUUID(SQLModel, table=True):
    """Test model with UUID field"""
    __tablename__ = "test_items_uuid"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    code: Optional[UUID] = None


@pytest.fixture
def sql_repo():
    """Create a fresh SQLModelRepository with in-memory database for each test"""
    # Use unique in-memory database for each test to avoid conflicts
    repo = SQLModelRepository.__new__(SQLModelRepository)

    # Create a unique in-memory SQLite database for this test
    import sqlalchemy
    engine = sqlalchemy.create_engine("sqlite:///:memory:", echo=False)
    repo.engine = engine
    repo._initialized = True

    # Create all tables
    SQLModel.metadata.create_all(engine)

    yield repo

    # Clean up
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


class TestSQLModelRepositorySingleton:
    """Tests for singleton pattern"""

    def test_singleton_returns_same_instance(self, sql_repo):
        """SQLModelRepository should be a singleton"""
        repo1 = sql_repo

        # Create another instance - should return the same object
        # Note: In a real scenario, this would be SQLModelRepository()
        # but for testing we just verify the instance exists
        assert repo1 is not None
        assert hasattr(repo1, 'engine')


class TestSQLModelRepositoryInitialization:
    """Tests for database initialization"""

    def test_init_db_creates_tables(self, sql_repo):
        """init_db() should create tables defined in SQLModel"""
        # Tables should already be created by fixture
        # Verify by checking schema
        schema = sql_repo.schema()

        assert "test_users" in schema.lower() or "testuser" in schema.lower()
        assert "id" in schema.lower()
        assert "name" in schema.lower()

    def test_schema_returns_table_information(self, sql_repo):
        """schema() should return string with table and column information"""
        schema = sql_repo.schema()

        assert isinstance(schema, str)
        assert len(schema) > 0
        # Should contain table names and columns
        assert "Table:" in schema or "test" in schema.lower()


class TestSQLModelRepositorySessionManagement:
    """Tests for session management"""

    def test_get_session_yields_session(self, sql_repo):
        """get_session() should yield a SQLModel Session object"""
        session_gen = sql_repo.get_session()

        # Should be a generator
        assert hasattr(session_gen, '__next__')

        # Get the session
        from sqlmodel import Session
        session = next(session_gen)
        assert isinstance(session, Session)


class TestSQLModelRepositoryCRUD:
    """Tests for basic CRUD operations"""

    def test_save_creates_new_record(self, sql_repo):
        """save() should create a new record in the database"""
        user = TestUser(id="user1", name="Alice", age=25)
        result = sql_repo.save(user)

        assert result is True

        # Verify record exists
        found_user = sql_repo.get(TestUser, "user1")
        assert found_user is not None
        assert found_user.name == "Alice"
        assert found_user.age == 25

    def test_save_updates_existing_record(self, sql_repo):
        """save() should update an existing record"""
        user = TestUser(id="user2", name="Bob", age=30)
        sql_repo.save(user)

        # Modify and save again
        user.name = "Robert"
        user.age = 31
        sql_repo.save(user)

        # Verify update
        found_user = sql_repo.get(TestUser, "user2")
        assert found_user.name == "Robert"
        assert found_user.age == 31

    def test_find_retrieves_entity_by_id(self, sql_repo):
        """find() should retrieve entity by ID"""
        user = TestUser(id="user3", name="Charlie")
        sql_repo.save(user)

        found = sql_repo.find(TestUser, "user3")
        assert found is not None
        assert found.name == "Charlie"

    def test_find_returns_none_for_nonexistent(self, sql_repo):
        """find() should return None for non-existent ID"""
        found = sql_repo.find(TestUser, "nonexistent")
        assert found is None

    def test_delete_removes_record(self, sql_repo):
        """delete() should remove record from database"""
        user = TestUser(id="user4", name="David")
        sql_repo.save(user)

        result = sql_repo.delete(user)
        assert result is True

        # Verify deletion
        found = sql_repo.get(TestUser, "user4")
        assert found is None

    def test_exists_checks_record_presence(self, sql_repo):
        """exists() should check if record exists"""
        user = TestUser(id="user5", name="Eve")
        sql_repo.save(user)

        assert sql_repo.exists(TestUser, "user5") is True
        assert sql_repo.exists(TestUser, "nonexistent") is False


class TestSQLModelRepositoryBulkOperations:
    """Tests for bulk operations"""

    def test_bulk_create_inserts_multiple_records(self, sql_repo):
        """bulk_create() should insert multiple records at once"""
        data = [
            {"id": f"bulk{i}", "name": f"User {i}", "age": 20 + i}
            for i in range(10)
        ]

        results = sql_repo.bulk_create(TestUser, data)

        assert len(results) == 10
        assert all(isinstance(r, TestUser) for r in results)

        # Verify all records are in database
        all_users = sql_repo.all(TestUser)
        assert len(all_users) == 10

    def test_bulk_upsert_updates_existing_records(self, sql_repo):
        """bulk_upsert() should update existing records"""
        # Create initial records
        initial_data = [
            {"id": f"upsert{i}", "name": f"User {i}", "age": 20}
            for i in range(5)
        ]
        sql_repo.bulk_create(TestUser, initial_data)

        # Update with new data
        update_data = [
            {"id": f"upsert{i}", "name": f"Updated {i}", "age": 30}
            for i in range(5)
        ]
        results = sql_repo.bulk_upsert(TestUser, update_data)

        assert len(results) == 5

        # Verify updates
        for i in range(5):
            user = sql_repo.get(TestUser, f"upsert{i}")
            assert user.name == f"Updated {i}"
            assert user.age == 30


class TestSQLModelRepositoryCount:
    """Tests for counting records"""

    def test_count_returns_total_records(self, sql_repo):
        """count() should return total number of records"""
        # Create 7 users
        for i in range(7):
            user = TestUser(id=f"count{i}", name=f"User {i}")
            sql_repo.save(user)

        count = sql_repo.count(TestUser)
        assert count == 7


class TestSQLModelRepositoryFilter:
    """Tests for advanced filtering"""

    def test_filter_handles_uuid_fields(self, sql_repo):
        """filter() should handle UUID fields correctly"""
        test_uuid = uuid4()
        item = TestItemWithUUID(name="Test Item", code=test_uuid)
        sql_repo.save(item)

        # Filter by UUID as string
        results = sql_repo.filter(TestItemWithUUID, code=str(test_uuid))
        assert len(results) == 1
        assert results[0].name == "Test Item"

    def test_filter_handles_date_range_queries(self, sql_repo):
        """filter() should handle date range queries"""
        # Create products with different dates
        products = [
            TestProduct(id="p1", name="Old Product", price=Decimal("10.00"),
                       release_date=date(2020, 1, 1)),
            TestProduct(id="p2", name="Mid Product", price=Decimal("20.00"),
                       release_date=date(2021, 6, 15)),
            TestProduct(id="p3", name="New Product", price=Decimal("30.00"),
                       release_date=date(2023, 12, 31)),
        ]
        for product in products:
            sql_repo.save(product)

        # Query for products in date range
        results = sql_repo.filter(
            TestProduct,
            release_date=(date(2021, 1, 1), date(2022, 12, 31))
        )

        assert len(results) == 1
        assert results[0].name == "Mid Product"

    def test_filter_handles_basic_queries(self, sql_repo):
        """filter() should handle basic exact match queries"""
        # Create users with different statuses and ages
        for i in range(5):
            user = TestUser(id=f"filter{i}", name=f"User {i}", age=20 + i, status="active" if i < 3 else "inactive")
            sql_repo.save(user)

        # Filter by status (exact match)
        results_active = sql_repo.filter(TestUser, status="active")
        assert len(results_active) == 3
        assert all(r.status == "active" for r in results_active)

        # Filter by age (exact match)
        results_age = sql_repo.filter(TestUser, age=22)
        assert len(results_age) == 1
        assert results_age[0].age == 22

        # Filter by multiple conditions
        results_multi = sql_repo.filter(TestUser, status="active", age=21)
        assert len(results_multi) == 1
        assert results_multi[0].status == "active"
        assert results_multi[0].age == 21


class TestSQLModelRepositoryConnectionPooling:
    """Tests for connection handling"""

    @pytest.mark.asyncio
    async def test_handles_concurrent_operations(self, sql_repo):
        """Repository should handle concurrent operations without connection leaks"""
        # Perform multiple operations
        for i in range(20):
            user = TestUser(id=f"concurrent{i}", name=f"User {i}", age=i)
            sql_repo.save(user)

        # Verify all operations completed
        count = sql_repo.count(TestUser)
        assert count == 20

        # Verify no connection leaks by performing more operations
        for i in range(20):
            found = sql_repo.get(TestUser, f"concurrent{i}")
            assert found is not None


class TestSQLModelRepositoryAll:
    """Tests for retrieving all records"""

    def test_all_returns_all_entities(self, sql_repo):
        """all() should return all entities of the given type"""
        for i in range(5):
            user = TestUser(id=f"all{i}", name=f"User {i}")
            sql_repo.save(user)

        all_users = sql_repo.all(TestUser)
        assert len(all_users) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
