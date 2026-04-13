"""PostgreSQL async repository using SQLAlchemy 2.0 + asyncpg.

Provides fully async entity persistence with connection pooling,
transactional operations, and all standard repository methods.

Requires: pip install sqlalchemy[asyncio] asyncpg
  or:     pip install nitro-boost[postgres]

Usage:
    from nitro.domain.repository.postgres import AsyncPostgresRepository

    repo = AsyncPostgresRepository(url="postgresql+asyncpg://user:pass@host/db")
    await repo.init_db()

    # Use with Entity by swapping the repository:
    Entity._repository = repo
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

try:
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        create_async_engine,
        async_sessionmaker,
    )
    HAS_ASYNC = True
except ImportError:
    HAS_ASYNC = False

from sqlmodel import SQLModel, select


class AsyncPostgresRepository:
    """Async PostgreSQL persistence backend using SQLAlchemy 2.0.

    Features:
    - Fully async CRUD operations
    - Connection pooling with configurable pool size
    - Eager relationship loading
    - Filtering, searching, sorting, pagination
    - Bulk create and upsert
    - Transactional context manager
    """

    _instance = None
    _initialized = False

    def __new__(
        cls,
        url: str = "postgresql+asyncpg://localhost/nitro",
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: float = 30.0,
        **engine_kwargs,
    ):
        if cls._instance is None:
            if not HAS_ASYNC:
                raise ImportError(
                    "sqlalchemy[asyncio] and asyncpg required: "
                    "pip install 'sqlalchemy[asyncio]' asyncpg"
                )
            cls._instance = super().__new__(cls)

            engine = create_async_engine(
                url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                **engine_kwargs,
            )
            cls._instance._engine = engine
            cls._instance._session_factory = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            cls._instance._url = url
            cls._instance.pool_config = {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_timeout": pool_timeout,
            }
        return cls._instance

    def __init__(self, url: str = "postgresql+asyncpg://localhost/nitro", **kwargs):
        if not self._initialized:
            AsyncPostgresRepository._initialized = True

    @classmethod
    def reset(cls):
        """Reset singleton — useful in tests."""
        cls._instance = None
        cls._initialized = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def init_db(self) -> None:
        """Create all tables from SQLModel metadata."""
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def drop_db(self) -> None:
        """Drop all tables — use in tests only."""
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)

    async def dispose(self) -> None:
        """Close all connections in the pool."""
        await self._engine.dispose()

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    def session(self) -> AsyncSession:
        """Get a new async session (use as async context manager)."""
        return self._session_factory()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def save(self, record: SQLModel) -> bool:
        """Insert or update an entity."""
        data = record.model_dump()
        model = type(record)

        # Filter out computed fields
        model_fields = model.model_fields
        computed_fields = set()
        for field_name in data:
            if field_name not in model_fields:
                attr = getattr(model, field_name, None)
                if attr and isinstance(attr, property) and not attr.fset:
                    computed_fields.add(field_name)
        data = {k: v for k, v in data.items() if k not in computed_fields}

        async with self._session_factory() as session:
            async with session.begin():
                if "id" in data:
                    db_record = await session.get(model, data["id"])
                    if db_record:
                        for key, value in data.items():
                            setattr(db_record, key, value)
                    else:
                        db_record = model(**data)
                else:
                    db_record = model(**data)

                session.add(db_record)

            # Refresh outside the transaction to get generated values
            await session.refresh(db_record)
            for key, value in db_record.model_dump().items():
                if key not in computed_fields:
                    setattr(record, key, value)

        return True

    async def get(self, model: Type[SQLModel], entity_id: Any) -> Optional[SQLModel]:
        """Get an entity by ID."""
        return await self.find(model, entity_id)

    async def find(self, model: Type[SQLModel], entity_id: Any) -> Optional[SQLModel]:
        """Find an entity by ID with eager-loaded relationships."""
        async with self._session_factory() as session:
            # Build query with eager loading
            stmt = select(model).where(model.id == entity_id)

            for attr_name in dir(model):
                if not attr_name.startswith("_"):
                    attr = getattr(model, attr_name, None)
                    if hasattr(attr, "property") and hasattr(attr.property, "mapper"):
                        stmt = stmt.options(selectinload(attr))

            result = await session.execute(stmt)
            row = result.scalars().first()

            if row is None:
                row = await session.get(model, entity_id)

            return row

    async def find_by(
        self, model: Type[SQLModel], **kwargs
    ) -> Optional[SQLModel]:
        """Find first entity matching keyword filters."""
        async with self._session_factory() as session:
            query = select(model)
            for key, value in kwargs.items():
                query = query.where(getattr(model, key) == value)
            result = await session.execute(query)
            return result.scalars().first()

    async def delete(self, record: SQLModel) -> bool:
        """Delete an entity."""
        async with self._session_factory() as session:
            async with session.begin():
                db_record = await session.get(type(record), record.id)
                if db_record:
                    await session.delete(db_record)
                    return True
                return False

    async def exists(self, model: Type[SQLModel], entity_id: Any) -> bool:
        """Check if an entity exists by ID."""
        async with self._session_factory() as session:
            result = await session.get(model, entity_id)
            return result is not None

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def all(self, model: Type[SQLModel]) -> List[SQLModel]:
        """Get all entities of a model type."""
        async with self._session_factory() as session:
            result = await session.execute(select(model))
            return list(result.scalars().all())

    async def count(self, model: Type[SQLModel]) -> int:
        """Count all entities of a model type."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count()).select_from(model)
            )
            return result.scalar_one()

    async def where(
        self,
        model: Type[SQLModel],
        *expressions: Any,
        order_by: Optional[Any] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[SQLModel]:
        """Query entities with SQLAlchemy expressions."""
        async with self._session_factory() as session:
            query = select(model).where(*expressions)
            if order_by is not None:
                if isinstance(order_by, str):
                    order_by = getattr(model, order_by)
                query = query.order_by(order_by)
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def filter(
        self,
        model: Type[SQLModel],
        sorting_field: Optional[str] = None,
        sort_direction: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        as_dict: bool = False,
        fields: Optional[List[str]] = None,
        exact_match: bool = True,
        **kwargs,
    ) -> List[Any]:
        """Filter entities by keyword arguments with sorting and pagination."""
        async with self._session_factory() as session:
            invalid_fields = [
                f for f in kwargs if f not in model.model_fields
            ]
            if invalid_fields:
                raise ValueError(
                    f"Invalid fields for filtering: {', '.join(invalid_fields)}"
                )

            if fields:
                query = select(*[getattr(model, f) for f in fields])
            else:
                query = select(model)

            for field, value in kwargs.items():
                if value is None:
                    query = query.filter(getattr(model, field).is_(None))
                    continue

                field_type = model.model_fields[field].annotation
                if get_origin(field_type) is Union:
                    field_type = next(
                        (t for t in get_args(field_type) if t is not type(None)),
                        str,
                    )

                if not exact_match and isinstance(value, str):
                    query = query.filter(
                        getattr(model, field).ilike(f"%{value}%")
                    )
                elif isinstance(value, (list, tuple)):
                    query = query.filter(getattr(model, field).in_(value))
                elif field_type is UUID and isinstance(value, str):
                    try:
                        value = UUID(value)
                    except ValueError:
                        raise ValueError(
                            f"Invalid UUID format for field {field}: {value}"
                        )
                    query = query.filter(getattr(model, field) == value)
                elif (
                    field_type in (datetime, date)
                    and isinstance(value, (list, tuple))
                    and len(value) == 2
                ):
                    query = query.filter(
                        getattr(model, field).between(value[0], value[1])
                    )
                elif not exact_match and field_type is str:
                    query = query.filter(
                        getattr(model, field).ilike(f"%{value}%")
                    )
                else:
                    query = query.filter(getattr(model, field) == value)

            if sorting_field:
                if sorting_field not in model.model_fields:
                    raise ValueError(
                        f"Sorting field '{sorting_field}' does not exist."
                    )
                order_field = getattr(model, sorting_field)
                query = query.order_by(
                    order_field.desc()
                    if sort_direction.lower() == "desc"
                    else order_field
                )
            else:
                query = query.order_by(model.id)

            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            result = await session.execute(query)
            rows = list(result.scalars().all())

            if as_dict:
                return [r.model_dump() for r in rows]
            return rows

    async def search(
        self,
        model: Type[SQLModel],
        search_value: Optional[str] = None,
        sorting_field: Optional[str] = None,
        sort_direction: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        as_dict: bool = False,
        fields: Optional[List[str]] = None,
    ) -> List[Any]:
        """Full-text search across string fields."""
        async with self._session_factory() as session:
            if fields:
                query = select(*[getattr(model, f) for f in fields])
            else:
                query = select(model)

            if search_value:
                string_fields = [
                    k for k, v in model.model_fields.items() if v.annotation is str
                ]
                if string_fields:
                    conditions = [
                        getattr(model, f).ilike(f"%{search_value}%")
                        for f in string_fields
                    ]
                    query = query.filter(or_(*conditions))

            if sorting_field:
                if sorting_field not in model.model_fields:
                    raise ValueError(
                        f"Sorting field '{sorting_field}' does not exist."
                    )
                order_field = getattr(model, sorting_field)
                query = query.order_by(
                    order_field.desc()
                    if sort_direction.lower() == "desc"
                    else order_field
                )
            else:
                query = query.order_by(model.id)

            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            result = await session.execute(query)
            rows = list(result.scalars().all())

            if as_dict:
                return [r.model_dump() for r in rows]
            return rows

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    async def bulk_create(
        self, model: Type[SQLModel], data: List[Dict[str, Any]]
    ) -> List[SQLModel]:
        """Create multiple entities in a single transaction."""
        async with self._session_factory() as session:
            async with session.begin():
                records = [model(**item) for item in data]
                session.add_all(records)
            for record in records:
                await session.refresh(record)
            return records

    async def bulk_upsert(
        self, model: Type[SQLModel], data: List[Dict[str, Any]]
    ) -> List[SQLModel]:
        """Update existing or insert new entities."""
        async with self._session_factory() as session:
            async with session.begin():
                records = []
                for item in data:
                    if "id" in item:
                        record = await session.get(model, item["id"])
                        if record:
                            for key, value in item.items():
                                setattr(record, key, value)
                            records.append(record)
                session.add_all(records)
            for record in records:
                await session.refresh(record)
            return records

    async def delete_where(
        self, model: Type[SQLModel], *expressions
    ) -> int:
        """Delete records matching expressions. Returns count deleted."""
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(model).where(*expressions)
                )
                rows = list(result.scalars().all())
                count = len(rows)
                for record in rows:
                    await session.delete(record)
            return count

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(
        self, model: Type[SQLModel], entity_id: Any, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an entity by ID with a data dict."""
        async with self._session_factory() as session:
            async with session.begin():
                record = await session.get(model, entity_id)
                if not record:
                    raise Exception(f"Record with id {entity_id} not found")
                for key, value in data.items():
                    setattr(record, key, value)
                session.add(record)
            await session.refresh(record)
            return record.model_dump()

    # ------------------------------------------------------------------
    # Schema introspection
    # ------------------------------------------------------------------

    async def schema(self) -> str:
        """Return a text description of all tables."""
        async with self._engine.connect() as conn:
            def _inspect(sync_conn):
                inspector = sa.inspect(sync_conn)
                res = ""
                for table_name in inspector.get_table_names():
                    res += f"Table: {table_name}\n"
                    pk_cols = inspector.get_pk_constraint(table_name)[
                        "constrained_columns"
                    ]
                    for column in inspector.get_columns(table_name):
                        pk = "*" if column["name"] in pk_cols else "-"
                        res += f"  {pk} {column['name']}: {column['type']}\n"
                return res

            return await conn.run_sync(_inspect)

    # ------------------------------------------------------------------
    # Flush
    # ------------------------------------------------------------------

    async def flush(self, model_class: Optional[Type[SQLModel]] = None) -> None:
        """Delete all records of a model, or all records if no model given."""
        async with self._session_factory() as session:
            async with session.begin():
                if model_class:
                    result = await session.execute(select(model_class))
                    for record in result.scalars().all():
                        await session.delete(record)
                else:
                    # Delete from all mapped tables
                    for table in reversed(SQLModel.metadata.sorted_tables):
                        await session.execute(table.delete())
