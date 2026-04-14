"""nitro.plugins — Plugin metadata model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PluginMeta(BaseModel):
    """Metadata describing a Nitro plugin.

    Used for display, dependency resolution, and compatibility checks.
    """

    name: str = Field(..., description="Unique plugin identifier (kebab-case)")
    version: str = Field(..., description="SemVer version string")
    description: str = Field(default="", description="Human-readable summary")
    author: str = Field(default="", description="Plugin author")
    dependencies: List[str] = Field(
        default_factory=list,
        description="Names of plugins that must be set up first",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Categorization tags",
    )
    config_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON-Schema-like dict describing accepted config keys",
    )
