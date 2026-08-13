from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BusinessLogicException
from src.core.logger import get_logger
from src.domain.academics.crud import (
    academic_session_crud,
    class_subject_crud,
    classroom_crud,
)
from src.domain.curriculum.crud import subject_crud
from src.domain.academics.models import AcademicSession, ClassRoom, ClassSubject
from src.domain.academics.schemas import (
    AcademicSessionCreate,
    AcademicSessionUpdate,
    ClassRoomCreate,
    ClassRoomUpdate,
    ClassSubjectCreate,
    ClassSubjectUpdate,
)

logger = get_logger(__name__)


class AcademicSessionService:
    @staticmethod
    async def _ensure_single_current(
        db: AsyncSession,
        exclude_id: int | None = None,
    ) -> None:
        from sqlalchemy import update as sa_update

        from src.domain.academics.models import AcademicSession

        stmt = (
            sa_update(AcademicSession)
            .where(AcademicSession.is_current.is_(True))
            .values(is_current=False)
        )
        if exclude_id is not None:
            stmt = stmt.where(AcademicSession.id != exclude_id)
        await db.execute(stmt)

    @staticmethod
    async def create(db: AsyncSession, data: AcademicSessionCreate) -> AcademicSession:
        payload = data.model_dump()
        if payload.get("is_current"):
            await AcademicSessionService._ensure_single_current(db)
        return await academic_session_crud.create(db, payload)

    @staticmethod
    async def list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[AcademicSession], int]:
        return await academic_session_crud.get_all(db, skip=skip, limit=limit)

    @staticmethod
    async def get(db: AsyncSession, session_id: int) -> AcademicSession:
        return await academic_session_crud.get_or_raise(db, session_id)

    @staticmethod
    async def update(
        db: AsyncSession,
        session_id: int,
        data: AcademicSessionUpdate,
    ) -> AcademicSession:
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return await academic_session_crud.get_or_raise(db, session_id)
        if payload.get("is_current"):
            await AcademicSessionService._ensure_single_current(db, exclude_id=session_id)
        return await academic_session_crud.update(db, session_id, payload)

    @staticmethod
    async def deactivate(db: AsyncSession, session_id: int) -> None:
        """Reference data is deactivated (is_active=False), not hard-deleted --
        AcademicSession is RESTRICT-referenced by ClassRoom and CASCADE by
        ClassSubject, so a hard delete would either fail loudly or silently
        cascade-wipe classrooms depending on which FK fires first. Same
        convention as ExamService.delete_exam / AssignmentService.delete_assignment.
        """
        await academic_session_crud.get_or_raise(db, session_id)
        await academic_session_crud.update(db, session_id, {"is_active": False})
        logger.info(f"AcademicSession deactivated: id={session_id}")


class ClassRoomService:
    @staticmethod
    async def create(db: AsyncSession, data: ClassRoomCreate) -> ClassRoom:
        await academic_session_crud.get_or_raise(db, data.academic_sessions_id)
        return await classroom_crud.create(db, data.model_dump())

    @staticmethod
    async def list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        academic_sessions_id: int | None = None,
    ) -> tuple[list[ClassRoom], int]:
        filters = (
            {"academic_sessions_id": academic_sessions_id}
            if academic_sessions_id
            else None
        )
        return await classroom_crud.get_all(db, skip=skip, limit=limit, filters=filters)

    @staticmethod
    async def get(db: AsyncSession, classroom_id: int) -> ClassRoom:
        return await classroom_crud.get_or_raise(db, classroom_id)

    @staticmethod
    async def update(
        db: AsyncSession,
        classroom_id: int,
        data: ClassRoomUpdate,
    ) -> ClassRoom:
        payload = data.model_dump(exclude_unset=True)
        if "academic_sessions_id" in payload:
            await academic_session_crud.get_or_raise(
                db,
                payload["academic_sessions_id"],
            )
        if not payload:
            return await classroom_crud.get_or_raise(db, classroom_id)
        return await classroom_crud.update(db, classroom_id, payload)

    @staticmethod
    async def deactivate(db: AsyncSession, classroom_id: int) -> None:
        await classroom_crud.get_or_raise(db, classroom_id)
        await classroom_crud.update(db, classroom_id, {"is_active": False})
        logger.info(f"ClassRoom deactivated: id={classroom_id}")


class ClassSubjectService:
    """Was entirely missing (no schemas.py entries, no crud instance, no
    service, no router) despite ClassSubject being a required foreign key
    for TeacherSubject and StudyMaterial. Without this, teachers could
    never be assigned to a classroom+subject and study material could
    never be uploaded -- both endpoints require a valid class_subject_id
    that nothing could ever create.
    """

    @staticmethod
    async def create(db: AsyncSession, data: ClassSubjectCreate) -> ClassSubject:
        await academic_session_crud.get_or_raise(db, data.academic_sessions_id)
        await classroom_crud.get_or_raise(db, data.classroom_id)
        await subject_crud.get_or_raise(db, data.subject_id)

        existing = await class_subject_crud.get_by(
            db,
            academic_sessions_id=data.academic_sessions_id,
            classroom_id=data.classroom_id,
            subject_id=data.subject_id,
        )
        if existing:
            raise BusinessLogicException(
                "This subject is already mapped to this classroom for this academic session",
            )
        return await class_subject_crud.create(db, data.model_dump())

    @staticmethod
    async def list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        classroom_id: int | None = None,
        academic_sessions_id: int | None = None,
    ) -> tuple[list[ClassSubject], int]:
        filters = {}
        if classroom_id:
            filters["classroom_id"] = classroom_id
        if academic_sessions_id:
            filters["academic_sessions_id"] = academic_sessions_id
        return await class_subject_crud.get_all(
            db,
            skip=skip,
            limit=limit,
            filters=filters or None,
        )

    @staticmethod
    async def get(db: AsyncSession, class_subject_id: int) -> ClassSubject:
        return await class_subject_crud.get_or_raise(db, class_subject_id)

    @staticmethod
    async def update(
        db: AsyncSession,
        class_subject_id: int,
        data: ClassSubjectUpdate,
    ) -> ClassSubject:
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return await class_subject_crud.get_or_raise(db, class_subject_id)
        return await class_subject_crud.update(db, class_subject_id, payload)

    @staticmethod
    async def deactivate(db: AsyncSession, class_subject_id: int) -> None:
        """NOTE: TeacherSubject.class_subject_id is ondelete=CASCADE, so a
        hard delete here would silently wipe teacher assignments. Deactivate
        only; the DB row (and any teacher assignments pointing at it) stays
        intact for historical/audit purposes.
        """
        await class_subject_crud.get_or_raise(db, class_subject_id)
        await class_subject_crud.update(db, class_subject_id, {"is_active": False})
        logger.info(f"ClassSubject deactivated: id={class_subject_id}")
