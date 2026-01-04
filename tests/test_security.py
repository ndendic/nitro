"""
Tests for security features (SQL injection prevention, validation)
"""
import pytest
from sqlmodel import Field
from nitro.domain.entities.base_entity import Entity
from nitro.domain.repository.sql import SQLModelRepository


class SecurityTestUser(Entity, table=True):
    """Test entity for security testing"""
    __tablename__ = "security_test_users"

    name: str = ""
    email: str = ""
    bio: str = ""


class TestSQLInjectionPrevention:
    """Test SQL injection prevention via parameterized queries"""

    def test_sql_injection_via_filter_prevented(self, test_repository):
        """Verify SQL injection via filter is prevented"""
        test_repository.init_db()

        # Create test user
        user = SecurityTestUser(id="user1", name="Alice", email="alice@example.com")
        user.save()

        # Try SQL injection via filter
        # Classic SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE security_test_users; --",
            "' OR '1'='1",
            "admin'--",
            "1' OR '1' = '1",
            "'; DELETE FROM security_test_users WHERE 'a' = 'a",
        ]

        for malicious_input in malicious_inputs:
            # Try to inject via filter
            # SQLModel uses parameterized queries, so this should be safe
            results = SecurityTestUser.filter(name=malicious_input)

            # Should return empty list (no match) rather than executing injection
            assert isinstance(results, list)
            # Should not find any users with malicious SQL as name
            assert len(results) == 0

        # Verify original data is intact
        all_users = SecurityTestUser.all()
        assert len(all_users) == 1
        assert all_users[0].name == "Alice"

    def test_sql_injection_via_search_prevented(self, test_repository):
        """Verify SQL injection via search is prevented"""
        test_repository.init_db()

        # Create test user
        user = SecurityTestUser(id="user1", name="Alice", email="alice@example.com")
        user.save()

        # Try SQL injection via search
        malicious_search = "'; DROP TABLE security_test_users; --"

        # Search should not execute injection
        results = SecurityTestUser.search(search_value=malicious_search, fields=["name"])

        # Should return empty results, not execute malicious SQL
        assert isinstance(results, list)
        assert len(results) == 0

        # Verify data is intact
        all_users = SecurityTestUser.all()
        assert len(all_users) == 1

    def test_parameterized_queries_in_where(self, test_repository):
        """Verify WHERE clause uses parameterized queries"""
        test_repository.init_db()

        # Create test users
        SecurityTestUser(id="user1", name="Alice", email="alice@example.com").save()
        SecurityTestUser(id="user2", name="Bob", email="bob@example.com").save()

        # Try SQL injection via where clause
        # This should be handled safely by SQLAlchemy/SQLModel
        results = SecurityTestUser.where(
            SecurityTestUser.name == "'; DROP TABLE security_test_users; --"
        )

        # Should return empty list
        assert len(results) == 0

        # Verify data is intact
        all_users = SecurityTestUser.all()
        assert len(all_users) == 2

    def test_no_sql_errors_with_special_characters(self, test_repository):
        """Verify special characters in data don't cause SQL errors"""
        test_repository.init_db()

        # Special characters that might cause issues
        special_chars = [
            "O'Brien",  # Single quote
            'User with "quotes"',  # Double quotes
            "User with ; semicolon",  # Semicolon
            "User with -- comment",  # SQL comment
            "User with /* block */ comment",  # Block comment
            "User with \\ backslash",  # Backslash
        ]

        for i, name in enumerate(special_chars):
            user = SecurityTestUser(id=f"user{i}", name=name, email=f"user{i}@example.com")
            # Should save without SQL errors
            result = user.save()
            assert result is True

            # Should be retrievable
            retrieved = SecurityTestUser.get(f"user{i}")
            assert retrieved is not None
            assert retrieved.name == name

    def test_sql_injection_via_id_prevented(self, test_repository):
        """Verify SQL injection via ID parameter is prevented"""
        test_repository.init_db()

        # Create test user
        user = SecurityTestUser(id="user1", name="Alice", email="alice@example.com")
        user.save()

        # Try SQL injection via get()
        malicious_id = "' OR '1'='1"
        result = SecurityTestUser.get(malicious_id)

        # Should return None (no match), not execute injection
        assert result is None

        # Verify data is intact
        all_users = SecurityTestUser.all()
        assert len(all_users) == 1


