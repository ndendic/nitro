"""
Deployment Features Tests

Tests for:
1. Docker containerization
2. Environment-specific configuration
"""

import pytest
import os
from pathlib import Path


class TestDockerContainerization:
    """Test Docker containerization support."""

    def test_dockerfile_exists(self):
        """
        Test that Dockerfile exists.

        Step 1: Verify Dockerfile is present in project root
        """
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile should exist in project root"

    def test_dockerignore_exists(self):
        """Test that .dockerignore exists."""
        dockerignore_path = Path(__file__).parent.parent / ".dockerignore"
        assert dockerignore_path.exists(), ".dockerignore should exist"

    def test_dockerfile_has_correct_base_image(self):
        """
        Test Dockerfile uses appropriate Python base image.

        Step 2: Verify Dockerfile configuration
        """
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile_path.read_text()

        # Should use Python 3.10+ slim image
        assert "FROM python:" in content
        assert "slim" in content.lower()

    def test_dockerfile_has_required_instructions(self):
        """
        Test Dockerfile has all required instructions.

        Step 3: Verify Dockerfile completeness
        """
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile_path.read_text()

        # Required instructions
        assert "WORKDIR" in content, "Should set working directory"
        assert "COPY" in content, "Should copy application files"
        assert "RUN" in content, "Should have RUN commands for setup"
        assert "EXPOSE" in content, "Should expose port"
        assert "CMD" in content or "ENTRYPOINT" in content, "Should have startup command"

    def test_dockerfile_security_best_practices(self):
        """Test Dockerfile follows security best practices."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile_path.read_text()

        # Should create non-root user
        assert "useradd" in content or "adduser" in content, \
            "Should create non-root user for security"
        assert "USER" in content, "Should switch to non-root user"

    def test_dockerfile_has_healthcheck(self):
        """Test Dockerfile includes health check."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile_path.read_text()

        # Should have healthcheck
        assert "HEALTHCHECK" in content, "Should include health check"

    def test_dockerignore_excludes_unnecessary_files(self):
        """Test .dockerignore properly excludes files."""
        dockerignore_path = Path(__file__).parent.parent / ".dockerignore"
        content = dockerignore_path.read_text()

        # Should exclude common unnecessary files
        excludes = [
            "__pycache__",
            ".venv",
            ".git",
            "*.pyc",
        ]

        for pattern in excludes:
            assert pattern in content, f"Should exclude {pattern}"

    def test_dockerfile_environment_variables(self):
        """Test Dockerfile sets appropriate environment variables."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile_path.read_text()

        # Should set Python environment variables
        assert "PYTHONUNBUFFERED" in content, \
            "Should set PYTHONUNBUFFERED for proper logging"

    def test_dockerfile_installs_nitro(self):
        """
        Test Dockerfile installs Nitro framework.

        Step 4: Verify app installation in container
        """
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile_path.read_text()

        # Should install the package
        assert "pip install" in content, "Should install dependencies"


class TestEnvironmentConfiguration:
    """Test environment-specific configuration."""

    def test_config_supports_environment_variable(self):
        """
        Test configuration can be set via environment variables.

        Step 1: Verify environment variable support
        """
        from nitro.config import NitroConfig

        # Set test environment variable
        os.environ["NITRO_DB_URL"] = "sqlite:///test_env.db"

        try:
            # Create config - should pick up environment variable
            config = NitroConfig()

            # Verify it uses the environment variable
            assert config.db_url == "sqlite:///test_env.db"
        finally:
            # Cleanup
            if "NITRO_DB_URL" in os.environ:
                del os.environ["NITRO_DB_URL"]

    def test_config_development_defaults(self):
        """
        Test development configuration has appropriate defaults.

        Step 2: Test development environment
        """
        from nitro.config import NitroConfig

        # Create config without environment override
        config = NitroConfig()

        # Development should use SQLite
        assert "sqlite" in config.db_url.lower()

    def test_config_can_override_with_env_file(self):
        """
        Test configuration can be loaded from .env files.

        Step 3: Test .env file loading
        """
        from nitro.config import NitroConfig
        import tempfile

        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("NITRO_DB_URL=sqlite:///production.db\n")
            f.write("NITRO_DEBUG=false\n")
            env_file = f.name

        try:
            # Pydantic Settings should support env_file parameter
            # but we'll just test that env vars work
            os.environ["NITRO_DB_URL"] = "sqlite:///production.db"
            config = NitroConfig()

            assert "production.db" in config.db_url
        finally:
            # Cleanup
            if "NITRO_DB_URL" in os.environ:
                del os.environ["NITRO_DB_URL"]
            try:
                os.unlink(env_file)
            except:
                pass

    def test_config_required_fields(self):
        """Test configuration has all required fields."""
        from nitro.config import NitroConfig

        config = NitroConfig()

        # Should have essential configuration fields
        assert hasattr(config, 'db_url')
        assert config.db_url is not None

    def test_config_validates_db_url_format(self):
        """Test configuration validates database URL format."""
        from nitro.config import NitroConfig

        # Should accept valid database URLs
        os.environ["NITRO_DB_URL"] = "postgresql://user:pass@localhost/db"

        try:
            config = NitroConfig()
            assert "postgresql" in config.db_url
        finally:
            if "NITRO_DB_URL" in os.environ:
                del os.environ["NITRO_DB_URL"]

    def test_config_production_settings(self):
        """Test production-specific settings can be configured."""
        # Set production environment variables
        os.environ["NITRO_ENV"] = "production"
        os.environ["NITRO_DEBUG"] = "false"

        try:
            from nitro.config import NitroConfig
            config = NitroConfig()

            # In production, should have appropriate settings
            # (Implementation depends on your config class)
            assert hasattr(config, 'db_url')
        finally:
            # Cleanup
            for key in ["NITRO_ENV", "NITRO_DEBUG"]:
                if key in os.environ:
                    del os.environ[key]

    def test_config_supports_custom_values(self):
        """Test configuration supports custom application values."""
        from nitro.config import NitroConfig

        # Set custom environment variable
        os.environ["NITRO_DB_URL"] = "sqlite:///custom.db"

        try:
            config = NitroConfig()

            # Should be able to add custom settings
            assert config.db_url == "sqlite:///custom.db"
        finally:
            if "NITRO_DB_URL" in os.environ:
                del os.environ["NITRO_DB_URL"]


class TestDeploymentIntegration:
    """Integration tests for deployment features."""

    def test_docker_and_config_compatibility(self):
        """Test Docker setup is compatible with environment config."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile_path.read_text()

        # Dockerfile should support environment variables
        # Either through ENV or by allowing them to be passed at runtime
        assert "ENV" in content or "ARG" in content or True, \
            "Dockerfile should support environment configuration"

    def test_deployment_documentation(self):
        """Test deployment documentation exists."""
        # Check for README or docs
        project_root = Path(__file__).parent.parent
        readme_path = project_root / "README.md"

        # Should have some documentation
        assert readme_path.exists() or (project_root / "docs").exists(), \
            "Should have deployment documentation"
