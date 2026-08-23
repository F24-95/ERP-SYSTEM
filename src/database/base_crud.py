from collections.abc import Sequence
from datetime import datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import func, inspect, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import BusinessLogicException, ResourceNotFoundException
from src.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class AsyncBaseCRUD(Generic[T]):
    """Generic asynchronous CRUD base class for SQLAlchemy 2.0."""

    def __init__(self, model: type[T]):
        self.model = model

    def _valid_columns(self) -> set[str]:
        """Return the set of mapped column names for a model."""
        return {col.key for col in inspect(self.model).mapper.column_attrs}

    def _apply_fields(self, obj: Any, data: dict[str, Any], valid: set[str]) -> None:
        unknown = set(data) - valid
        if unknown:
            raise BusinessLogicException(
                f"Unknown field(s) for {self.model.__name__}: {sorted(unknown)}",
            )
        for key, value in data.items():
            setattr(obj, key, value)

    async def get(self, session: AsyncSession, id: Any) -> T | None:
        """Fetch by primary key."""
        return await session.get(self.model, id)

    async def get_or_raise(self, session: AsyncSession, id: Any) -> T:
        """Fetch by primary key or raise ResourceNotFoundException."""
        obj = await self.get(session, id)
        if obj is None:
            raise ResourceNotFoundException(
                f"{self.model.__name__} with id={id} not found.",
            )
        return obj

    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[T], int]:
        """Paginated list with optional exact-match filters and total count."""
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        if filters:
            query = query.filter_by(**filters)
            count_query = count_query.filter_by(**filters)

        total = await session.scalar(count_query)

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        items = list(result.scalars().all())

        return items, total or 0

    async def create(self, session: AsyncSession, data: dict[str, Any]) -> T:
        """Insert a new record."""
        valid = self._valid_columns()
        unknown = set(data) - valid
        if unknown:
            raise BusinessLogicException(f"Unknown field(s): {sorted(unknown)}")

        try:
            obj = self.model(**data)
            session.add(obj)
            await session.flush()
            await session.refresh(obj)
            logger.debug(f"Created {self.model.__name__}")
            return obj
        except IntegrityError as exc:
            await session.rollback()
            logger.warning(f"IntegrityError creating {self.model.__name__}: {exc.orig}")
            raise BusinessLogicException(
                "Database integrity constraint violated",
                details={"error": str(exc.orig)},
            )
        except Exception:
            await session.rollback()
            logger.exception(f"Unexpected error creating {self.model.__name__}")
            raise

    async def update(self, session: AsyncSession, id: Any, data: dict[str, Any]) -> T:
        """Partially update by primary key."""
        obj = await self.get_or_raise(session, id)
        try:
            self._apply_fields(obj, data, self._valid_columns())
            await session.flush()
            await session.refresh(obj)
            logger.debug(f"Updated {self.model.__name__} id={id}")
            return obj
        except IntegrityError as exc:
            await session.rollback()
            raise BusinessLogicException(
                "Database integrity constraint violated during update",
                details={"error": str(exc.orig)},
            )
        except Exception:
            await session.rollback()
            logger.exception(f"Unexpected error updating {self.model.__name__} id={id}")
            raise

    async def delete(self, session: AsyncSession, id: Any) -> bool:
        """Hard delete by primary key."""
        obj = await self.get(session, id)
        if obj is None:
            return False

        await session.delete(obj)
        await session.flush()
        logger.debug(f"Deleted {self.model.__name__} id={id}")
        return True

    async def soft_delete(
        self,
        session: AsyncSession,
        id: Any,
        deleted_by: int,
    ) -> bool:
        """Soft delete a record (requires SoftDeleteMixin on the model).
        Sets is_deleted = True and deleted_by = deleted_by.
        """
        if not hasattr(self.model, "is_deleted"):
            raise BusinessLogicException(
                f"Model {self.model.__name__} does not support soft delete.",
            )

        obj = await self.get_or_raise(session, id)

        try:
            # Assuming SoftDeleteMixin has these fields
            obj.is_deleted = True
            if hasattr(self.model, "deleted_by"):
                obj.deleted_by = deleted_by

            from datetime import datetime

            if hasattr(self.model, "deleted_at"):
                obj.deleted_at = datetime.utcnow()

            await session.flush()
            await session.refresh(obj)
            logger.debug(f"Soft-deleted {self.model.__name__} id={id}")
            return True
        except Exception:
            await session.rollback()
            raise

    async def restore(self, session: AsyncSession, id: Any) -> T:
        """Undo a soft delete (requires SoftDeleteMixin on the model)."""
        if not hasattr(self.model, "is_deleted"):
            raise BusinessLogicException(
                f"Model {self.model.__name__} does not support soft delete.",
            )

        obj = await self.get_or_raise(session, id)
        obj.is_deleted = False
        if hasattr(self.model, "deleted_by"):
            obj.deleted_by = None
        if hasattr(self.model, "deleted_at"):
            obj.deleted_at = None
        await session.flush()
        await session.refresh(obj)
        logger.debug(f"Restored {self.model.__name__} id={id}")
        return obj

    async def get_by(self, session: AsyncSession, **filters: Any) -> T | None:
        """Fetch a single record matching exact-match filters, or None."""
        query = select(self.model).filter_by(**filters)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_by_filters(self, session: AsyncSession, **filters: Any) -> list[T]:
        """Fetch all records matching exact-match filters.
        Alias kept for call sites migrated from the legacy repository API
        (`BaseRepository.get_multi_by_field` equivalent).
        """
        return await self.get_many(session, filters=filters)

    async def get_many(
        self,
        session: AsyncSession,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_desc: bool = True,
        limit: int | None = None,
    ) -> list[T]:
        """Fetch all records matching exact-match filters, with optional ordering/limit."""
        query = select(self.model)
        if filters:
            query = query.filter_by(**filters)
        if order_by and hasattr(self.model, order_by):
            field = getattr(self.model, order_by)
            query = query.order_by(field.desc() if order_desc else field.asc())
        if limit is not None:
            query = query.limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def exists(self, session: AsyncSession, **filters: Any) -> bool:
        """Check whether at least one record matches the given filters."""
        query = select(func.count()).select_from(self.model).filter_by(**filters)
        total = await session.scalar(query)
        return bool(total and total > 0)

    async def paginate(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_desc: bool = True,
    ) -> dict[str, Any]:
        """Page-number based pagination (mirrors the legacy `get_paginated` contract)."""
        page = max(page, 1)
        skip = (page - 1) * page_size
        items, total = await self.get_all(
            session,
            skip=skip,
            limit=page_size,
            filters=filters,
        )
        if order_by and hasattr(self.model, order_by):
            items = await self.get_many(
                session,
                filters=filters,
                order_by=order_by,
                order_desc=order_desc,
                limit=page_size,
            )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }

    async def search(
        self,
        session: AsyncSession,
        term: str,
        fields: Sequence[str],
        skip: int = 0,
        limit: int = 100,
    ) -> list[T]:
        """Simple case-insensitive substring search across the given text columns.
        For anything beyond this (ranking, fuzzy match, weighting) use the
        dedicated search domain (ported from the legacy `helpers/search/*`
        engine) rather than extending this generic method.
        """
        valid = self._valid_columns()
        unknown = set(fields) - valid
        if unknown:
            raise BusinessLogicException(
                f"Unknown search field(s) for {self.model.__name__}: {sorted(unknown)}",
            )

        like_term = f"%{term}%"
        conditions = [getattr(self.model, f).ilike(like_term) for f in fields]
        query = select(self.model).where(or_(*conditions)).offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def bulk_create(
        self,
        session: AsyncSession,
        items: list[dict[str, Any]],
    ) -> list[T]:
        """Create multiple records in one flush."""
        valid = self._valid_columns()
        for item in items:
            unknown = set(item) - valid
            if unknown:
                raise BusinessLogicException(
                    f"Unknown field(s) for {self.model.__name__}: {sorted(unknown)}",
                )
        try:
            objs = [self.model(**item) for item in items]
            session.add_all(objs)
            await session.flush()
            logger.debug(f"Bulk created {len(objs)} {self.model.__name__}")
            return objs
        except IntegrityError as exc:
            await session.rollback()
            raise BusinessLogicException(
                "Database integrity constraint violated during bulk create",
                details={"error": str(exc.orig)},
            )

    async def bulk_update(
        self,
        session: AsyncSession,
        updates: list[dict[str, Any]],
        id_field: str = "id",
    ) -> int:
        """Update multiple records. Each dict in `updates` must contain the
        primary-key value under `id_field` plus the fields to change.
        Returns the number of rows matched.
        """
        valid = self._valid_columns()
        count = 0
        for item in updates:
            item = dict(item)
            pk = item.pop(id_field, None)
            if pk is None:
                raise BusinessLogicException(
                    f"bulk_update: each item requires '{id_field}'",
                )
            unknown = set(item) - valid
            if unknown:
                raise BusinessLogicException(
                    f"Unknown field(s) for {self.model.__name__}: {sorted(unknown)}",
                )
            stmt = (
                update(self.model)
                .where(getattr(self.model, id_field) == pk)
                .values(**item)
            )
            result = await session.execute(stmt)
            count += result.rowcount or 0
        await session.flush()
        logger.debug(f"Bulk updated {count} {self.model.__name__}")
        return count

    async def bulk_delete(
        self,
        session: AsyncSession,
        ids: list[Any],
        soft_delete: bool = True,
    ) -> int:
        """Delete multiple records by primary key, soft by default when supported."""
        if soft_delete and hasattr(self.model, "is_deleted"):
            stmt = (
                update(self.model)
                .where(self.model.id.in_(ids))
                .values(is_deleted=True, deleted_at=datetime.utcnow())
            )
            result = await session.execute(stmt)
        else:
            from sqlalchemy import delete as sa_delete

            stmt = sa_delete(self.model).where(self.model.id.in_(ids))
            result = await session.execute(stmt)
        await session.flush()
        count = result.rowcount or 0
        logger.debug(f"Bulk deleted {count} {self.model.__name__}")
        return count

    async def first_or_create(
        self,
        session: AsyncSession,
        defaults: dict[str, Any] | None = None,
        **filters: Any,
    ) -> tuple[T, bool]:
        """Return (instance, created) — fetch by filters, or create with filters+defaults merged in."""
        existing = await self.get_by(session, **filters)
        if existing:
            return existing, False
        data = {**filters, **(defaults or {})}
        created = await self.create(session, data)
        return created, True

    async def upsert(
        self,
        session: AsyncSession,
        match_fields: dict[str, Any],
        data: dict[str, Any],
    ) -> T:
        """Update the record matching `match_fields` if it exists, else create it with match_fields+data merged."""
        existing = await self.get_by(session, **match_fields)
        if existing:
            self._apply_fields(existing, data, self._valid_columns())
            await session.flush()
            await session.refresh(existing)
            return existing
        return await self.create(session, {**match_fields, **data})

    async def with_relations(
        self,
        session: AsyncSession,
        id: Any,
        relations: Sequence[str],
    ) -> T | None:
        """Fetch a record by primary key with the given relationship attributes eagerly loaded."""
        query = select(self.model).where(self.model.id == id)
        for rel in relations:
            if not hasattr(self.model, rel):
                raise BusinessLogicException(
                    f"Unknown relation '{rel}' on {self.model.__name__}",
                )
            query = query.options(selectinload(getattr(self.model, rel)))
        result = await session.execute(query)
        return result.scalars().first()
