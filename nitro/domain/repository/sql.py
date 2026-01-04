from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, Generator, List, Optional, Type, Union, get_args, get_origin
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from sqlmodel import Session, SQLModel, create_engine, select

from .base import EntityRepositoryInterface
from nitro.config import NitroConfig

config = NitroConfig()

class SQLModelRepository(EntityRepositoryInterface):

    _instance = None
    _initialized = False

    def __new__(
        cls,
        url: Optional[str] = config.db_url,
        echo: bool = False,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        pool_timeout: Optional[float] = None,
        **engine_kwargs
    ):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            # Build engine creation kwargs
            create_kwargs = {"echo": echo}

            # Add pool configuration if provided (only for non-SQLite databases)
            # SQLite uses SingletonThreadPool which doesn't support these parameters
            is_sqlite = url and url.startswith("sqlite:")

            if not is_sqlite:
                if pool_size is not None:
                    create_kwargs["pool_size"] = pool_size
                if max_overflow is not None:
                    create_kwargs["max_overflow"] = max_overflow
                if pool_timeout is not None:
                    create_kwargs["pool_timeout"] = pool_timeout

            # Add any additional engine kwargs
            create_kwargs.update(engine_kwargs)

            cls._instance.engine = create_engine(url, **create_kwargs)
            cls._instance.pool_config = {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_timeout": pool_timeout
            }
        return cls._instance

    def __init__(
        self,
        url: Optional[str] = config.db_url,
        echo: bool = False,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        pool_timeout: Optional[float] = None,
        **engine_kwargs
    ):
        if not self._initialized:
            SQLModelRepository._initialized = True

    def init_db(self) -> None:
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        with Session(self.engine) as session:
            yield session

    def schema(self) -> str:
        inspector = sa.inspect(self.engine)
        res = ""
        for table_name in inspector.get_table_names():
            res += f"Table: {table_name}\n"
            pk_cols = inspector.get_pk_constraint(table_name)["constrained_columns"]
            for column in inspector.get_columns(table_name):
                pk_marker = "*" if column["name"] in pk_cols else "-"
                res += f"  {pk_marker} {column['name']}: {column['type']}\n"
        return res

    def all(self, model: Type[SQLModel]) -> List[SQLModel]:
        with Session(self.engine) as session:
            return session.exec(select(model)).all()

    def filter(
        self,
        model: Type[SQLModel],
        sorting_field: Optional[str] = None,
        sort_direction: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        as_dict: bool = False,
        fields: Optional[List[str]] = None,
        exact_match: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            # Validate that all filter fields exist in the model
            invalid_fields = [field for field in kwargs.keys() if field not in model.model_fields]
            if invalid_fields:
                raise ValueError(f"Invalid fields for filtering: {', '.join(invalid_fields)}")

            # Build the base query
            if fields:
                query = select(*[getattr(model, field) for field in fields])
            else:
                query = select(model)

            # Add filters for each kwarg
            for field, value in kwargs.items():
                if value is None:
                    query = query.filter(getattr(model, field).is_(None))
                    continue

                field_type = model.model_fields[field].annotation
                # Get the underlying type if it's Optional
                if get_origin(field_type) is Union:
                    # Optional[T] is actually Union[T, None]
                    field_type = next((t for t in get_args(field_type) if t is not type(None)), str)

                if not exact_match and isinstance(value, str):
                    query = query.filter(getattr(model, field).ilike(f"%{value}%"))
                else:
                    # Handle different field types
                    if field_type in (str, Optional[str]):
                        if exact_match:
                            query = query.filter(getattr(model, field) == value)
                        else:
                            query = query.filter(getattr(model, field).ilike(f"%{value}%"))
                    
                    elif field_type in (int, float, Decimal, bool, Optional[int], Optional[float], Optional[Decimal], Optional[bool]):
                        query = query.filter(getattr(model, field) == value)
                    
                    elif field_type in (datetime, date, Optional[datetime], Optional[date]):
                        # Handle date/datetime range queries
                        if isinstance(value, (list, tuple)) and len(value) == 2:
                            start, end = value
                            query = query.filter(
                                getattr(model, field).between(start, end)
                            )
                        else:
                            query = query.filter(getattr(model, field) == value)
                    elif field_type is UUID:
                        # Handle UUID fields, converting string to UUID if needed
                        if isinstance(value, str):
                            try:
                                value = UUID(value)
                            except ValueError:
                                raise ValueError(f"Invalid UUID format for field {field}: {value}")
                        query = query.filter(getattr(model, field) == value)
                    
                    elif isinstance(value, (list, tuple)):
                        # Handle IN queries for lists
                        query = query.filter(getattr(model, field).in_(value))
                    
                    else:
                        # Default to exact match for unknown types
                        query = query.filter(getattr(model, field) == value)

            # Add sorting
            if sorting_field:
                if sorting_field in model.model_fields:
                    order_field = getattr(model, sorting_field)
                    query = query.order_by(
                        order_field.desc()
                        if sort_direction.lower() == "desc"
                        else order_field
                    )
                else:
                    raise ValueError(
                        f"Sorting field '{sorting_field}' does not exist in the model."
                    )
            else:
                query = query.order_by(model.id)

            # Add pagination
            if limit is not None:
                query = query.limit(limit)

            if offset is not None:
                query = query.offset(offset)

            results = session.exec(query).all()

            if as_dict:
                return [result.dict() for result in results]
            return results

    def search(
        self,
        model: Type[SQLModel],
        search_value: Optional[str] = None,
        sorting_field: Optional[str] = None,
        sort_direction: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        as_dict: bool = False,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            if fields:
                query = select(*[getattr(model, field) for field in fields])
            else:
                query = select(model)

            if search_value:
                string_fields = [
                    k for k, v in model.model_fields.items() if v.annotation is str
                ]
                if string_fields:
                    conditions = [
                        getattr(model, field).ilike(f"%{search_value}%")
                        for field in string_fields
                    ]
                    query = query.filter(or_(*conditions))

            if sorting_field:
                if sorting_field in model.model_fields:
                    order_field = getattr(model, sorting_field)
                    query = query.order_by(
                        order_field.desc()
                        if sort_direction.lower() == "desc"
                        else order_field
                    )
                else:
                    raise ValueError(
                        f"Sorting field '{sorting_field}' does not exist in the model."
                    )
            else:
                query = query.order_by(model.id)

            if limit is not None:
                query = query.limit(limit)

            if offset is not None:
                query = query.offset(offset)

            results = session.exec(query).all()

            if as_dict:
                dict_results = [result.model_dump() for result in results]
                return dict_results
            else:
                return results

    def get(self, model: Type[SQLModel], id: Any) -> Optional[SQLModel]:
        """Get an entity by ID. Alias for find()."""
        return self.find(model, id)

    def find(self, model: Type[SQLModel], id: Any) -> Optional[SQLModel]:
        with Session(self.engine) as session:
            # Build query with eager loading for all relationships
            stmt = select(model).where(model.id == id)

            # Eagerly load all relationships to avoid DetachedInstanceError
            for attr_name in dir(model):
                if not attr_name.startswith('_'):
                    attr = getattr(model, attr_name, None)
                    # Check if it's a relationship attribute
                    if hasattr(attr, 'property') and hasattr(attr.property, 'mapper'):
                        stmt = stmt.options(selectinload(attr))

            result = session.exec(stmt).first()

            # If not found with relationships, try simple get
            if result is None:
                result = session.get(model, id)

            # Ensure all relationships are loaded before returning
            if result:
                # Access relationships to trigger loading while session is active
                for attr_name in dir(model):
                    if not attr_name.startswith('_'):
                        try:
                            attr = getattr(model, attr_name, None)
                            if hasattr(attr, 'property') and hasattr(attr.property, 'mapper'):
                                # Access the relationship to load it
                                getattr(result, attr_name)
                        except:
                            pass

            return result

    def find_by(self, model: Type[SQLModel], **kwargs) -> Optional[SQLModel]:
        with Session(self.engine) as session:
            query = select(model)
            for key, value in kwargs.items():
                query = query.where(getattr(model, key) == value)
            return session.exec(query).first()
        
    def exists(self, model: Type[SQLModel], id: Any) -> bool:
        with Session(self.engine) as session:
            return session.get(model, id) is not None

    def update(self, model: Type[SQLModel], id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        with Session(self.engine) as session:
            record = session.get(model, id)
            if not record:
                raise Exception(f"Record with id {id} not found")
            for key, value in data.items():
                setattr(record, key, value)
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.model_dump()


    def delete(self, record: SQLModel) -> bool:
        with Session(self.engine) as session:
            db_record = session.get(type(record), record.id)
            if db_record:
                session.delete(db_record)
                session.commit()
                return True
            return False


    def save(self, record: SQLModel) -> bool:
        data = record.model_dump()
        model = type(record)

        # Get model fields to filter out computed fields
        model_fields = model.model_fields
        computed_fields = set()

        # Identify computed fields (they have no setter)
        for field_name in data.keys():
            if field_name not in model_fields:
                # Check if it's a computed field
                attr = getattr(model, field_name, None)
                if attr and isinstance(attr, property) and not attr.fset:
                    computed_fields.add(field_name)

        # Remove computed fields from data
        data = {k: v for k, v in data.items() if k not in computed_fields}

        with Session(self.engine) as session:
            if "id" in data:
                db_record = session.get(model, data["id"])
                if db_record:
                    for key, value in data.items():
                        setattr(db_record, key, value)
                else:
                    db_record = model(**data)
            else:
                db_record = model(**data)

            session.add(db_record)
            session.commit()
            session.refresh(db_record)

            # Update the original record with any database-generated values
            # But skip computed fields
            for key, value in db_record.model_dump().items():
                if key not in computed_fields:
                    setattr(record, key, value)

            return True


    def bulk_create(self, model: Type[SQLModel], data: List[Dict[str, Any]]) -> List[SQLModel]:
        with Session(self.engine) as session:
            records = [model(**item) for item in data]
            session.add_all(records)
            session.commit()
            for record in records:
                session.refresh(record)
            return records


    def bulk_upsert(self, model: Type[SQLModel], data: List[Dict[str, Any]]) -> List[SQLModel]:
        with Session(self.engine) as session:
            records = []
            for item in data:
                if "id" in item:
                    record = session.get(model, item["id"])
                    if record:
                        for key, value in item.items():
                            setattr(record, key, value)
                        records.append(record)
            session.add_all(records)
            session.commit()
            for record in records:
                session.refresh(record)
            return records


    def count(self, model: Type[SQLModel]) -> int:
        with Session(self.engine) as session:
            return session.exec(select(func.count()).select_from(model)).one()

    def where(
        self, model: Type[SQLModel],
        *expressions: Any,
        order_by: Optional[sa.Column|None|str] = None,
        limit: Optional[int|None] = None,
        offset: Optional[int|None] = None
    ) -> List[SQLModel]:
        with Session(self.engine) as session:
            query = select(model).where(*expressions)
            if order_by is not None:
                order_by = getattr(model, order_by) if isinstance(order_by, str) else order_by
                query = query.order_by(order_by)
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            return session.exec(query).all()