from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import AuthorizationException, ResourceNotFoundException
from src.core.logger import get_logger
from src.domain.assignments.crud import assignment_crud, assignment_result_crud
from src.domain.assignments.models import Assignment, AssignmentResult
from src.domain.assignments.schemas import (
    AssignmentCreate,
    AssignmentResultCreate,
    AssignmentUpdate,
)
from src.domain.operations.models import StudentClass, TeacherSubject
from src.domain.users.models import TeacherProfile, User

logger = get_logger(__name__)


class AssignmentService:
    @staticmethod
    async def _get_assignment_or_raise(
        db: AsyncSession,
        assignment_id: int,
    ) -> Assignment:
        assignment = await assignment_crud.get(db, assignment_id)
        if not assignment:
            raise ResourceNotFoundException(
                f"Assignment with id={assignment_id} not found",
            )
        return assignment

    @staticmethod
    def _check_ownership(assignment: Assignment, current_user: User) -> None:
        """Only the assignment's creator or an admin may modify it — matches
        the legacy router's inline `assignment.created_by != current_user.id
        and current_user.role != UserRole.ADMIN` check.
        """
        if (
            assignment.created_by != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            raise AuthorizationException("You can only modify your own assignments")

    @staticmethod
    async def _check_can_view(
        db: AsyncSession,
        assignment: Assignment,
        current_user: User,
    ) -> None:
        """Was `_check_teacher_can_view`, and unconditionally denied every
        role except admin/teacher -- meaning a student could never view a
        single assignment or their own results at all
        (GET /assignments/{id} and GET /assignments/{id}/results both
        raised AuthorizationException("Permission denied") for every
        student, every time). Fixed to let a student view an assignment
        for a class they're actually enrolled in.
        """
        if current_user.role == UserRole.ADMIN:
            return
        if current_user.role == UserRole.TEACHER:
            teacher = await db.scalar(
                select(TeacherProfile).filter_by(user_id=current_user.id),
            )
            if not teacher:
                raise ResourceNotFoundException("Teacher profile not found")
            teacher_subject = await db.scalar(
                select(TeacherSubject).filter_by(
                    id=assignment.teacher_subject_id,
                    teacher_id=current_user.id,
                    is_active=True,
                ),
            )
            if not teacher_subject:
                raise AuthorizationException("You can only view assignments you teach")
            return
        if current_user.role == UserRole.STUDENT:
            enrolled = await db.scalar(
                select(StudentClass).filter(
                    StudentClass.student_id == current_user.id,
                    StudentClass.classroom_id == assignment.classroom_id,
                    StudentClass.is_active == True,
                ),
            )
            if not enrolled:
                raise AuthorizationException(
                    "You can only view assignments for your own class",
                )
            return
        raise AuthorizationException("Permission denied")

    @staticmethod
    async def create_assignment(
        db: AsyncSession,
        assignment_data: AssignmentCreate,
        current_user: User,
    ) -> Assignment:
        teacher = await db.scalar(
            select(TeacherProfile).filter_by(user_id=current_user.id),
        )
        if not teacher:
            raise ResourceNotFoundException("Teacher profile not found")

        teacher_subject = await db.scalar(
            select(TeacherSubject).filter_by(
                id=assignment_data.teacher_subject_id,
                teacher_id=current_user.id,
            ),
        )
        if not teacher_subject:
            raise AuthorizationException("You are not assigned to this class")

        data = assignment_data.model_dump()
        data["uploaded_by"] = current_user.id
        data["created_by"] = current_user.id
        assignment = await assignment_crud.create(db, data)
        logger.info(
            f"Assignment created: {assignment.assignment_id} by user={current_user.id}",
        )
        return assignment

    @staticmethod
    async def get_assignments(
        db: AsyncSession,
        current_user: User,
        classroom_id: int | None = None,
        status: str | None = None,
    ) -> list[Assignment]:
        query = select(Assignment).filter(Assignment.is_active == True)  # noqa: E712
        if classroom_id is not None:
            query = query.filter(Assignment.classroom_id == classroom_id)
        if status is not None:
            query = query.filter(Assignment.status == status)

        if current_user.role == UserRole.TEACHER:
            ts_ids = select(TeacherSubject.id).filter_by(teacher_id=current_user.id)
            query = query.filter(Assignment.teacher_subject_id.in_(ts_ids))
        elif current_user.role == UserRole.STUDENT:
            # Was previously unfiltered for students -- any logged-in
            # student could see every class's assignments, not just theirs.
            classroom_ids = select(StudentClass.classroom_id).filter_by(
                student_id=current_user.id,
            )
            query = query.filter(Assignment.classroom_id.in_(classroom_ids))

        query = query.order_by(Assignment.due_date.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_assignment(
        db: AsyncSession,
        assignment_id: int,
        current_user: User,
    ) -> Assignment:
        assignment = await AssignmentService._get_assignment_or_raise(db, assignment_id)
        await AssignmentService._check_can_view(db, assignment, current_user)
        return assignment

    @staticmethod
    async def update_assignment(
        db: AsyncSession,
        assignment_id: int,
        assignment_data: AssignmentUpdate,
        current_user: User,
    ) -> Assignment:
        assignment = await AssignmentService._get_assignment_or_raise(db, assignment_id)
        AssignmentService._check_ownership(assignment, current_user)

        updates = assignment_data.model_dump(exclude_unset=True)
        updates["updated_by"] = current_user.id
        updated = await assignment_crud.update(db, assignment_id, updates)
        logger.info(
            f"Assignment updated: {updated.assignment_id} by user={current_user.id}",
        )
        return updated

    @staticmethod
    async def delete_assignment(
        db: AsyncSession,
        assignment_id: int,
        current_user: User,
    ) -> None:
        assignment = await AssignmentService._get_assignment_or_raise(db, assignment_id)
        AssignmentService._check_ownership(assignment, current_user)

        await assignment_crud.update(
            db,
            assignment_id,
            {"is_active": False, "deleted_by": current_user.id},
        )
        logger.info(
            f"Assignment deleted: {assignment.assignment_id} by user={current_user.id}",
        )

    @staticmethod
    async def grade_assignment(
        db: AsyncSession,
        assignment_id: int,
        results_data: list[AssignmentResultCreate],
        current_user: User,
    ) -> list[AssignmentResult]:
        assignment = await AssignmentService._get_assignment_or_raise(db, assignment_id)
        AssignmentService._check_ownership(assignment, current_user)

        graded = []
        for item in results_data:
            existing = await db.scalar(
                select(AssignmentResult).filter_by(
                    assignment_id=assignment_id,
                    student_class_id=item.student_class_id,
                ),
            )
            if existing:
                data = item.model_dump(exclude={"student_class_id"})
                data["is_checked"] = True
                data["checked_at"] = datetime.utcnow()
                data["checked_by"] = current_user.id
                updated = await assignment_result_crud.update(db, existing.id, data)
                graded.append(updated)
            else:
                data = item.model_dump()
                data["assignment_id"] = assignment_id
                data["is_checked"] = True
                data["checked_at"] = datetime.utcnow()
                data["checked_by"] = current_user.id
                created = await assignment_result_crud.create(db, data)
                graded.append(created)

        # Legacy behavior: checked_students is set to the count of results in
        # *this* grading call, not the cumulative total across all calls.
        assignment.checked_students = len(graded)
        await db.flush()
        logger.info(
            f"Graded {len(graded)} results for assignment={assignment.assignment_id}",
        )
        return graded

    @staticmethod
    async def get_assignment_results(
        db: AsyncSession,
        assignment_id: int,
        current_user: User,
    ) -> list[AssignmentResult]:
        """Was returning every student's grade for the assignment to anyone
        who passed the (previously admin/teacher-only) view check. Now that
        students can view too, results must be scoped: a student only ever
        sees their own grade, never classmates'.
        """
        assignment = await AssignmentService._get_assignment_or_raise(db, assignment_id)
        await AssignmentService._check_can_view(db, assignment, current_user)

        all_results = await assignment_result_crud.get_many(
            db,
            filters={"assignment_id": assignment_id},
        )

        if current_user.role == UserRole.STUDENT:
            student_class_ids = (
                await db.scalars(
                    select(StudentClass.id).filter_by(student_id=current_user.id),
                )
            ).all()
            return [r for r in all_results if r.student_class_id in student_class_ids]

        return all_results

    @staticmethod
    async def get_assignment_result(
        db: AsyncSession,
        result_id: int,
        current_user: User,
    ) -> AssignmentResult:
        """Was missing entirely -- a specific student's grade could only
        ever be fetched as part of the full list, never on its own.
        """
        result = await assignment_result_crud.get(db, result_id)
        if not result:
            raise ResourceNotFoundException(
                f"Assignment result with id={result_id} not found",
            )

        assignment = await AssignmentService._get_assignment_or_raise(
            db,
            result.assignment_id,
        )
        await AssignmentService._check_can_view(db, assignment, current_user)

        if current_user.role == UserRole.STUDENT:
            owns = await db.scalar(
                select(StudentClass).filter_by(
                    id=result.student_class_id,
                    student_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException("You can only view your own result")

        return result

    @staticmethod
    async def delete_assignment_result(
        db: AsyncSession,
        result_id: int,
        current_user: User,
    ) -> None:
        """Was missing entirely -- an erroneously-graded/duplicate result
        row could never be removed, only overwritten via re-grading.
        """
        result = await assignment_result_crud.get(db, result_id)
        if not result:
            raise ResourceNotFoundException(
                f"Assignment result with id={result_id} not found",
            )

        assignment = await AssignmentService._get_assignment_or_raise(
            db,
            result.assignment_id,
        )
        if current_user.role == UserRole.TEACHER:
            teacher_subject = await db.scalar(
                select(TeacherSubject).filter_by(
                    id=assignment.teacher_subject_id,
                    teacher_id=current_user.id,
                    is_active=True,
                ),
            )
            if not teacher_subject:
                raise AuthorizationException(
                    "You can only delete results for assignments you teach",
                )
        elif current_user.role != UserRole.ADMIN:
            raise AuthorizationException("Permission denied")

        await assignment_result_crud.delete(db, result_id)
        logger.info(
            f"Assignment result deleted: id={result_id} by user={current_user.id}",
        )
