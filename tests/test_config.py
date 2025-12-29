"""Tests for Nitro configuration system."""

import os
import tempfile
from pathlib import Path

import pytest

from nitro.config import NitroConfig, TailwindConfig, get_nitro_config, detect_css_paths


class TestNitroConfigEnvironmentVariables:
    """Test NitroConfig loading from environment variables."""

    def test_config_loads_from_environment_variables(self, monkeypatch):
        """Test that NitroConfig loads values from environment variables."""
        # Set environment variables
        monkeypatch.setenv("NITRO_DB_URL", "postgresql://localhost/testdb")
        monkeypatch.setenv("NITRO_TAILWIND_CSS_INPUT", "custom/input.css")
        monkeypatch.setenv("NITRO_TAILWIND_CSS_OUTPUT", "custom/output.css")

        # Create config
        config = NitroConfig()

        # Verify values from env vars
        assert config.db_url == "postgresql://localhost/testdb"
        assert config.tailwind.css_input == Path("custom/input.css")
        assert config.tailwind.css_output == Path("custom/output.css")

    def test_config_db_url_from_env(self, monkeypatch):
        """Test that db_url specifically loads from NITRO_DB_URL env var."""
        test_url = "mysql://user:pass@localhost/mydb"
        monkeypatch.setenv("NITRO_DB_URL", test_url)

        config = NitroConfig()

        assert config.db_url == test_url

    def test_tailwind_config_loads_from_env(self, monkeypatch):
        """Test that TailwindConfig loads from NITRO_TAILWIND_* env vars."""
        monkeypatch.setenv("NITRO_TAILWIND_CSS_INPUT", "src/styles/input.css")
        monkeypatch.setenv("NITRO_TAILWIND_CSS_OUTPUT", "dist/styles/output.css")

        config = TailwindConfig()

        assert config.css_input == Path("src/styles/input.css")
        assert config.css_output == Path("dist/styles/output.css")


class TestNitroConfigDotEnvFile:
    """Test NitroConfig loading from .env file."""

    def test_config_loads_from_dotenv_file(self, tmp_path, monkeypatch):
        """Test that NitroConfig loads from .env file."""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            "NITRO_DB_URL=sqlite:///test.db\n"
            "NITRO_TAILWIND_CSS_INPUT=assets/input.css\n"
            "NITRO_TAILWIND_CSS_OUTPUT=assets/output.css\n"
        )

        # Change to temp directory so .env is found
        monkeypatch.chdir(tmp_path)

        # Create config (should load from .env)
        config = get_nitro_config(tmp_path)

        # Verify values loaded from .env
        assert config.db_url == "sqlite:///test.db"
        assert config.tailwind.css_input == Path("assets/input.css")
        assert config.tailwind.css_output == Path("assets/output.css")

    def test_config_prefers_env_vars_over_dotenv(self, tmp_path, monkeypatch):
        """Test that environment variables take precedence over .env file."""
        # Create .env file with one value
        env_file = tmp_path / ".env"
        env_file.write_text("NITRO_DB_URL=sqlite:///from_file.db\n")

        # Set environment variable with different value
        monkeypatch.setenv("NITRO_DB_URL", "postgresql://from_env")
        monkeypatch.chdir(tmp_path)

        config = NitroConfig()

        # Environment variable should win
        assert config.db_url == "postgresql://from_env"


class TestNitroConfigDefaults:
    """Test NitroConfig default values."""

    def test_config_has_sensible_defaults(self):
        """Test that NitroConfig has sensible default values."""
        config = NitroConfig()

        # Check default db_url is sqlite
        assert config.db_url == "sqlite:///nitro.db"
        assert "sqlite" in config.db_url.lower()

        # Check default Tailwind paths are set
        assert config.tailwind.css_input == Path("static/css/input.css")
        assert config.tailwind.css_output == Path("static/css/output.css")

    def test_config_default_tailwind_content_paths(self):
        """Test that default Tailwind content paths are set."""
        config = NitroConfig()

        # Check default content paths include common patterns
        content_paths = config.tailwind.content_paths
        assert "**/*.py" in content_paths
        assert "**/*.html" in content_paths
        assert "**/*.jinja2" in content_paths

        # Check test files are excluded
        assert "!**/test_*.py" in content_paths

    def test_config_default_project_root(self):
        """Test that project_root defaults to current directory."""
        config = NitroConfig()

        assert config.project_root == Path.cwd()


