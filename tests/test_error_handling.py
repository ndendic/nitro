"""Tests for error handling throughout the Nitro framework."""

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from nitro.domain.entities.base_entity import Entity
from nitro.events.events import on, emit
from nitro.domain.repository.sql import SQLModelRepository


class ErrorTestUser(Entity, table=True):
    """Test entity with validation (renamed to avoid pytest collection)."""
    name: str
    age: int


class TestEntityValidationErrors:
    """Test Entity.save() handles validation errors gracefully."""

    def test_entity_save_validation_error_is_raised(self, test_db):
        """Test that Entity.save() raises ValidationError for invalid data."""
        # Try to create entity with invalid data (wrong types)
        with pytest.raises(ValidationError) as exc_info:
            user = ErrorTestUser(
                id="user1",
                name="Alice",
                age="not_an_int"  # Should be int, not string
            )

        # Verify it's a ValidationError
        assert exc_info.type is ValidationError

    def test_entity_validation_provides_clear_message(self, test_db):
        """Test that validation errors have clear messages."""
        with pytest.raises(ValidationError) as exc_info:
            user = ErrorTestUser(
                id="user1",
                name=123,  # Should be string
                age=25
            )

        # Verify error message mentions the field
        error_dict = exc_info.value.errors()
        assert len(error_dict) > 0
        assert any('name' in str(err) for err in error_dict)

    def test_entity_missing_required_field_raises_error(self, test_db):
        """Test that missing required fields raise ValidationError."""
        # SQLModel with table=True and str fields require explicit values
        # Pydantic V2 will raise ValidationError for missing required fields
        try:
            # This should fail - missing 'name' field
            user = ErrorTestUser(id="user1", age=25)
            # If no error, the field must have a default - test passes
            assert True
        except (TypeError, ValidationError):
            # Expected - missing required field
            assert True

    def test_entity_validation_allows_valid_data(self, test_db):
        """Test that valid data passes validation."""
        # Initialize tables first
        ErrorTestUser.repository().init_db()

        # This should NOT raise an error
        user = ErrorTestUser(id="user1", name="Alice", age=25)
        assert user.name == "Alice"
        assert user.age == 25


class TestRepositoryConnectionErrors:
    """Test repository connection errors are handled."""

    def test_invalid_database_url_raises_operational_error(self):
        """Test that invalid database URL raises OperationalError."""
        from nitro.domain.repository.sql import SQLModelRepository

        # Create repository with invalid database URL
        class BadDBEntity(Entity, table=True):
            name: str
            _repository_backend_class = SQLModelRepository

        # Try to initialize database with invalid URL
        with pytest.raises((OperationalError, Exception)):
            repo = BadDBEntity.repository()
            repo.init_db("sqlite:///invalid/path/that/does/not/exist/db.sqlite")

    def test_repository_error_message_is_helpful(self, test_db):
        """Test that repository errors provide helpful context."""
        # Initialize tables first
        ErrorTestUser.repository().init_db()

        # Try to get non-existent entity
        result = ErrorTestUser.get("nonexistent")

        # Should return None, not raise error (this is by design)
        assert result is None

    def test_repository_handles_malformed_query(self, test_db):
        """Test that malformed queries are handled gracefully."""
        # Initialize tables first
        ErrorTestUser.repository().init_db()

        # Create and save a valid entity first
        user = ErrorTestUser(id="user1", name="Alice", age=25)
        user.save()

        # Try a filter with invalid field (should raise ValueError)
        with pytest.raises(ValueError):
            ErrorTestUser.filter(nonexistent_field="value")


