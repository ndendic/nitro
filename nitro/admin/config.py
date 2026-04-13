"""Admin site and per-entity configuration."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from nitro.crud.config import CRUDConfig, _pluralize


class AdminEntityConfig(CRUDConfig):
    """Per-entity admin configuration — extends CRUDConfig with admin extras."""

    category: str = ""
    """Group label in the sidebar (e.g. 'Content', 'Users'). Empty = ungrouped."""

    priority: int = 0
    """Sort order within its category (lower = higher in sidebar)."""

    visible: bool = True
    """Show in sidebar navigation. Set False to register routes but hide from nav."""

    dashboard_visible: bool = True
    """Show on the dashboard card grid."""

    description: str = ""
    """Short description shown on dashboard cards."""

    def resolve(self, entity_class) -> AdminEntityConfig:
        """Return a copy with auto-derived fields filled in, preserving admin fields."""
        # Get base CRUD resolution
        crud_resolved = super().resolve(entity_class)
        # Merge: CRUD-resolved fields + our admin-specific fields
        data = crud_resolved.model_dump()
        for field_name in ("category", "priority", "visible", "dashboard_visible", "description"):
            data[field_name] = getattr(self, field_name)
        return AdminEntityConfig(**data)


class AdminSite(BaseModel):
    """Top-level admin site configuration."""

    title: str = "Admin"
    """Page title and header text."""

    url_prefix: str = "/admin"
    """URL prefix for all admin routes."""

    brand_icon: str = "shield"
    """Lucide icon for the sidebar header."""

    entities: dict[str, AdminEntityConfig] = {}
    """Per-entity configs keyed by entity class name.

    Entities not listed here get auto-derived defaults.
    """

    sidebar_width: str = "w-64"
    """Tailwind width class for the sidebar."""

    accent_color: str = "primary"
    """CSS accent colour token for active elements."""

    def config_for(self, entity_class) -> AdminEntityConfig:
        """Return resolved AdminEntityConfig for *entity_class*.

        Uses the explicit config if one was registered for this class name,
        otherwise auto-derives from the class.
        """
        name = entity_class.__name__
        cfg = self.entities.get(name, AdminEntityConfig())
        return cfg.resolve(entity_class)