class TestNitroConfigValidation:
    """Test NitroConfig validation."""

    def test_config_validates_tailwind_content_paths_is_list(self, monkeypatch):
        """Test that content_paths must be a list."""
        # Set invalid content_paths (string instead of list)
        monkeypatch.setenv("NITRO_TAILWIND_CONTENT_PATHS", "not-a-list")

        # This should raise a validation error
        with pytest.raises(Exception):  # Pydantic will raise validation error
            config = TailwindConfig()
            # Force validation by accessing the field
            _ = config.tailwind.content_paths

    def test_config_accepts_valid_content_paths_list(self, monkeypatch):
        """Test that valid content_paths list is accepted."""
        # Set valid content_paths as JSON list
        import json
        valid_paths = ["**/*.py", "**/*.html"]
        monkeypatch.setenv("NITRO_TAILWIND_CONTENT_PATHS", json.dumps(valid_paths))

        config = TailwindConfig()

        # Should load successfully
        assert config.content_paths == valid_paths


class TestDetectCssPaths:
    """Test CSS path detection logic."""

    def test_detect_css_paths_with_static_dir(self, tmp_path):
        """Test that static/ directory is detected."""
        # Create static directory
        (tmp_path / "static").mkdir()

        input_path, output_path = detect_css_paths(tmp_path)

        assert input_path == Path("static/css/input.css")
        assert output_path == Path("static/css/output.css")

    def test_detect_css_paths_with_assets_dir(self, tmp_path):
        """Test that assets/ directory is detected."""
        # Create assets directory (no static)
        (tmp_path / "assets").mkdir()

        input_path, output_path = detect_css_paths(tmp_path)

        assert input_path == Path("assets/input.css")
        assert output_path == Path("assets/output.css")

    def test_detect_css_paths_fallback(self, tmp_path):
        """Test fallback when neither static/ nor assets/ exist."""
        # Don't create any directories

        input_path, output_path = detect_css_paths(tmp_path)

        assert input_path == Path("input.css")
        assert output_path == Path("output.css")

    def test_detect_css_paths_prefers_static_over_assets(self, tmp_path):
        """Test that static/ is preferred when both static/ and assets/ exist."""
        # Create both directories
        (tmp_path / "static").mkdir()
        (tmp_path / "assets").mkdir()

        input_path, output_path = detect_css_paths(tmp_path)

        # Should prefer static
        assert input_path == Path("static/css/input.css")
        assert output_path == Path("static/css/output.css")


class TestGetNitroConfig:
    """Test get_nitro_config helper function."""

    def test_get_nitro_config_with_custom_root(self, tmp_path):
        """Test get_nitro_config with custom project root."""
        config = get_nitro_config(tmp_path)

        assert config.project_root == tmp_path

    def test_get_nitro_config_defaults_to_cwd(self):
        """Test get_nitro_config defaults to current working directory."""
        config = get_nitro_config()

        assert config.project_root == Path.cwd()

    def test_get_nitro_config_auto_detects_css_paths(self, tmp_path):
        """Test that get_nitro_config auto-detects CSS paths based on project structure."""
        # Create static directory
        (tmp_path / "static").mkdir()

        config = get_nitro_config(tmp_path)

        # Should have detected static/ directory
        assert config.tailwind.css_input == Path("static/css/input.css")
        assert config.tailwind.css_output == Path("static/css/output.css")


class TestConfigAbsolutePaths:
    """Test absolute path computation."""

    def test_css_input_absolute_path(self, tmp_path):
        """Test css_input_absolute computed field."""
        config = NitroConfig(project_root=tmp_path)

        expected = tmp_path / "static/css/input.css"
        assert config.css_input_absolute == expected

    def test_css_output_absolute_path(self, tmp_path):
        """Test css_output_absolute computed field."""
        config = NitroConfig(project_root=tmp_path)

        expected = tmp_path / "static/css/output.css"
        assert config.css_output_absolute == expected

    def test_css_dir_absolute_path(self, tmp_path):
        """Test css_dir_absolute computed field."""
        config = NitroConfig(project_root=tmp_path)

        expected = tmp_path / "static/css"
        assert config.css_dir_absolute == expected


class TestConfigBackwardCompatibility:
    """Test backward compatibility aliases."""

    def test_project_config_alias_exists(self):
        """Test that ProjectConfig alias exists."""
        from nitro.config import ProjectConfig

        # Should be the same as NitroConfig
        assert ProjectConfig is NitroConfig

    def test_get_project_config_alias_exists(self):
        """Test that get_project_config alias exists."""
        from nitro.config import get_project_config

        # Should be the same as get_nitro_config
        assert get_project_config is get_nitro_config

    def test_detect_project_config_alias_exists(self):
        """Test that detect_project_config alias exists."""
        from nitro.config import detect_project_config

        # Should be the same as get_nitro_config
        assert detect_project_config is get_nitro_config
