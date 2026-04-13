"""Configuration dataclasses for the scaffold generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

TemplateChoice = Literal["minimal", "auth", "fullstack"]

TEMPLATE_DESCRIPTIONS = {
    "minimal": "Production-ready starter — settings, health checks, structured logging",
    "auth": "App with user management — adds auth, sessions, login/register",
    "fullstack": "Complete production app — adds CRUD auto-views and i18n",
}


@dataclass
class ScaffoldConfig:
    """Configuration for a scaffold generation run.

    Attributes:
        name: Project name used in generated code and filenames.
        template: Template tier to generate (minimal, auth, fullstack).
        output_dir: Target directory path (used by CLI, not by generator).
    """

    name: str
    template: TemplateChoice = "minimal"
    output_dir: str = "."

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Project name cannot be empty")
        if self.template not in TEMPLATE_DESCRIPTIONS:
            raise ValueError(
                f"Unknown template '{self.template}'. "
                f"Choose from: {', '.join(TEMPLATE_DESCRIPTIONS)}"
            )

    @property
    def safe_name(self) -> str:
        """Identifier-safe version of the project name."""
        return self.name.replace("-", "_").replace(" ", "_")

    @property
    def description(self) -> str:
        """Human-readable description of the chosen template."""
        return TEMPLATE_DESCRIPTIONS[self.template]
