"""Nitro project configuration using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TailwindConfig(BaseSettings):
    """Tailwind CSS configuration."""

    model_config = SettingsConfigDict(
        env_prefix="NITRO_TAILWIND_",
        case_sensitive=False,
    )

    css_input: Path = Field(default=Path("static/css/input.css"), description="Path to Tailwind input CSS file")
    css_output: Path = Field(default=Path("static/css/output.css"), description="Path to Tailwind output CSS file")
    content_paths: list[str] = Field(
        default=["**/*.py", "**/*.html", "**/*.jinja2", "!**/__pycache__/**", "!**/test_*.py"],
        description="Content paths for Tailwind to scan"
    )


class NitroConfig(BaseSettings):
    """Nitro project configuration with environment support."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.prod"),
        env_file_encoding="utf-8",
        env_prefix="NITRO_",
        case_sensitive=False,
        extra="ignore"
    )

    project_root: Path = Field(default_factory=Path.cwd, description="Project root directory")
    tailwind: TailwindConfig = Field(default_factory=TailwindConfig, description="Tailwind CSS configuration")
    db_url: str = Field(default="sqlite:///nitro.db", description="Database URL")
    @computed_field
    @property
    def css_input_absolute(self) -> Path:
        """Get absolute path to CSS input file."""
        return self._absolute(self.tailwind.css_input)

    @computed_field
    @property
    def css_output_absolute(self) -> Path:
        """Get absolute path to CSS output file."""
        return self._absolute(self.tailwind.css_output)

    @computed_field
    @property
    def css_dir_absolute(self) -> Path:
        """Get absolute path to CSS directory."""
        return self.css_output_absolute.parent

    def _absolute(self, path: Path) -> Path:
        """Convert relative path to absolute based on project root."""
        return path if path.is_absolute() else self.project_root / path


def detect_css_paths(root: Path) -> tuple[Path, Path]:
    """Detect appropriate CSS input and output paths based on project structure."""
    if (root / "static").exists():
        return Path("static/css/input.css"), Path("static/css/output.css")
    if (root / "assets").exists():
        return Path("assets/input.css"), Path("assets/output.css")
    return Path("input.css"), Path("output.css")


def get_nitro_config(project_root: Optional[Path] = None) -> NitroConfig:
    """Get Nitro configuration with auto-detection and environment override support."""
    root = project_root or Path.cwd()

    # Create config classes that look for .env in the current working directory
    from pydantic_settings import SettingsConfigDict

    # Update the settings to look in the current directory for .env files
    class LocalTailwindConfig(TailwindConfig):
        model_config = SettingsConfigDict(
            env_file=(
                str(root / ".env"),
                str(root / ".env.local"),
                str(root / ".env.prod")
            ),
            env_file_encoding="utf-8",
            env_prefix="NITRO_TAILWIND_",
            case_sensitive=False,
            extra="ignore"  # Ignore extra variables in .env file
        )

    class LocalNitroConfig(NitroConfig):
        model_config = SettingsConfigDict(
            env_file=(
                str(root / ".env"),
                str(root / ".env.local"),
                str(root / ".env.prod")
            ),
            env_file_encoding="utf-8",
            env_prefix="NITRO_",
            case_sensitive=False,
            extra="ignore"
        )

    # Create Tailwind config first to check if env vars are present
    tailwind_config = LocalTailwindConfig()

    # If no environment variables were loaded, set detected defaults
    if tailwind_config.css_input == Path("static/css/input.css") and tailwind_config.css_output == Path("static/css/output.css"):
        # Use auto-detected paths only if env vars not set
        css_input, css_output = detect_css_paths(root)
        tailwind_config = LocalTailwindConfig(
            css_input=css_input,
            css_output=css_output
        )

    # Create main config
    config = LocalNitroConfig(
        project_root=root,
        tailwind=tailwind_config
    )

    return config


def get_content_patterns(project_root: Path) -> list[str]:
    """Get content patterns for Tailwind to scan."""
    config = get_nitro_config(project_root)
    return config.tailwind.content_paths


# Backward compatibility aliases
ProjectConfig = NitroConfig
detect_project_config = get_nitro_config
get_project_config = get_nitro_config