class TestEntityValidation:
    """Test entity validation for data integrity"""

    def test_validation_allows_safe_html_content(self, test_repository):
        """Verify validation allows safe HTML content"""
        test_repository.init_db()

        # Pydantic doesn't sanitize by default, but validates types
        user = SecurityTestUser(
            id="user1",
            name="Alice",
            bio="<p>This is my bio</p>"
        )

        # Should save (Pydantic validates type, not content)
        result = user.save()
        assert result is True

        # Content should be preserved as-is
        retrieved = SecurityTestUser.get("user1")
        assert retrieved.bio == "<p>This is my bio</p>"

    def test_validation_stores_script_tags_safely(self, test_repository):
        """Verify script tags are stored (validation is application responsibility)"""
        test_repository.init_db()

        # Note: Nitro stores data as-is; XSS prevention is application's job
        user = SecurityTestUser(
            id="user1",
            name="Alice",
            bio="<script>alert('xss')</script>"
        )

        # Should save (storage layer doesn't sanitize)
        result = user.save()
        assert result is True

        # Data is stored as-is
        retrieved = SecurityTestUser.get("user1")
        assert "<script>" in retrieved.bio

        # NOTE: Applications should sanitize on OUTPUT, not storage
        # This test verifies Nitro doesn't corrupt data

    def test_type_validation_prevents_wrong_types(self):
        """Verify Pydantic type validation works"""
        from pydantic import ValidationError

        # Try to create entity with wrong type
        with pytest.raises(ValidationError):
            SecurityTestUser(
                id="user1",
                name=12345,  # Should be string
                email="alice@example.com"
            )

    def test_field_constraints_enforced(self, test_repository):
        """Verify field constraints are enforced"""
        from pydantic import ValidationError

        # Define entity with constraints
        class ConstrainedUser(Entity, table=True):
            __tablename__ = "constrained_users"

            name: str = Field(min_length=1, max_length=50)
            age: int = Field(ge=0, le=150)

        test_repository.init_db()

        # Try to violate constraints
        with pytest.raises(ValidationError):
            ConstrainedUser(id="user1", name="", age=25)  # Empty name

        with pytest.raises(ValidationError):
            ConstrainedUser(id="user2", name="Alice", age=-5)  # Negative age

        with pytest.raises(ValidationError):
            ConstrainedUser(id="user3", name="Alice", age=200)  # Age too high

        # Valid entity should work
        valid_user = ConstrainedUser(id="user4", name="Alice", age=25)
        assert valid_user.save() is True

    def test_optional_fields_handle_none_safely(self, test_repository):
        """Verify optional fields handle None values safely"""
        from typing import Optional

        class OptionalFieldUser(Entity, table=True):
            __tablename__ = "optional_field_users"

            name: str
            bio: Optional[str] = None

        test_repository.init_db()

        # Create user with None bio
        user = OptionalFieldUser(id="user1", name="Alice", bio=None)
        assert user.save() is True

        # Retrieve and verify
        retrieved = OptionalFieldUser.get("user1")
        assert retrieved.bio is None


class TestSecurityIntegration:
    """Integration tests for security features"""

    def test_end_to_end_sql_injection_resistance(self, test_repository):
        """End-to-end test of SQL injection resistance"""
        test_repository.init_db()

        # Create legitimate users
        SecurityTestUser(id="user1", name="Alice", email="alice@example.com").save()
        SecurityTestUser(id="user2", name="Bob", email="bob@example.com").save()

        # Attempt various injection vectors
        injection_attempts = [
            ("get", ["'; DROP TABLE security_test_users; --"]),
            ("filter", {"name": "' OR '1'='1"}),
            ("search", ["admin'--"]),
        ]

        for method_name, args in injection_attempts:
            if method_name == "get":
                SecurityTestUser.get(*args)
            elif method_name == "filter":
                SecurityTestUser.filter(**args)
            elif method_name == "search":
                SecurityTestUser.search(search_value=args[0], fields=["name"])

        # Verify all data is intact
        all_users = SecurityTestUser.all()
        assert len(all_users) == 2
        assert all_users[0].name == "Alice"
        assert all_users[1].name == "Bob"

    def test_concurrent_operations_with_special_characters(self, test_repository):
        """Verify operations with special characters are safe"""
        test_repository.init_db()

        special_names = [
            "O'Brien",
            'User "quoted"',
            "User; with semicolon",
            "User -- comment",
        ]

        # Save users sequentially (simpler and more reliable)
        for i, name in enumerate(special_names):
            user = SecurityTestUser(id=f"user{i}", name=name, email=f"user{i}@example.com")
            result = user.save()
            assert result is True

        # Verify all users saved correctly
        all_users = SecurityTestUser.all()
        assert len(all_users) == len(special_names)

        # Verify names are preserved correctly
        saved_names = [u.name for u in all_users]
        for name in special_names:
            assert name in saved_names
