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
from nitro.infrastructure.events.events import event

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Entity(SQLModel):
    """SQL-backed entity without mixin inheritance to avoid metaclass conflicts."""
    
    # SQLAlchemy table configuration
    __table_args__ = {'extend_existing': True}
    _repository: ClassVar[SQLModelRepository] = SQLModelRepository()

    # Pydantic model configuration (for validation/serialization)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        validate_assignment=True,
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )

    
    id: str = Field(primary_key=True)

    @classmethod
    def get(cls, id: Any) -> Optional["Entity"]:
        return cls._repository.get(cls, id)

    @classmethod
    def exists(cls, id: Any) -> bool:
        return cls._repository.exists(cls, id)

    def save(self) -> bool:
        return self._repository.save(self)

    def delete(self) -> bool:
        return self._repository.delete(self)

    @classmethod
    def all(cls) -> List["Entity"]:
        return cls._repository.all(cls)

    @classmethod
    def where(
        cls,
        *expressions: Any,
        order_by: Optional[sa.Column|None] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List["Entity"]:
        return cls._repository.where(cls, *expressions, order_by=order_by, limit=limit, offset=offset)

    @classmethod
    def find(cls, id: Any) -> Optional["Entity"]:
        return cls._repository.find(cls, id)

    @classmethod
    def find_by(cls, **kwargs) -> Union[List["Entity"], "Entity", None]:
        return cls._repository.find_by(cls, **kwargs)

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
        return cls._repository.search(
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
        return cls._repository.filter(
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