"""Tests for the `nitro create` CLI command using typer's CliRunner."""

import uuid
import pytest
from typer.testing import CliRunner

from nitro.cli.main import app


runner = CliRunner()


def _unique(prefix: str) -> str:
    """Return a unique project name so parallel runs don't collide."""
    return f"{prefix}_{uuid.uuid4().hex[:6]}"


class TestCreateCommand:
    def test_create_help(self):
        """The create command should show help without errors."""
        result = runner.invoke(app, ["create", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output.lower() or "nitro" in result.output.lower()

    def test_create_minimal_template(self, tmp_path, monkeypatch):
        """nitro create <name> --template minimal writes expected files."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["create", "myapp", "--template", "minimal"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "main.py" in result.output
        assert "settings.py" in result.output
        assert "entities.py" in result.output
        assert ".env.example" in result.output

    def test_create_auth_template(self, tmp_path, monkeypatch):
        """nitro create <name> --template auth writes auth_views.py."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["create", "myapp", "--template", "auth"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "auth_views.py" in result.output

    def test_create_fullstack_template(self, tmp_path, monkeypatch):
        """nitro create <name> --template fullstack writes locale files."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["create", "myapp", "--template", "fullstack"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "locales/en.json" in result.output
        assert "locales/sr.json" in result.output

    def test_create_invalid_template(self, tmp_path, monkeypatch):
        """An unknown template name exits with code 1."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["create", "badproject", "--template", "nonexistent"],
        )
        assert result.exit_code != 0

    def test_create_writes_files_to_disk(self, tmp_path, monkeypatch):
        """Files are actually written under cwd/<name>/."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["create", "disktest", "--template", "minimal"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        project_dir = tmp_path / "disktest"
        assert (project_dir / "main.py").exists()
        assert (project_dir / "settings.py").exists()
        assert (project_dir / "entities.py").exists()

    def test_create_verbose_shows_each_file(self, tmp_path, monkeypatch):
        """--verbose flag causes each file to be printed individually."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["create", "myapp", "--template", "minimal", "--verbose"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # Verbose output should include "Created:" prefix
        assert "Created:" in result.output

    def test_create_shows_next_steps(self, tmp_path, monkeypatch):
        """The output should include next-step instructions."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["create", "myapp", "--template", "minimal"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert "next steps" in output_lower or "next" in output_lower

    def test_create_force_flag_overwrites(self, tmp_path, monkeypatch):
        """--force flag allows overwriting an existing non-empty directory."""
        monkeypatch.chdir(tmp_path)
        # First creation
        runner.invoke(
            app,
            ["create", "existing", "--template", "minimal"],
            catch_exceptions=False,
        )
        # Second creation with --force should succeed
        result = runner.invoke(
            app,
            ["create", "existing", "--template", "minimal", "--force"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

    def test_create_command_registered_in_main_app(self):
        """The top-level 'nitro --help' output should list 'create'."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "create" in result.output
