"""
Tests for testing-related features of Nitro Framework.

This module verifies that Nitro provides excellent testing support including:
- Pytest fixtures for database isolation
- MemoryRepository for fast unit tests
- Entity models work with factory pattern
"""
import pytest
from typing import Optional
from sqlmodel import SQLModel, Field
from nitro.domain.entities.base_entity import Entity
from nitro.domain.repository.memory import MemoryRepository
from nitro.domain.repository.sql import SQLModelRepository


# =============================================================================
# Test Entities
# =============================================================================

class FactoryTestUser(Entity, table=True):
    """User entity for testing."""
    __tablename__ = "factory_test_users"

    id: str = Field(primary_key=True)
    name: str
    email: str
    age: Optional[int] = None


class MemoryTestProduct(SQLModel, table=False):
    """Product entity using MemoryRepository."""
    id: str = Field(primary_key=True)
    name: str
    price: float


# =============================================================================
# Test 1: pytest fixtures available for Nitro entities
# =============================================================================

class TestPytestFixtures:
    """Verify pytest fixtures work correctly with Nitro entities."""

    def test_test_db_fixture_provides_clean_database(self, test_db):
        """test_db fixture should provide a clean in-memory database."""
        # Verify we have an engine
        assert test_db is not None
        assert str(test_db.url) == "sqlite:///:memory:"

    def test_test_repository_fixture_provides_isolated_repo(self, test_repository):
        """test_repository fixture should provide an isolated repository."""
        # Verify we have a repository
        assert test_repository is not None
        assert isinstance(test_repository, SQLModelRepository)

        # Verify it's initialized
        assert test_repository._initialized is True

    def test_test_session_fixture_provides_session(self, test_session):
        """test_session fixture should provide a database session."""
        # Verify we have a session
        assert test_session is not None

        # Verify we can execute a query
        from sqlmodel import select
        result = test_session.exec(select(FactoryTestUser)).all()
        assert isinstance(result, list)

    def test_fixtures_provide_isolation_between_tests_1(self, test_repository):
        """First test: Create a user and verify isolation."""
        # Create and save a user
        user = FactoryTestUser(id="user1", name="Alice", email="alice@example.com")
        user.save()

        # Verify user exists
        assert FactoryTestUser.get("user1") is not None
        assert FactoryTestUser.get("user1").name == "Alice"

    def test_fixtures_provide_isolation_between_tests_2(self, test_repository):
        """Second test: Verify previous test's data doesn't leak."""
        # This should be a clean database - no user from previous test
        user = FactoryTestUser.get("user1")
        assert user is None

        # Verify empty database
        all_users = FactoryTestUser.all()
        assert len(all_users) == 0

    def test_fixture_cleanup_between_tests_1(self, test_repository):
        """Create multiple entities."""
        for i in range(5):
            user = FactoryTestUser(
                id=f"user{i}",
                name=f"User {i}",
                email=f"user{i}@example.com",
                age=20 + i
            )
            user.save()

        assert len(FactoryTestUser.all()) == 5

    def test_fixture_cleanup_between_tests_2(self, test_repository):
        """Verify previous test's entities don't persist."""
        # Database should be clean
        assert len(FactoryTestUser.all()) == 0

    def test_concurrent_test_execution_isolation(self, test_repository):
        """Verify each test gets its own isolated environment."""
        # This test should not see any data from other tests
        users = FactoryTestUser.all()
        assert len(users) == 0

        # Create a user in this test
        user = FactoryTestUser(id="isolated", name="Isolated", email="isolated@test.com")
        user.save()

        # Should only see the user created in this test
        assert len(FactoryTestUser.all()) == 1


# =============================================================================
# Test 2: MemoryRepository perfect for unit tests
# =============================================================================

@pytest.fixture
def memory_repo():
    """Get fresh MemoryRepository instance and clear data."""
    repo = MemoryRepository()
    # Clear all data between tests
    repo._data.clear()
    repo._expiry.clear()
    return repo


class TestMemoryRepositoryForUnitTests:
    """Verify MemoryRepository is fast and perfect for unit testing."""

    def test_memory_repository_no_database_required(self, memory_repo):
        """MemoryRepository should work without any database setup."""
        # No database needed - MemoryRepository works immediately
        product = MemoryTestProduct(id="p1", name="Widget", price=9.99)
        memory_repo.save(product)

        # Retrieve and verify
        retrieved = memory_repo.find("p1")
        assert retrieved is not None
        assert retrieved.name == "Widget"
        assert retrieved.price == 9.99

    def test_memory_repository_fast_operation(self, memory_repo):
        """MemoryRepository operations should be very fast."""
        import time

        # Create many entities
        start = time.time()
        for i in range(100):
            product = MemoryTestProduct(
                id=f"p{i}",
                name=f"Product {i}",
                price=float(i)
            )
            memory_repo.save(product)
        duration = time.time() - start

        # Should be very fast (< 100ms for 100 entities)
        assert duration < 0.1

        # Verify all saved by checking specific ones
        assert memory_repo.find("p0") is not None
        assert memory_repo.find("p99") is not None

    def test_memory_repository_automatic_cleanup(self, memory_repo):
        """MemoryRepository can be easily cleared between tests."""
        # Create some products
        for i in range(5):
            product = MemoryTestProduct(id=f"prod{i}", name=f"P{i}", price=1.0)
            memory_repo.save(product)

        # Verify saved
        assert len(memory_repo._data) == 5

        # Clear the repository
        memory_repo._data.clear()

        # Verify empty
        assert len(memory_repo._data) == 0

    def test_memory_repository_supports_all_operations(self, memory_repo):
        """MemoryRepository should support all CRUD operations."""
        # Create
        p1 = MemoryTestProduct(id="p1", name="Test", price=5.0)
        result = memory_repo.save(p1)
        assert result is True

        # Read
        assert memory_repo.find("p1") is not None
        assert memory_repo.exists("p1") is True

        # Update
        p1.price = 10.0
        memory_repo.save(p1)
        retrieved = memory_repo.find("p1")
        assert retrieved.price == 10.0

        # Delete
        result = memory_repo.delete("p1")
        assert result is True
        assert memory_repo.find("p1") is None

    def test_memory_repository_isolation_with_fixtures(self, memory_repo):
        """Fixtures provide clean MemoryRepository between tests."""
        # This should be empty at test start
        assert len(memory_repo._data) == 0

        # Add data
        memory_repo.save(MemoryTestProduct(id="p1", name="Product", price=1.0))
        assert len(memory_repo._data) == 1


