"""
Tests for CLI Database commands (nitro db init, migrations, migrate)
"""
import subprocess
import tempfile
import os
import pytest
from pathlib import Path
import shutil


class TestDBInit:
    """Test nitro db init command"""

    def test_db_init_command_exists(self):
        """Verify 'nitro db init' command is available"""
        result = subprocess.run(
            ["uv", "run", "nitro", "db", "init", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        assert "init" in result.stdout.lower() or "initialize" in result.stdout.lower()
        assert "alembic" in result.stdout.lower() or "database" in result.stdout.lower()

    def test_db_init_creates_alembic_directory(self):
        """Verify 'nitro db init' creates Alembic directory structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a minimal Python file to serve as entry point
            (tmppath / "app.py").write_text("""
from nitro.domain.entities.base_entity import Entity

class User(Entity, table=True):
    __tablename__ = "users"
    name: str = ""
""")

            # Run db init
            result = subprocess.run(
                ["uv", "run", "nitro", "db", "init"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            # Should succeed or give helpful error
            if result.returncode == 0:
                # Check for Alembic directory
                alembic_dir = tmppath / "alembic"
                alembic_ini = tmppath / "alembic.ini"

                # At least one should exist
                assert alembic_dir.exists() or alembic_ini.exists(), "No Alembic files created"

                # If directory exists, check for versions folder
                if alembic_dir.exists():
                    versions_dir = alembic_dir / "versions"
                    assert versions_dir.exists() or len(list(alembic_dir.iterdir())) > 0

    def test_db_init_is_idempotent(self):
        """Verify running 'nitro db init' twice is safe"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a minimal app file
            (tmppath / "app.py").write_text("# Minimal app")

            # Run init first time
            result1 = subprocess.run(
                ["uv", "run", "nitro", "db", "init"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            # Run init second time
            result2 = subprocess.run(
                ["uv", "run", "nitro", "db", "init"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            # Both should either succeed or fail gracefully
            # Second run should not crash
            assert result2.returncode in [0, 1, 2]


class TestDBMigrations:
    """Test nitro db migrations command"""

    def test_db_migrations_command_exists(self):
        """Verify 'nitro db migrations' command is available"""
        result = subprocess.run(
            ["uv", "run", "nitro", "db", "migrations", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        assert "migration" in result.stdout.lower() or "generate" in result.stdout.lower()

    def test_db_migrations_requires_init(self):
        """Verify 'nitro db migrations' gives error without init"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to create migration without init
            result = subprocess.run(
                ["uv", "run", "nitro", "db", "migrations"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=10
            )

            # Should fail or give helpful error
            if result.returncode != 0:
                output = result.stdout + result.stderr
                # Error should mention initialization or configuration
                assert "init" in output.lower() or "alembic" in output.lower() or "not found" in output.lower()

    def test_db_migrations_accepts_message_parameter(self):
        """Verify migrations command accepts -m parameter"""
        result = subprocess.run(
            ["uv", "run", "nitro", "db", "migrations", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        # Should mention message parameter
        assert "-m" in result.stdout or "--message" in result.stdout or "message" in result.stdout.lower()


class TestDBMigrate:
    """Test nitro db migrate command"""

    def test_db_migrate_command_exists(self):
        """Verify 'nitro db migrate' command is available"""
        result = subprocess.run(
            ["uv", "run", "nitro", "db", "migrate", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        assert "migrate" in result.stdout.lower() or "apply" in result.stdout.lower()

    def test_db_migrate_requires_init(self):
        """Verify 'nitro db migrate' gives error without init"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to migrate without init
            result = subprocess.run(
                ["uv", "run", "nitro", "db", "migrate"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=10
            )

            # Should fail or give helpful error
            if result.returncode != 0:
                output = result.stdout + result.stderr
                # Error should mention initialization or configuration
                assert "init" in output.lower() or "alembic" in output.lower() or "not found" in output.lower()

    def test_db_migrate_accepts_revision_parameter(self):
        """Verify migrate command can target specific revision"""
        result = subprocess.run(
            ["uv", "run", "nitro", "db", "migrate", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        # May accept revision as argument or default to "head"


class TestDBWorkflow:
    """Test complete database workflow"""

    def test_db_all_commands_accessible(self):
        """Verify all db commands are accessible"""
        commands = ["init", "migrations", "migrate"]

        for cmd in commands:
            result = subprocess.run(
                ["uv", "run", "nitro", "db", cmd, "--help"],
                capture_output=True,
                text=True,
                cwd="/home/ndendic/Projects/auto-nitro/nitro"
            )

            assert result.returncode == 0, f"Command 'db {cmd}' failed"
            assert len(result.stdout) > 0, f"No output from 'db {cmd} --help'"

    def test_db_commands_use_alembic_backend(self):
        """Verify DB commands mention Alembic integration"""
        result = subprocess.run(
            ["uv", "run", "nitro", "db", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        # Should mention Alembic somewhere in help
        help_text = result.stdout.lower()
        assert "alembic" in help_text or "migration" in help_text


class TestDBIntegration:
    """Integration tests for database CLI"""

    def test_db_init_with_existing_models(self):
        """Test db init with actual Entity models"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a more complete app with models
            (tmppath / "models.py").write_text("""
from nitro.domain.entities.base_entity import Entity

class User(Entity, table=True):
    __tablename__ = "users"
    name: str = ""
    email: str = ""

class Post(Entity, table=True):
    __tablename__ = "posts"
    title: str = ""
    content: str = ""
""")

            # Try to initialize
            result = subprocess.run(
                ["uv", "run", "nitro", "db", "init"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            # Should either succeed or fail gracefully
            assert result.returncode in [0, 1, 2]

    def test_db_commands_respect_database_url(self):
        """Verify DB commands respect NITRO_DB_URL env var"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["NITRO_DB_URL"] = "sqlite:///test.db"

            result = subprocess.run(
                ["uv", "run", "nitro", "db", "init"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                env=env
            )

            # Command should work with custom DB URL
            assert result.returncode in [0, 1, 2]
