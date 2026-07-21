from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import AuthorizationException, ResourceNotFoundException
from src.core.logger import get_logger
from src.domain.khan_academy.crud import (
    ka_student_activity_crud,
    ka_subject_activity_crud,
    ka_subject_progress_crud,
    ka_topic_progress_crud,
    topic_crud,
)
from src.domain.khan_academy.models import (
    KaStudentActivity,
    KaSubjectActivity,
    KaSubjectProgress,
    KaTopicProgress,
    Topic,
)
from src.domain.users.models import StudentProfile, User

logger = get_logger(__name__)


class TopicService:
    """Full CRUD for the Topic catalog. Admin/Teacher manage; anyone
    authenticated can browse (matches how Subject/ClassRoom-level catalog
    data is treated elsewhere in this project -- no legacy precedent exists
    for this table since it's new, so this follows the closest analogous
    pattern: study material's "staff creates, everyone reads" shape).
    """

    @staticmethod
    async def create_topic(db: AsyncSession, data: dict) -> Topic:
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
    async def get_topic(db: AsyncSession, topic_id: int) -> Topic:
        topic = await topic_crud.get(db, topic_id)
        if not topic:
            raise ResourceNotFoundException("Topic not found")
        return topic

    @staticmethod
    async def update_topic(db: AsyncSession, topic_id: int, data: dict) -> Topic:
        await TopicService.get_topic(db, topic_id)
        return await topic_crud.update(db, topic_id, data)

    @staticmethod
    async def delete_topic(db: AsyncSession, topic_id: int) -> None:
        await TopicService.get_topic(db, topic_id)
        await topic_crud.update(db, topic_id, {"is_active": False})


class KaProgressService:
    """KA subject/topic progress snapshots.

    These tables are meant to be populated by a Khan Academy API sync job
    (not written by end users), so `ingest_*` here is a thin upsert intended
    for that job to call -- there's no legacy sync job to port (KA
    integration is new to this project), so the actual KA API polling logic
    itself is out of scope; this is the data-landing contract for it.
    """

    @staticmethod
    async def ingest_subject_progress(
        db: AsyncSession,
        data: dict,
    ) -> KaSubjectProgress:
        existing = await db.scalar(
            select(KaSubjectProgress).filter_by(
                student_profile_id=data["student_profile_id"],
                subject_id=data.get("subject_id"),
                snapshot_date=data["snapshot_date"],
            ),
        )
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            await db.flush()
            return existing
        return await ka_subject_progress_crud.create(db, data)

    @staticmethod
    async def ingest_topic_progress(db: AsyncSession, data: dict) -> KaTopicProgress:
        existing = await db.scalar(
            select(KaTopicProgress).filter_by(
                student_profile_id=data["student_profile_id"],
                topic_id=data.get("topic_id"),
                snapshot_date=data["snapshot_date"],
            ),
        )
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            await db.flush()
            return existing
        return await ka_topic_progress_crud.create(db, data)

    @staticmethod
    async def get_student_progress_summary(
        db: AsyncSession,
        student_profile_id: int,
        current_user: User,
    ) -> dict:
        if current_user.role == UserRole.STUDENT:
            own_profile = await db.scalar(
                select(StudentProfile).filter_by(user_id=current_user.id),
            )
            if not own_profile or own_profile.id != student_profile_id:
                raise AuthorizationException("You can only view your own progress")

        subject_result = await db.execute(
            select(KaSubjectProgress)
            .filter_by(student_profile_id=student_profile_id)
            .order_by(KaSubjectProgress.snapshot_date.desc()),
        )
        topic_result = await db.execute(
            select(KaTopicProgress)
            .filter_by(student_profile_id=student_profile_id)
            .order_by(KaTopicProgress.snapshot_date.desc()),
        )

        return {
            "student_profile_id": student_profile_id,
            "subject_progress": list(subject_result.scalars().all()),
            "topic_progress": list(topic_result.scalars().all()),
        }

    # ------------------------------------------------------------------
    # KaStudentActivity / KaSubjectActivity -- were completely missing
    # (models + crud singletons existed, nothing else did). Same sync-job
    # landing-point contract and same student-can-only-view-own-data rule
    # as the progress snapshots above.
    # ------------------------------------------------------------------

    @staticmethod
    async def ingest_student_activity(
        db: AsyncSession,
        data: dict,
    ) -> KaStudentActivity:
        existing = await db.scalar(
            select(KaStudentActivity).filter_by(
                student_profile_id=data["student_profile_id"],
                from_date=data["from_date"],
                to_date=data["to_date"],
            ),
        )
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            await db.flush()
            return existing
        return await ka_student_activity_crud.create(db, data)

    @staticmethod
    async def ingest_subject_activity(
        db: AsyncSession,
        data: dict,
    ) -> KaSubjectActivity:
        # No natural upsert key here (unlike the snapshot tables) -- a
        # student can log multiple distinct activities against the same
        # subject/topic on the same date, so every ingest is a new row.
        return await ka_subject_activity_crud.create(db, data)

    @staticmethod
    async def get_student_activities(
        db: AsyncSession,
        student_profile_id: int,
        current_user: User,
    ) -> dict:
        if current_user.role == UserRole.STUDENT:
            own_profile = await db.scalar(
                select(StudentProfile).filter_by(user_id=current_user.id),
            )
            if not own_profile or own_profile.id != student_profile_id:
                raise AuthorizationException("You can only view your own activity")

        student_result = await db.execute(
            select(KaStudentActivity)
            .filter_by(student_profile_id=student_profile_id)
            .order_by(KaStudentActivity.from_date.desc()),
        )
        subject_result = await db.execute(
            select(KaSubjectActivity)
            .filter_by(student_profile_id=student_profile_id)
            .order_by(KaSubjectActivity.activity_date.desc()),
        )

        return {
            "student_profile_id": student_profile_id,
            "student_activity": list(student_result.scalars().all()),
            "subject_activity": list(subject_result.scalars().all()),
        }
