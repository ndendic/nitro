"""Tests for nitro config CLI commands."""

import json
import os

import pytest
from typer.testing import CliRunner

from nitro.cli.main import app

runner = CliRunner()


class TestConfigShow:
    """Tests for `nitro config show`."""

    def test_show_outputs_table(self):
        """Config show should output a table with config keys."""
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        # Table should contain known config keys
        assert "db_url" in result.output
        assert "project_root" in result.output
        assert "tailwind.css_input" in result.output
        assert "tailwind.css_output" in result.output

    def test_show_outputs_source_column(self):
        """Config show table should include a Source column."""
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        # Source column header and at least one 'default' row
        assert "Source" in result.output

    def test_show_json_flag_outputs_valid_json(self):
        """Config show --json should output valid JSON."""
        result = runner.invoke(app, ["config", "show", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "db_url" in data
        assert "project_root" in data
        assert "tailwind" in data
        assert "css_input" in data["tailwind"]
        assert "css_output" in data["tailwind"]
        assert "content_paths" in data["tailwind"]

    def test_show_json_contains_defaults(self):
        """Config show --json should contain default db_url."""
        result = runner.invoke(app, ["config", "show", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        # Default db_url is sqlite:///nitro.db
        assert "sqlite" in data["db_url"]

    def test_show_json_has_computed_fields(self):
        """Config show --json should include computed absolute paths."""
        result = runner.invoke(app, ["config", "show", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "css_input_absolute" in data["tailwind"]
        assert "css_output_absolute" in data["tailwind"]

    def test_show_env_override_reflected(self, monkeypatch):
        """Config show should reflect env var overrides."""
        monkeypatch.setenv("NITRO_DB_URL", "postgresql://user:pass@localhost/testdb")
        result = runner.invoke(app, ["config", "show", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["db_url"] == "postgresql://user:pass@localhost/testdb"


class TestConfigCheck:
    """Tests for `nitro config check`."""

    def test_check_runs_without_error_by_default(self):
        """Config check should run without crashing in default state."""
        result = runner.invoke(app, ["config", "check"])
        # Exit code 0 (OK) or 1 (warnings) — both are valid non-crash outcomes
        assert result.exit_code in (0, 1)

    def test_check_outputs_db_url_status(self):
        """Config check should report db_url status."""
        result = runner.invoke(app, ["config", "check"])
        assert "db_url" in result.output

    def test_check_outputs_tailwind_input_status(self):
        """Config check should report tailwind css_input status."""
        result = runner.invoke(app, ["config", "check"])
        assert "tailwind.css_input" in result.output

    def test_check_exit_code_zero_when_all_good(self, tmp_path, monkeypatch):
        """Config check should exit 0 when all paths exist."""
        # Create the expected paths
        css_dir = tmp_path / "static" / "css"
        css_dir.mkdir(parents=True)
        (css_dir / "input.css").write_text("/* input */")
        (css_dir / "output.css").write_text("/* output */")

        monkeypatch.setenv("NITRO_PROJECT_ROOT", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["config", "check"])
        assert result.exit_code == 0

    def test_check_shows_env_file_info(self, tmp_path, monkeypatch):
        """Config check should mention .env files."""
        monkeypatch.chdir(tmp_path)
        # No .env files exist
        result = runner.invoke(app, ["config", "check"])
        assert "env" in result.output.lower()

    def test_check_detects_env_file_present(self, tmp_path, monkeypatch):
        """Config check should detect .env file when present."""
        (tmp_path / ".env").write_text("NITRO_DB_URL=sqlite:///test.db\n")
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["config", "check"])
        assert ".env" in result.output


class TestConfigEnv:
    """Tests for `nitro config env`."""

    def test_env_lists_environment_variables(self):
        """Config env should list all supported env vars."""
        result = runner.invoke(app, ["config", "env"])
        assert result.exit_code == 0
        assert "NITRO_DB_URL" in result.output
        assert "NITRO_TAILWIND_CSS_INPUT" in result.output
        assert "NITRO_TAILWIND_CSS_OUTPUT" in result.output
        assert "NITRO_TAILWIND_CONTENT_PATHS" in result.output

    def test_env_shows_descriptions(self):
        """Config env table should include descriptions."""
        result = runner.invoke(app, ["config", "env"])
        assert result.exit_code == 0
        assert "Database" in result.output

    def test_env_shows_current_value_when_set(self, monkeypatch):
        """Config env should show current value when env var is set."""
        monkeypatch.setenv("NITRO_DB_URL", "sqlite:///custom.db")
        result = runner.invoke(app, ["config", "env"])
        assert result.exit_code == 0
        assert "sqlite:///custom.db" in result.output

    def test_env_shows_loaded_env_files(self, tmp_path, monkeypatch):
        """Config env should show which .env files are loaded."""
        (tmp_path / ".env").write_text("NITRO_DB_URL=sqlite:///test.db\n")
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["config", "env"])
        assert result.exit_code == 0
        assert ".env" in result.output

    def test_env_shows_no_env_files_message_when_absent(self, tmp_path, monkeypatch):
        """Config env should say no .env files when none exist."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["config", "env"])
        assert result.exit_code == 0
        assert "No .env" in result.output or "none" in result.output.lower()


class TestConfigHelp:
    """Tests for CLI help text."""

    def test_config_group_has_help(self):
        """The config group should have help text."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "show" in result.output
        assert "check" in result.output
        assert "env" in result.output

    def test_show_has_json_option_in_help(self):
        """Config show --help should mention --json option."""
        result = runner.invoke(app, ["config", "show", "--help"])
        assert result.exit_code == 0
        assert "--json" in result.output
