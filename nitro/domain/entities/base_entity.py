"""
Fixed SQLEntity implementation without mixin inheritance.

This version copies essential functionality from mixins directly into the class
to avoid metaclass conflicts with SQLModel.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, ClassVar, Union

from sqlmodel import SQLModel, Field
import sqlalchemy as sa
from pydantic import ConfigDict

from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.infrastructure.html.datastar import Signals

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Entity(SQLModel):
    """SQL-backed entity without mixin inheritance to avoid metaclass conflicts."""
    
    # SQLAlchemy table configuration
    __table_args__ = {'extend_existing': True}
    
    # Pydantic model configuration (for validation/serialization)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        validate_assignment=True,
        json_encoders={datetime: lambda dt: dt.isoformat()},
    )


    id: str = Field(primary_key=True)

    @classmethod
    def repository(cls) -> SQLModelRepository:
        """Get the singleton repository instance."""
        return SQLModelRepository()

    @classmethod
    def get(cls, id: Any) -> Optional["Entity"]:
        return cls.repository().get(cls, id)

    @classmethod
    def exists(cls, id: Any) -> bool:
        return cls.repository().exists(cls, id)

    def save(self) -> bool:
        return self.repository().save(self)

    def delete(self) -> bool:
        return self.repository().delete(self)

    @classmethod
    def all(cls) -> List["Entity"]:
        return cls.repository().all(cls)

    @classmethod
    def where(
        cls,
        *expressions: Any,
        order_by: Optional[sa.Column|None] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List["Entity"]:
        # return ("This is a test")
        return cls.repository().where(cls, *expressions, order_by=order_by, limit=limit, offset=offset)

    @classmethod
    def find(cls, id: Any) -> Optional["Entity"]:
        return cls.repository().find(cls, id)

    @classmethod
    def find_by(cls, **kwargs) -> Union[List["Entity"], "Entity", None]:
        return cls.repository().find_by(cls, **kwargs)

    @classmethod
    def search(
        cls,
        search_value: Optional[str] = None,
        sorting_field: Optional[str] = None,
        sort_direction: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        as_dict: bool = False,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        return cls.repository().search(
            cls,
            search_value=search_value,
            sorting_field=sorting_field,
            sort_direction=sort_direction,
            limit=limit,
            offset=offset,
            as_dict=as_dict,
            fields=fields,
        )

    @classmethod
    def filter(cls,
        sorting_field: Optional[str] = None,
        sort_direction: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        as_dict: bool = False,
        fields: Optional[List[str]] = None,
        exact_match: bool = True,  # This parameter is correctly defined here
        **kwargs
    ) -> List["Entity"]:
        return cls.repository().filter(
            model=cls,
            sorting_field=sorting_field,
            sort_direction=sort_direction,
            limit=limit,
            offset=offset,
            as_dict=as_dict,
            fields=fields,
            exact_match=exact_match,  # But it needs to be explicitly passed here
            **kwargs
        )

    @property
    def signals(self) -> Signals:
        return Signals(**self.model_dump())