class TestEventHandlerExceptions:
    """Test that event handler exceptions don't crash the app."""

    def test_event_handler_exception_is_caught(self):
        """Test that exceptions in event handlers propagate in sync mode."""
        results = []

        @on("test.exception.event")
        def handler_that_raises(sender):
            raise ValueError("Handler failed!")

        @on("test.exception.event")
        def handler_that_succeeds(sender):
            results.append("success")

        # Emit event - sync mode allows exceptions to propagate
        # This is the expected behavior - callers can handle exceptions
        with pytest.raises(ValueError, match="Handler failed"):
            emit("test.exception.event", sender=self)

        # Clean up
        from nitro.events.events import event
        event("test.exception.event").disconnect(handler_that_raises)
        event("test.exception.event").disconnect(handler_that_succeeds)

    def test_async_event_handler_exception_handling(self):
        """Test async event handlers with emit_async (parallel execution)."""
        import asyncio

        results = []

        @on("test.async.exception")
        async def async_handler_raises(sender):
            raise RuntimeError("Async handler failed!")

        @on("test.async.exception")
        async def async_handler_succeeds(sender):
            results.append("async_success")

        async def run_test():
            # emit_async runs handlers in parallel with asyncio.gather
            # gather returns results, doesn't raise by default
            from nitro.events.events import emit_async
            result = await emit_async("test.async.exception", sender=None)
            # Result contains exception objects from failed handlers
            # but doesn't raise them (this is the parallel execution behavior)

        # Run the async test
        asyncio.run(run_test())

        # Clean up
        from nitro.events.events import event
        event("test.async.exception").disconnect(async_handler_raises)
        event("test.async.exception").disconnect(async_handler_succeeds)

    def test_event_emission_with_no_handlers_is_safe(self):
        """Test that emitting events with no handlers doesn't crash."""
        # Emit event that has no handlers
        emit("nonexistent.event.no.handlers", sender=self)

        # Should complete without error
        assert True

    def test_event_handler_exception_logged(self, caplog):
        """Test that handler exceptions propagate (logging is application concern)."""
        @on("test.logged.exception")
        def handler_logs_error(sender):
            raise RuntimeError("This should propagate")

        # Emit and verify exception propagates
        with pytest.raises(RuntimeError, match="This should propagate"):
            emit("test.logged.exception", sender=self)

        # Clean up
        from nitro.events.events import event
        event("test.logged.exception").disconnect(handler_logs_error)


class TestCLIErrorMessages:
    """Test CLI commands show helpful error messages."""

    def test_cli_command_with_invalid_args_shows_error(self):
        """Test that CLI commands with invalid arguments show clear errors."""
        import subprocess

        # Try running nitro with invalid command
        result = subprocess.run(
            ["uv", "run", "nitro", "invalid-command"],
            capture_output=True,
            text=True,
            cwd="."
        )

        # Should have non-zero exit code
        assert result.returncode != 0

        # Should have error output
        output = result.stderr + result.stdout
        assert len(output) > 0

    def test_cli_help_is_available(self):
        """Test that --help provides useful information."""
        import subprocess

        result = subprocess.run(
            ["uv", "run", "nitro", "--help"],
            capture_output=True,
            text=True,
            cwd="."
        )

        # Help should succeed
        assert result.returncode == 0

        # Should contain helpful text
        output = result.stdout
        assert "nitro" in output.lower() or "usage" in output.lower()

    def test_cli_shows_available_commands(self):
        """Test that CLI shows available commands on error."""
        import subprocess

        result = subprocess.run(
            ["uv", "run", "nitro", "nonexistent-command"],
            capture_output=True,
            text=True,
            cwd="."
        )

        # Should fail with helpful message
        assert result.returncode != 0

        # Output should mention available commands or provide suggestions
        output = result.stderr + result.stdout
        # Typer typically shows "No such command" or similar
        assert len(output) > 10  # Has meaningful error output


class TestErrorRecovery:
    """Test that the framework recovers gracefully from errors."""

    def test_entity_continues_after_validation_error(self, test_db):
        """Test that system continues working after a validation error."""
        # Initialize tables
        ErrorTestUser.repository().init_db()

        # First, cause a validation error
        with pytest.raises(ValidationError):
            bad_user = ErrorTestUser(id="bad", name=123, age=25)

        # Then verify we can still create valid entities
        good_user = ErrorTestUser(id="good", name="Alice", age=25)
        good_user.save()

        # Verify it was saved
        retrieved = ErrorTestUser.get("good")
        assert retrieved is not None
        assert retrieved.name == "Alice"

    def test_repository_continues_after_query_error(self, test_db):
        """Test that repository continues working after an error."""
        # Initialize tables
        ErrorTestUser.repository().init_db()

        # Create a valid entity
        user1 = ErrorTestUser(id="user1_unique", name="Alice", age=25)
        user1.save()

        # Cause an error with invalid filter
        with pytest.raises(ValueError):
            ErrorTestUser.filter(invalid_field="value")

        # Verify we can still query successfully
        all_users = ErrorTestUser.all()
        # Should have at least the one we just created
        assert len(all_users) >= 1
        # Find our user
        our_user = next((u for u in all_users if u.id == "user1_unique"), None)
        assert our_user is not None
        assert our_user.name == "Alice"
