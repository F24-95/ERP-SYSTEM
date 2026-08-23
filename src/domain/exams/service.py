from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import (
    AuthorizationException,
    ResourceNotFoundException,
)
from src.core.logger import get_logger
from src.domain.exams.crud import exam_crud, exam_result_crud
from src.domain.exams.models import Exam, ExamResult
from src.domain.exams.schemas import ExamCreate, ExamResultCreate, ExamUpdate
from src.domain.operations.models import StudentClass, TeacherSubject
from src.domain.users.models import TeacherProfile, User

logger = get_logger(__name__)


class ExamService:

    @staticmethod
    async def _get_exam_or_raise(
        db: AsyncSession,
        exam_id: int,
    ) -> Exam:
        exam = await exam_crud.get(db, exam_id)
        if not exam:
            raise ResourceNotFoundException(
                f"Exam with id={exam_id} not found",
            )
        return exam

    @staticmethod
    def _check_ownership(exam: Exam, current_user: User) -> None:
        """Only the exam's creator or an admin may modify it — same rule as
        the legacy router's inline `exam.created_by != current_user.id and
        current_user.role != UserRole.ADMIN` check.
        """
        if (
            exam.created_by != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            raise AuthorizationException("You can only modify your own exams")

    @staticmethod
    async def create_exam(
        db: AsyncSession,
        exam_data: ExamCreate,
        current_user: User,
    ) -> Exam:
        teacher = await db.scalar(
            select(TeacherProfile).filter_by(user_id=current_user.id),
        )
        if not teacher:
            raise ResourceNotFoundException("Teacher profile not found")

        # Verify teacher is assigned to this subject (legacy: TeacherSubject.teacher_id ==
        # teacher.teacher_id business-ID lookup; the new schema FKs TeacherSubject.teacher_id
        # directly to users.id, so the equivalent check compares against current_user.id).
        teacher_subject = await db.scalar(
            select(TeacherSubject).filter_by(
                id=exam_data.teacher_subject_id,
                teacher_id=current_user.id,
            ),
        )
        if not teacher_subject:
            raise AuthorizationException("You are not assigned to this class")

        exam = await exam_crud.create(
            db,
            {**exam_data.model_dump(), "created_by": current_user.id},
        )
        logger.info(
            f"Exam created: {exam.exam_id} by user={current_user.id}",
        )
        return exam

    @staticmethod
    async def get_exams(
        db: AsyncSession,
        current_user: User,
        classroom_id: int | None = None,
        status: str | None = None,
    ) -> list[Exam]:
        query = select(Exam)
        if classroom_id:
            query = query.filter(Exam.classroom_id == classroom_id)
        if status:
            query = query.filter(Exam.status == status)

        # Teachers only see exams for subjects they're assigned to.
        if current_user.role == UserRole.TEACHER:
            ts_ids = select(TeacherSubject.id).filter_by(
                teacher_id=current_user.id,
            )
            query = query.filter(Exam.teacher_subject_id.in_(ts_ids))
        elif current_user.role == UserRole.STUDENT:
            # Was previously unfiltered for students -- any logged-in
            # student could see every class's exams, not just their own.
            classroom_ids = select(StudentClass.classroom_id).filter_by(
                student_id=current_user.id,
            )
            query = query.filter(Exam.classroom_id.in_(classroom_ids))

        query = query.order_by(Exam.exam_date.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_exam(db: AsyncSession, exam_id: int) -> Exam:
        return await ExamService._get_exam_or_raise(db, exam_id)

    @staticmethod
    async def update_exam(
        db: AsyncSession,
        exam_id: int,
        exam_data: ExamUpdate,
        current_user: User,
    ) -> Exam:
        exam = await ExamService._get_exam_or_raise(db, exam_id)
        ExamService._check_ownership(exam, current_user)

        updates = exam_data.model_dump(exclude_unset=True)
        updates["updated_by"] = current_user.id
        updated = await exam_crud.update(db, exam_id, updates)
        logger.info(
            f"Exam updated: {updated.exam_id} by user={current_user.id}",
        )
        return updated

    @staticmethod
    async def delete_exam(
        db: AsyncSession,
        exam_id: int,
        current_user: User,
    ) -> None:
        exam = await ExamService._get_exam_or_raise(db, exam_id)
        ExamService._check_ownership(exam, current_user)

        # Legacy behavior: soft delete via is_active flag, not the
        # SoftDeleteMixin's is_deleted (Exam only has ActiveMixin).
        await exam_crud.update(
            db,
            exam_id,
            {"is_active": False, "deleted_by": current_user.id},
        )
        logger.info(
            f"Exam deleted: {exam.exam_id} by user={current_user.id}",
        )

    @staticmethod
    async def upload_exam_results(
        db: AsyncSession,
        exam_id: int,
        results_data: list[ExamResultCreate],
        current_user: User,
    ) -> list[ExamResult]:
        exam = await ExamService._get_exam_or_raise(db, exam_id)
        ExamService._check_ownership(exam, current_user)

        uploaded = []
        for item in results_data:
            existing = await db.scalar(
                select(ExamResult).filter_by(
                    exam_id=exam_id,
                    student_class_id=item.student_class_id,
                ),
            )
            if existing:
                data = item.model_dump(exclude={"student_class_id"})
                data["checked_at"] = datetime.utcnow()
                data["checked_by"] = current_user.id
                updated = await exam_result_crud.update(
                    db, existing.id, data,
                )
                uploaded.append(updated)
            else:
                data = item.model_dump()
                data["exam_id"] = exam_id
                data["checked_at"] = datetime.utcnow()
                data["checked_by"] = current_user.id
                created = await exam_result_crud.create(db, data)
                uploaded.append(created)

        exam.result_uploaded = len(uploaded)
        await db.flush()
        logger.info(
            f"Uploaded {len(uploaded)} results for exam={exam.exam_id}",
        )
        return uploaded

    @staticmethod
    async def get_exam_results(
        db: AsyncSession,
        exam_id: int,
        current_user: User,
    ) -> list[ExamResult]:
        """Was returning the FULL class result list (marks, rank, remarks --
        for every student) to *any* authenticated caller regardless of role,
        via GET /exams/{exam_id}/results with only `get_current_user` on the
        route. A student could see every classmate's marks. Now scoped:
        admin sees everything; a teacher only if they own the exam; a
        student only their own result.
        """
        exam = await ExamService._get_exam_or_raise(db, exam_id)

        if current_user.role == UserRole.ADMIN:
            return await exam_result_crud.get_many(
                db,
                filters={"exam_id": exam_id},
                order_by="rank_in_class",
                order_desc=False,
            )

        if current_user.role == UserRole.TEACHER:
            ExamService._check_ownership(exam, current_user)
            return await exam_result_crud.get_many(
                db,
                filters={"exam_id": exam_id},
                order_by="rank_in_class",
                order_desc=False,
            )

        if current_user.role == UserRole.STUDENT:
            student_class_ids = (
                await db.scalars(
                    select(StudentClass.id).filter_by(
                        student_id=current_user.id,
                    ),
                )
            ).all()
            all_results = await exam_result_crud.get_many(
                db,
                filters={"exam_id": exam_id},
            )
            return [
                r for r in all_results
                if r.student_class_id in student_class_ids
            ]

        raise AuthorizationException("Permission denied")

    @staticmethod
    async def get_exam_result(
        db: AsyncSession,
        result_id: int,
        current_user: User,
    ) -> ExamResult:
        """Was missing entirely -- a specific student's result could only
        ever be fetched as part of the full list, never on its own.
        """
        result = await exam_result_crud.get(db, result_id)
        if not result:
            raise ResourceNotFoundException(
                f"Exam result with id={result_id} not found",
            )

        exam = await ExamService._get_exam_or_raise(db, result.exam_id)
        if current_user.role == UserRole.ADMIN:
            return result
        if current_user.role == UserRole.TEACHER:
            ExamService._check_ownership(exam, current_user)
            return result
        if current_user.role == UserRole.STUDENT:
            owns = await db.scalar(
                select(StudentClass).filter_by(
                    id=result.student_class_id,
                    student_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException(
                    "You can only view your own result",
                )
            return result
        raise AuthorizationException("Permission denied")

    @staticmethod
    async def delete_exam_result(
        db: AsyncSession,
        result_id: int,
        current_user: User,
    ) -> None:
        """Was missing entirely -- an erroneously-uploaded result (wrong
        student, duplicate row) could never be removed; the only "update"
        path was re-uploading the whole class's results, which upserts by
        student_class_id and so can't delete a row, only overwrite it.
        """
        result = await exam_result_crud.get(db, result_id)
        if not result:
            raise ResourceNotFoundException(
                f"Exam result with id={result_id} not found",
            )
        exam = await ExamService._get_exam_or_raise(db, result.exam_id)
        if current_user.role == UserRole.TEACHER:
            ExamService._check_ownership(exam, current_user)
        elif current_user.role != UserRole.ADMIN:
            raise AuthorizationException("Permission denied")
        await exam_result_crud.delete(db, result_id)
        logger.info(
            f"Exam result deleted: id={result_id} by user={current_user.id}",
        )
