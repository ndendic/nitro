"""
Nitro Auth — User entity.

Uses Nitro's Entity base class (SQLModel-backed Active Record).
Roles are stored as a comma-separated string to stay SQLite-compatible.
"""

from nitro.domain.entities.base_entity import Entity
from sqlmodel import Field
from typing import Optional
from datetime import datetime, timezone


class User(Entity, table=True):
    __tablename__ = "auth_users"

    email: str = Field(unique=True, index=True)
    hashed_password: str = ""
    display_name: str = ""
    is_active: bool = True
    is_superuser: bool = False
    roles: str = ""  # comma-separated roles (JSON column breaks SQLite)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    @property
    def role_list(self) -> list[str]:
        return [r.strip() for r in self.roles.split(",") if r.strip()]

    def has_role(self, role: str) -> bool:
        return role in self.role_list

    def add_role(self, role: str):
        roles = self.role_list
        if role not in roles:
            roles.append(role)
            self.roles = ",".join(roles)

    def remove_role(self, role: str):
        self.roles = ",".join(r for r in self.role_list if r != role)
