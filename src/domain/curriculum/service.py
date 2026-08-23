from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ResourceNotFoundException
from src.core.logger import get_logger
from src.domain.curriculum.crud import subject_crud, topic_crud
from src.domain.curriculum.models import Subject, Topic
from src.domain.curriculum.schemas import SubjectCreate, SubjectUpdate

logger = get_logger(__name__)


class SubjectService:
    @staticmethod
    async def create(
        db: AsyncSession,
        data: SubjectCreate,
    ) -> Subject:
        return await subject_crud.create(db, data.model_dump())

    @staticmethod
    async def list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Subject], int]:
        return await subject_crud.get_all(db, skip=skip, limit=limit)

    @staticmethod
    async def get(
        db: AsyncSession,
        subject_id: int,
    ) -> Subject:
        return await subject_crud.get_or_raise(db, subject_id)

    @staticmethod
    async def update(
        db: AsyncSession,
        subject_id: int,
        data: SubjectUpdate,
    ) -> Subject:
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return await subject_crud.get_or_raise(db, subject_id)
        return await subject_crud.update(db, subject_id, payload)

    @staticmethod
    async def deactivate(
        db: AsyncSession,
        subject_id: int,
    ) -> None:
        await subject_crud.get_or_raise(db, subject_id)
        await subject_crud.update(db, subject_id, {"is_active": False})
        logger.info(f"Subject deactivated: id={subject_id}")


class TopicService:
    @staticmethod
    async def create_topic(
        db: AsyncSession,
        data: dict,
    ) -> Topic:
        return await topic_crud.create(db, data)

    @staticmethod
    async def list_topics(
        db: AsyncSession,
        subject_id: int = None,
        classroom_id: int = None,
    ) -> list[Topic]:
        query = select(Topic).filter(Topic.is_active == True)  # noqa: E712
        if subject_id is not None:
            query = query.filter(Topic.subject_id == subject_id)
        if classroom_id is not None:
            query = query.filter(Topic.classroom_id == classroom_id)
        query = query.order_by(Topic.display_order.asc())
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_topic(
        db: AsyncSession,
        topic_id: int,
    ) -> Topic:
        topic = await topic_crud.get(db, topic_id)
        if not topic:
            raise ResourceNotFoundException("Topic not found")
        return topic

    @staticmethod
    async def update_topic(
        db: AsyncSession,
        topic_id: int,
        data: dict,
    ) -> Topic:
        await TopicService.get_topic(db, topic_id)
        return await topic_crud.update(db, topic_id, data)

    @staticmethod
    async def delete_topic(
        db: AsyncSession,
        topic_id: int,
    ) -> None:
        await TopicService.get_topic(db, topic_id)
        await topic_crud.update(db, topic_id, {"is_active": False})
