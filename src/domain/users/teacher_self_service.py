"""TeacherSelfService

Self-service endpoints logic for the logged-in teacher: profile, assigned
classes/students/subjects, attendance marking, assignment listing, and a
dashboard summary. Ported from legacy `app/routers/teacher_router.py`.

Same schema-shape note as StudentSelfService: `TeacherSubject.teacher_id`
here is the teacher's `users.id` (integer), not the string
`teacher_profiles.teacher_id` business code, so lookups filter by
`current_user.id` directly — no `IdentifierResolverService` needed.
"""

from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    AuthorizationException,
    ResourceNotFoundException,
)
from src.core.logger import get_logger
from src.domain.academics.models import ClassRoom
from src.domain.assignments.models import Assignment
from src.domain.operations.models import (
    DailyClass,
    DailyClassStudent,
    StudentClass,
    TeacherSubject,
)
from src.domain.users.models import TeacherProfile

logger = get_logger(__name__)


class TeacherSelfService:
    @staticmethod
    async def _get_profile(
        db: AsyncSession,
        user_id: int,
    ) -> TeacherProfile:
        profile = await db.scalar(
            select(TeacherProfile).filter_by(user_id=user_id),
        )
        if not profile:
            raise ResourceNotFoundException("Teacher profile not found")
        return profile

    @staticmethod
    async def get_profile(
        db: AsyncSession,
        user_id: int,
    ) -> TeacherProfile:
        return await TeacherSelfService._get_profile(db, user_id)

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user_id: int,
        data: dict[str, Any],
    ) -> TeacherProfile:
        profile = await TeacherSelfService._get_profile(db, user_id)
        for key, value in data.items():
            setattr(profile, key, value)
        await db.flush()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def get_classes(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int | None = None,
    ) -> list[ClassRoom]:
        await TeacherSelfService._get_profile(db, user_id)

        query = (
            select(ClassRoom)
            .join(
                TeacherSubject,
                TeacherSubject.classroom_id == ClassRoom.id,
            )
            .filter(TeacherSubject.teacher_id == user_id)
            .distinct()
        )
        if academic_sessions_id:
            query = query.filter(
                ClassRoom.academic_sessions_id == academic_sessions_id,
            )
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_class_students(
        db: AsyncSession,
        user_id: int,
        classroom_id: int,
        academic_sessions_id: int,
    ) -> list[StudentClass]:
        await TeacherSelfService._get_profile(db, user_id)

        owns = await db.scalar(
            select(TeacherSubject).filter_by(
                teacher_id=user_id,
                classroom_id=classroom_id,
                academic_sessions_id=academic_sessions_id,
            ),
        )
        if not owns:
            raise AuthorizationException(
                "You are not assigned to this class",
            )

        query = (
            select(StudentClass)
            .filter(
                StudentClass.classroom_id == classroom_id,
                StudentClass.academic_sessions_id == academic_sessions_id,
                StudentClass.status == "ACTIVE",
            )
            .order_by(StudentClass.roll_number)
        )
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_my_students(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int,
        classroom_id: int | None = None,
    ) -> list[StudentClass]:
        await TeacherSelfService._get_profile(db, user_id)

        allowed_query = select(TeacherSubject.classroom_id).filter(
            TeacherSubject.teacher_id == user_id,
            TeacherSubject.academic_sessions_id == academic_sessions_id,
            TeacherSubject.is_active,
        )
        if classroom_id is not None:
            allowed_query = allowed_query.filter(
                TeacherSubject.classroom_id == classroom_id,
            )

        query = (
            select(StudentClass)
            .filter(
                StudentClass.academic_sessions_id == academic_sessions_id,
                StudentClass.status == "ACTIVE",
                StudentClass.classroom_id.in_(allowed_query),
            )
            .order_by(StudentClass.roll_number)
        )
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_subjects(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int | None = None,
    ) -> list[TeacherSubject]:
        await TeacherSelfService._get_profile(db, user_id)

        query = select(TeacherSubject).filter(
            TeacherSubject.teacher_id == user_id,
        )
        if academic_sessions_id:
            query = query.filter(
                TeacherSubject.academic_sessions_id == academic_sessions_id,
            )
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def mark_attendance(
        db: AsyncSession,
        user_id: int,
        daily_class_id: int,
        attendance_list: list[dict[str, Any]],
    ) -> dict[str, Any]:
        await TeacherSelfService._get_profile(db, user_id)

        teacher_subject_ids = select(TeacherSubject.id).filter(
            TeacherSubject.teacher_id == user_id,
        )
        daily_class = await db.scalar(
            select(DailyClass).filter(
                DailyClass.id == daily_class_id,
                DailyClass.teacher_subject_id.in_(teacher_subject_ids),
            ),
        )
        if not daily_class:
            raise ResourceNotFoundException(
                "Class not found or not assigned to you",
            )

        marked = 0
        for item in attendance_list:
            student_class_id = item.get("student_class_id")
            student_class = await db.scalar(
                select(StudentClass).filter_by(
                    id=student_class_id,
                    classroom_id=daily_class.classroom_id,
                ),
            )
            if not student_class:
                continue

            existing = await db.scalar(
                select(DailyClassStudent).filter_by(
                    daily_class_id=daily_class_id,
                    student_class_id=student_class_id,
                ),
            )
            fields = dict(
                attendance_status=item.get(
                    "attendance_status",
                    "Present",
                ),
                is_late=item.get("is_late", False),
                late_minutes=item.get("late_minutes", 0),
                remarks=item.get("remarks"),
                marked_by=user_id,
            )
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
            else:
                db.add(
                    DailyClassStudent(
                        daily_class_id=daily_class_id,
                        student_class_id=student_class_id,
                        **fields,
                    ),
                )
            marked += 1

        await db.flush()

        # Keep the StudentAttendance aggregate table in sync (matches
        # DailyClassService.mark_attendance's behavior).
        from src.domain.operations.service import DailyClassService

        marked_ids = {
            item.get("student_class_id")
            for item in attendance_list
            if item.get("student_class_id")
        }
        for student_class_id in marked_ids:
            await DailyClassService.recalculate_attendance(
                db,
                student_class_id,
            )

        return {
            "success": True,
            "message": f"Attendance marked for {marked} students",
            "total_marked": marked,
        }

    @staticmethod
    async def get_assignments(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int | None = None,
        classroom_id: int | None = None,
        status_filter: str | None = None,
    ) -> list[Assignment]:
        await TeacherSelfService._get_profile(db, user_id)

        teacher_subject_ids = select(TeacherSubject.id).filter(
            TeacherSubject.teacher_id == user_id,
            TeacherSubject.is_active,
        )
        query = select(Assignment).filter(
            Assignment.teacher_subject_id.in_(teacher_subject_ids),
        )
        if academic_sessions_id is not None:
            query = query.filter(
                Assignment.academic_sessions_id == academic_sessions_id,
            )
        if classroom_id:
            query = query.filter(
                Assignment.classroom_id == classroom_id,
            )
        if status_filter:
            query = query.filter(
                Assignment.status == status_filter,
            )
        query = query.order_by(Assignment.created_at.desc())
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_dashboard(
        db: AsyncSession,
        user_id: int,
    ) -> dict[str, Any]:
        await TeacherSelfService._get_profile(db, user_id)

        total_classes = (
            await db.scalar(
                select(func.count())
                .select_from(TeacherSubject)
                .filter(
                    TeacherSubject.teacher_id == user_id,
                    TeacherSubject.is_active,
                ),
            )
            or 0
        )

        total_students = (
            await db.scalar(
                select(func.count())
                .select_from(StudentClass)
                .join(
                    TeacherSubject,
                    TeacherSubject.classroom_id
                    == StudentClass.classroom_id,
                )
                .filter(
                    TeacherSubject.teacher_id == user_id,
                    StudentClass.status == "ACTIVE",
                ),
            )
            or 0
        )

        total_assignments = (
            await db.scalar(
                select(func.count())
                .select_from(Assignment)
                .filter(
                    Assignment.teacher_subject_id.in_(
                        select(TeacherSubject.id).filter(
                            TeacherSubject.teacher_id == user_id,
                        ),
                    ),
                ),
            )
            or 0
        )

        teacher_subject_ids = select(TeacherSubject.id).filter(
            TeacherSubject.teacher_id == user_id,
        )
        today_classes = (
            await db.scalar(
                select(func.count())
                .select_from(DailyClass)
                .filter(
                    DailyClass.teacher_subject_id.in_(
                        teacher_subject_ids,
                    ),
                    DailyClass.class_date == date.today(),
                ),
            )
            or 0
        )

        return {
            "total_classes": total_classes,
            "total_students": total_students,
            "total_assignments": total_assignments,
            "pending_assignments": 0,
            "today_classes": today_classes,
        }