# =============================================================================
# Test 3: Entity models work with factory pattern
# =============================================================================

class UserFactory:
    """Factory for creating test User entities."""

    _counter = 0

    @classmethod
    def create(cls, **overrides):
        """Create a User with default values, optionally overridden."""
        cls._counter += 1
        defaults = {
            "id": f"user{cls._counter}",
            "name": f"User {cls._counter}",
            "email": f"user{cls._counter}@example.com",
            "age": 25
        }
        defaults.update(overrides)
        return FactoryTestUser(**defaults)

    @classmethod
    def create_batch(cls, count, **overrides):
        """Create multiple users."""
        return [cls.create(**overrides) for _ in range(count)]

    @classmethod
    def reset(cls):
        """Reset counter for test isolation."""
        cls._counter = 0


class TestEntityFactoryPattern:
    """Verify Entity models work well with factory pattern."""

    def setup_method(self):
        """Reset factory counter before each test."""
        UserFactory.reset()

    def test_factory_creates_valid_entities(self, test_repository):
        """Factory should create valid entities with defaults."""
        user = UserFactory.create()

        assert user.id == "user1"
        assert user.name == "User 1"
        assert user.email == "user1@example.com"
        assert user.age == 25

    def test_factory_supports_overrides(self, test_repository):
        """Factory should allow overriding default values."""
        user = UserFactory.create(
            name="Custom Name",
            email="custom@example.com",
            age=30
        )

        assert user.name == "Custom Name"
        assert user.email == "custom@example.com"
        assert user.age == 30
        assert user.id == "user1"  # ID still auto-generated

    def test_factory_creates_unique_entities(self, test_repository):
        """Factory should create unique entities with each call."""
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        user3 = UserFactory.create()

        assert user1.id != user2.id != user3.id
        assert user1.email != user2.email != user3.email

    def test_factory_batch_creation(self, test_repository):
        """Factory should support batch creation."""
        users = UserFactory.create_batch(10)

        assert len(users) == 10
        assert all(isinstance(u, FactoryTestUser) for u in users)

        # All should have unique IDs
        ids = [u.id for u in users]
        assert len(ids) == len(set(ids))

    def test_factory_works_with_save(self, test_repository):
        """Factory-created entities should save normally."""
        user = UserFactory.create()
        assert user.save() is True

        # Verify retrieval
        retrieved = FactoryTestUser.get(user.id)
        assert retrieved is not None
        assert retrieved.name == user.name

    def test_factory_batch_with_save(self, test_repository):
        """Factory batch creation should work with save."""
        users = UserFactory.create_batch(5)

        # Save all
        for user in users:
            user.save()

        # Verify all saved
        assert len(FactoryTestUser.all()) == 5

    def test_factory_reset_between_tests_1(self, test_repository):
        """First test: Create users."""
        user1 = UserFactory.create()
        assert user1.id == "user1"

    def test_factory_reset_between_tests_2(self, test_repository):
        """Second test: Counter should reset due to setup_method."""
        user1 = UserFactory.create()
        assert user1.id == "user1"  # Counter reset

    def test_factory_with_custom_logic(self, test_repository):
        """Factory can include custom test data logic."""
        # Create admin user
        admin = UserFactory.create(
            name="Admin",
            email="admin@example.com",
            age=None  # No age for admin
        )

        # Create regular users
        users = UserFactory.create_batch(3, age=20)

        admin.save()
        for user in users:
            user.save()

        # Verify mixed data
        all_users = FactoryTestUser.all()
        assert len(all_users) == 4

        admin_retrieved = FactoryTestUser.find_by(name="Admin")
        assert admin_retrieved.age is None


# =============================================================================
# Integration Test: All testing features together
# =============================================================================

class TestTestingFeaturesIntegration:
    """Integration test combining all testing features."""

    def setup_method(self):
        """Setup for each test."""
        UserFactory.reset()

    def test_complete_testing_workflow(self, test_repository, memory_repo):
        """Demonstrate complete testing workflow with all features."""
        # 1. Use factory to create test data
        users = UserFactory.create_batch(3)

        # 2. Use MemoryRepository for fast auxiliary data
        product = MemoryTestProduct(id="p1", name="Test Product", price=99.99)
        memory_repo.save(product)

        # 3. Save users to test database (via fixture)
        for user in users:
            user.save()

        # 4. Verify everything works together
        assert len(FactoryTestUser.all()) == 3
        assert memory_repo.find("p1") is not None

        # 5. Test operations
        user = users[0]
        user.age = 30
        user.save()

        updated = FactoryTestUser.get(user.id)
        assert updated.age == 30

        # 6. Cleanup (automatic via fixtures)
        # Next test will have clean state
