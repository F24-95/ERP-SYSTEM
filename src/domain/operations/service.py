from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import (
    AuthorizationException,
    BusinessLogicException,
    ResourceNotFoundException,
)
from src.core.logger import get_logger
from src.domain.academics.models import (
    AcademicSession,
    ClassRoom,
    ClassSubject,
)
from src.domain.curriculum.models import Subject
from src.domain.operations.crud import (
    attendance_crud,
    availability_crud,
    daily_class_crud,
    daily_student_crud,
    promotion_crud,
    student_class_crud,
    teacher_subject_crud,
    timeslot_crud,
    timetable_crud,
    weekday_crud,
)
from src.domain.operations.models import (
    ClassTimeTable,
    DailyClass,
    DailyClassStudent,
    StudentAttendance,
    StudentClass,
    StudentPromotionHistory,
    TeacherAvailability,
    TeacherSubject,
    TimeSlot,
    WeekDay,
)
from src.domain.operations.schemas import (
    DailyClassCreate,
    DailyClassUpdate,
    StudentClassCreate,
    TeacherSubjectCreate,
)
from src.domain.users.models import StudentProfile, TeacherProfile, User

logger = get_logger(__name__)


class EnrollmentService:
    """Handles teacher assignment and student enrollment with business-rule validation."""

    @staticmethod
    async def assign_teacher(
        db: AsyncSession,
        data: TeacherSubjectCreate,
    ) -> TeacherSubject:
        # FIX: Old project had no uniqueness check before INSERT, causing raw IntegrityError
        query = select(TeacherSubject).filter(
            and_(
                TeacherSubject.academic_sessions_id == data.academic_sessions_id,
                TeacherSubject.classroom_id == data.classroom_id,
                TeacherSubject.subject_id == data.subject_id,
            ),
        )
        if (await db.execute(query)).scalars().first():
            raise BusinessLogicException(
                "Teacher already assigned to this subject in the given class and session.",
            )
        result = await teacher_subject_crud.create(db, data.model_dump())
        logger.info(
            f"Assigned teacher={data.teacher_id} to subject={data.subject_id} class={data.classroom_id}",
        )
        return result

    @staticmethod
    async def enroll_student(
        db: AsyncSession,
        data: StudentClassCreate,
    ) -> StudentClass:
        # Check: student not already enrolled in this session
        q1 = select(StudentClass).filter(
            and_(
                StudentClass.academic_sessions_id == data.academic_sessions_id,
                StudentClass.student_id == data.student_id,
            ),
        )
        if (await db.execute(q1)).scalars().first():
            raise BusinessLogicException(
                "Student is already enrolled in this academic session.",
            )
        # Check: roll number not taken
        q2 = select(StudentClass).filter(
            and_(
                StudentClass.academic_sessions_id == data.academic_sessions_id,
                StudentClass.classroom_id == data.classroom_id,
                StudentClass.roll_number == data.roll_number,
            ),
        )
        if (await db.execute(q2)).scalars().first():
            raise BusinessLogicException(
                f"Roll number {data.roll_number} is already taken in this class.",
            )
        result = await student_class_crud.create(db, data.model_dump())
        logger.info(
            f"Enrolled student={data.student_id} class={data.classroom_id} roll={data.roll_number}",
        )
        return result

    # ------------------------------------------------------------------
    # Previously missing: no way to fetch a single teacher assignment or
    # student enrollment, and no way to undo either (unassign/unenroll).
    # Once created, both were permanent with zero API to reverse them.
    # ------------------------------------------------------------------

    @staticmethod
    async def list_teacher_assignments(db: AsyncSession) -> list[TeacherSubject]:
        items, _total = await teacher_subject_crud.get_all(db)
        return items

    @staticmethod
    async def list_student_enrollments(db: AsyncSession) -> list[StudentClass]:
        items, _total = await student_class_crud.get_all(db)
        return items

    @staticmethod
    async def get_teacher_assignment(
        db: AsyncSession,
        assignment_id: int,
    ) -> TeacherSubject:
        return await teacher_subject_crud.get_or_raise(db, assignment_id)

    @staticmethod
    async def update_teacher_assignment(
        db: AsyncSession,
        assignment_id: int,
        data: dict[str, Any],
    ) -> TeacherSubject:
        """Was missing entirely -- a teacher assignment could be created,
        listed, fetched singly, and unassigned, but never edited (e.g. to
        fix which class_subject it points at) without a full
        unassign+recreate.
        """
        await teacher_subject_crud.get_or_raise(db, assignment_id)
        return await teacher_subject_crud.update(db, assignment_id, data)

    @staticmethod
    async def unassign_teacher(db: AsyncSession, assignment_id: int) -> None:
        await teacher_subject_crud.get_or_raise(db, assignment_id)
        await teacher_subject_crud.update(db, assignment_id, {"is_active": False})
        logger.info(f"Teacher assignment deactivated: id={assignment_id}")

    @staticmethod
    async def get_student_enrollment(
        db: AsyncSession,
        enrollment_id: int,
    ) -> StudentClass:
        return await student_class_crud.get_or_raise(db, enrollment_id)

    @staticmethod
    async def update_student_enrollment(
        db: AsyncSession,
        enrollment_id: int,
        data: dict[str, Any],
    ) -> StudentClass:
        """Was missing entirely -- e.g. correcting a roll_number typo or
        updating remarks required a full unenroll+re-enroll.
        """
        await student_class_crud.get_or_raise(db, enrollment_id)
        return await student_class_crud.update(db, enrollment_id, data)

    @staticmethod
    async def unenroll_student(db: AsyncSession, enrollment_id: int) -> None:
        """Deactivates rather than hard-deletes: fees, exam results, and
        attendance can all reference a student's classroom enrollment
        indirectly, so removing the row outright risks orphaning history.
        """
        await student_class_crud.get_or_raise(db, enrollment_id)
        await student_class_crud.update(db, enrollment_id, {"is_active": False})
        logger.info(f"Student enrollment deactivated: id={enrollment_id}")

    @staticmethod
    async def promote_student(
        db: AsyncSession,
        student_id: int,
        from_session_id: int,
        to_session_id: int,
        to_classroom_id: int,
        new_roll: int,
        promoted_by: int,
    ) -> StudentPromotionHistory:
        # Get current enrollment
        q = select(StudentClass).filter(
            and_(
                StudentClass.student_id == student_id,
                StudentClass.academic_sessions_id == from_session_id,
            ),
        )
        current = (await db.execute(q)).scalars().first()
        if not current:
            raise ResourceNotFoundException(
                "Student enrollment not found in the source session.",
            )

        existing_target = await db.scalar(
            select(StudentClass).filter_by(
                student_id=student_id,
                academic_sessions_id=to_session_id,
            ),
        )
        if existing_target:
            raise BusinessLogicException(
                "Student is already enrolled in the target academic session.",
            )

        history = await promotion_crud.create(
            db,
            {
                "student_id": student_id,
                "from_session_id": from_session_id,
                "to_session_id": to_session_id,
                "from_classroom_id": current.classroom_id,
                "to_classroom_id": to_classroom_id,
                "previous_roll_number": current.roll_number,
                "new_roll_number": new_roll,
                "promotion_date": datetime.utcnow().date(),
                "promotion_type": "PROMOTED",
                "promoted_by_user_id": promoted_by,
            },
        )
        # Deactivate old enrollment
        current.status = "PROMOTED"

        # Was missing entirely -- promote_student recorded a
        # StudentPromotionHistory row and marked the old enrollment
        # "PROMOTED", but never actually created the new StudentClass
        # enrollment for the destination session/classroom. That made
        # promotion a no-op from the student's perspective: the history
        # log would say they were promoted, but they'd have zero active
        # enrollment anywhere afterwards -- unable to have exams, fees,
        # attendance, etc. recorded against them in the new session at all.
        new_enrollment = await student_class_crud.create(
            db,
            {
                "academic_sessions_id": to_session_id,
                "student_id": student_id,
                "classroom_id": to_classroom_id,
                "roll_number": new_roll,
                "admission_date": current.admission_date,
                "status": "ACTIVE",
                "roll_number_locked": False,
                "remarks": f"Promoted from session={from_session_id}",
            },
        )

        await db.flush()
        logger.info(
            f"Promoted student={student_id} from session={from_session_id} to session={to_session_id} "
            f"(new enrollment id={new_enrollment.id})",
        )
        return history

    @staticmethod
    async def get_promotion_history(
        db: AsyncSession,
        student_id: int,
    ) -> list[StudentPromotionHistory]:
        """Was missing entirely -- promote_student() had no corresponding
        read endpoint, so a promotion history could be written but never
        looked back up.
        """
        result = await db.execute(
            select(StudentPromotionHistory)
            .filter_by(student_id=student_id)
            .order_by(StudentPromotionHistory.promotion_date.desc()),
        )
        return list(result.scalars().all())


class DailyClassService:
    """Daily class CRUD + attendance marking.

    Ported verbatim from `app/routers/daily_class_routers.py` (the active,
    non-commented-out half of that file) — the legacy `attendance_service.py`
    is a 0-byte file and `AcademicService`'s daily-class/attendance methods
    are dead code (grepped: never called by any router), so exactly like
    assignments/exams/notices, the router itself is the source of truth
    here, not either service class.
    """

    @staticmethod
    async def _get_teacher_profile_or_raise(
        db: AsyncSession,
        user_id: int,
    ) -> TeacherProfile:
        teacher = await db.scalar(select(TeacherProfile).filter_by(user_id=user_id))
        if not teacher:
            raise ResourceNotFoundException("Teacher profile not found")
        return teacher

    @staticmethod
    async def create_daily_class(
        db: AsyncSession,
        data: DailyClassCreate,
        current_user: User,
    ) -> DailyClass:
        # Legacy verifies the teacher owns the TeacherSubject being scheduled.
        # Note: legacy `require_role(UserRole.TEACHER)` — admins cannot create
        # a daily class via this endpoint (unlike some other domains). Preserved.
        teacher_subject = await db.scalar(
            select(TeacherSubject).filter_by(
                id=data.teacher_subject_id,
                teacher_id=current_user.id,
            ),
        )
        if not teacher_subject:
            raise AuthorizationException("You are not assigned to this class")

        existing = await db.scalar(
            select(DailyClass).filter_by(
                teacher_subject_id=data.teacher_subject_id,
                class_date=data.class_date,
            ),
        )
        if existing:
            raise BusinessLogicException("Class already exists for this date")

        new_class = await daily_class_crud.create(db, data.model_dump())
        logger.info(
            f"Daily class created: {new_class.daily_class_id} by user={current_user.id}",
        )
        return new_class

    @staticmethod
    async def get_daily_classes(
        db: AsyncSession,
        current_user: User,
        classroom_id: int | None = None,
        class_date: date | None = None,
        lecture_status: str | None = None,
    ) -> list[DailyClass]:
        query = select(DailyClass)
        if classroom_id:
            query = query.filter(DailyClass.classroom_id == classroom_id)
        if class_date:
            query = query.filter(DailyClass.class_date == class_date)
        if lecture_status:
            query = query.filter(DailyClass.lecture_status == lecture_status)

        # Legacy scopes the list to the teacher's own classes when the
        # caller is a teacher (admins/others see everything the other
        # filters allow).
        if current_user.role == UserRole.TEACHER:
            teacher = await db.scalar(
                select(TeacherProfile).filter_by(user_id=current_user.id),
            )
            if teacher:
                teacher_subject_ids = select(TeacherSubject.id).filter(
                    TeacherSubject.teacher_id == current_user.id,
                )
                query = query.filter(
                    DailyClass.teacher_subject_id.in_(teacher_subject_ids),
                )

        query = query.order_by(DailyClass.class_date.desc())
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_daily_class(db: AsyncSession, daily_class_id: int) -> DailyClass:
        daily_class = await daily_class_crud.get(db, daily_class_id)
        if not daily_class:
            raise ResourceNotFoundException("Class not found")
        return daily_class

    @staticmethod
    async def update_daily_class(
        db: AsyncSession,
        daily_class_id: int,
        data: DailyClassUpdate,
        current_user: User,
    ) -> DailyClass:
        daily_class = await DailyClassService.get_daily_class(db, daily_class_id)

        teacher = await db.scalar(
            select(TeacherProfile).filter_by(user_id=current_user.id),
        )
        # NOTE: legacy compares `daily_class.teacher_subject_id != teacher.teacher_id`
        # (a TeacherSubject row id, not the teacher's own id) — this is the exact
        # ownership check as written in `update_daily_class`/`delete_daily_class`/
        # `mark_attendance` in the legacy router. In the new schema TeacherSubject
        # is keyed by `teacher_id == users.id`, so the equivalent check is against
        # a TeacherSubject the caller actually owns, reproduced below.
        if teacher:
            owns = await db.scalar(
                select(TeacherSubject).filter_by(
                    id=daily_class.teacher_subject_id,
                    teacher_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException("You can only update your own classes")

        update_data = data.model_dump(exclude_unset=True)
        return await daily_class_crud.update(db, daily_class_id, update_data)

    @staticmethod
    async def delete_daily_class(
        db: AsyncSession,
        daily_class_id: int,
        current_user: User,
    ) -> None:
        daily_class = await DailyClassService.get_daily_class(db, daily_class_id)

        teacher = await db.scalar(
            select(TeacherProfile).filter_by(user_id=current_user.id),
        )
        if teacher:
            owns = await db.scalar(
                select(TeacherSubject).filter_by(
                    id=daily_class.teacher_subject_id,
                    teacher_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException("You can only delete your own classes")

        await daily_class_crud.delete(db, daily_class_id)

    @staticmethod
    async def mark_attendance(
        db: AsyncSession,
        daily_class_id: int,
        attendance_data: list[dict[str, Any]],
        current_user: User,
    ) -> list[DailyClassStudent]:
        """Bulk upsert attendance for a daily class.

        Matches legacy exactly: creates-or-updates one DailyClassStudent row
        per item, skips items whose student_class doesn't belong to this
        class's classroom, and does NOT touch the `StudentAttendance`
        aggregate table (see note on StudentAttendance below).
        """
        daily_class = await DailyClassService.get_daily_class(db, daily_class_id)

        teacher = await db.scalar(
            select(TeacherProfile).filter_by(user_id=current_user.id),
        )
        if teacher:
            owns = await db.scalar(
                select(TeacherSubject).filter_by(
                    id=daily_class.teacher_subject_id,
                    teacher_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException(
                    "You can only mark attendance for your classes",
                )

        marked_records: list[DailyClassStudent] = []
        for item in attendance_data:
            student_class = await db.scalar(
                select(StudentClass).filter_by(
                    id=item["student_class_id"],
                    classroom_id=daily_class.classroom_id,
                ),
            )
            if not student_class:
                continue

            existing = await db.scalar(
                select(DailyClassStudent).filter_by(
                    daily_class_id=daily_class_id,
                    student_class_id=item["student_class_id"],
                ),
            )
            if existing:
                existing.attendance_status = item.get("attendance_status", "Present")
                existing.is_late = item.get("is_late", False)
                existing.late_minutes = item.get("late_minutes", 0)
                existing.remarks = item.get("remarks")
                existing.marked_by = current_user.id
                existing.marked_at = datetime.utcnow()
                marked_records.append(existing)
            else:
                new_record = DailyClassStudent(
                    daily_class_id=daily_class_id,
                    student_class_id=item["student_class_id"],
                    attendance_status=item.get("attendance_status", "Present"),
                    is_late=item.get("is_late", False),
                    late_minutes=item.get("late_minutes", 0),
                    remarks=item.get("remarks"),
                    marked_by=current_user.id,
                )
                db.add(new_record)
                marked_records.append(new_record)

        await db.flush()
        logger.info(
            f"Attendance marked for daily_class={daily_class_id} count={len(marked_records)}",
        )
        return marked_records

    @staticmethod
    async def get_attendance(
        db: AsyncSession,
        daily_class_id: int,
        current_user: User,
    ) -> list[DailyClassStudent]:
        """Was returning every student's attendance status for the session
        to any authenticated caller regardless of role -- a student could
        see whether every classmate was present/absent/late, not just
        their own record. Same privacy-leak pattern already fixed for exam
        and assignment results. Admin/teacher still see the full roster
        (a teacher needs that to review/correct attendance); a student
        only sees their own entry.
        """
        await DailyClassService.get_daily_class(db, daily_class_id)
        query = select(DailyClassStudent).filter_by(daily_class_id=daily_class_id)

        if current_user.role == UserRole.STUDENT:
            student_class_ids = (
                await db.scalars(
                    select(StudentClass.id).filter_by(student_id=current_user.id),
                )
            ).all()
            query = query.filter(
                DailyClassStudent.student_class_id.in_(student_class_ids),
            )
        elif current_user.role not in (UserRole.ADMIN, UserRole.TEACHER):
            raise AuthorizationException("Permission denied")

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_attendance_record(
        db: AsyncSession,
        record_id: int,
        current_user: User,
    ) -> DailyClassStudent:
        """Was missing entirely -- an individual attendance row could only
        ever be fetched as part of the full per-session roster.
        """
        record = await daily_student_crud.get(db, record_id)
        if not record:
            raise ResourceNotFoundException(
                f"Attendance record with id={record_id} not found",
            )
        if current_user.role == UserRole.STUDENT:
            owns = await db.scalar(
                select(StudentClass).filter_by(
                    id=record.student_class_id,
                    student_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException(
                    "You can only view your own attendance record",
                )
        elif current_user.role not in (UserRole.ADMIN, UserRole.TEACHER):
            raise AuthorizationException("Permission denied")
        return record

    @staticmethod
    async def update_attendance_record(
        db: AsyncSession,
        record_id: int,
        data: dict[str, Any],
        current_user: User,
    ) -> DailyClassStudent:
        """Correcting a single student's attendance was already possible by
        re-POSTing that one row through the bulk mark_attendance upsert,
        but there was no dedicated single-record endpoint for it, and no
        way to delete a record at all. Added for completeness/discoverability.
        """
        record = await daily_student_crud.get(db, record_id)
        if not record:
            raise ResourceNotFoundException(
                f"Attendance record with id={record_id} not found",
            )
        if current_user.role == UserRole.TEACHER:
            daily_class = await DailyClassService.get_daily_class(
                db,
                record.daily_class_id,
            )
            owns = await db.scalar(
                select(TeacherSubject).filter_by(
                    id=daily_class.teacher_subject_id,
                    teacher_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException(
                    "You can only correct attendance for your own classes",
                )
        elif current_user.role != UserRole.ADMIN:
            raise AuthorizationException("Permission denied")
        return await daily_student_crud.update(db, record_id, data)

    @staticmethod
    async def delete_attendance_record(
        db: AsyncSession,
        record_id: int,
        current_user: User,
    ) -> None:
        """Was missing entirely -- an erroneously-created attendance row
        (e.g. a transferred-out student marked in the wrong class) could
        never be removed.
        """
        record = await daily_student_crud.get(db, record_id)
        if not record:
            raise ResourceNotFoundException(
                f"Attendance record with id={record_id} not found",
            )
        if current_user.role == UserRole.TEACHER:
            daily_class = await DailyClassService.get_daily_class(
                db,
                record.daily_class_id,
            )
            owns = await db.scalar(
                select(TeacherSubject).filter_by(
                    id=daily_class.teacher_subject_id,
                    teacher_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException(
                    "You can only delete attendance for your own classes",
                )
        elif current_user.role != UserRole.ADMIN:
            raise AuthorizationException("Permission denied")
        await daily_student_crud.delete(db, record_id)
        logger.info(
            f"Attendance record deleted: id={record_id} by user={current_user.id}",
        )

    @staticmethod
    async def recalculate_attendance_summary(
        db: AsyncSession,
        student_class_id: int,
    ) -> StudentAttendance:
        """Was missing entirely -- the StudentAttendance aggregate table
        (total/present/absent/percentage) existed with a CRUD instance but
        nothing ever wrote to it. get_class_summary's hardcoded
        `attendance_average: 0` (documented as a preserved legacy TODO) is
        this same gap surfacing on the class-dashboard side. This computes
        it on demand from DailyClassStudent rather than adding a
        scheduler/cron (no such infra exists in this project yet).
        """
        result = await db.execute(
            select(
                DailyClassStudent.attendance_status,
                func.count(DailyClassStudent.id),
            )
            .filter_by(student_class_id=student_class_id)
            .group_by(DailyClassStudent.attendance_status),
        )
        counts = dict(result.all())
        total = sum(counts.values())
        present = counts.get("Present", 0)
        absent = counts.get("Absent", 0)
        percentage = round((present / total) * 100, 2) if total else 0.0

        existing = await db.scalar(
            select(StudentAttendance).filter_by(student_class_id=student_class_id),
        )
        payload = {
            "student_class_id": student_class_id,
            "total_classes": total,
            "present_classes": present,
            "absent_classes": absent,
            "attendance_percentage": percentage,
        }
        if existing:
            return await attendance_crud.update(db, existing.id, payload)
        return await attendance_crud.create(db, payload)

    @staticmethod
    async def get_attendance_summary(
        db: AsyncSession,
        student_class_id: int,
        current_user: User,
    ) -> StudentAttendance | None:
        """Was missing entirely alongside the recalculation above."""
        if current_user.role == UserRole.STUDENT:
            owns = await db.scalar(
                select(StudentClass).filter_by(
                    id=student_class_id,
                    student_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException(
                    "You can only view your own attendance summary",
                )
        elif current_user.role not in (UserRole.ADMIN, UserRole.TEACHER):
            raise AuthorizationException("Permission denied")
        return await db.scalar(
            select(StudentAttendance).filter_by(student_class_id=student_class_id),
        )

    @staticmethod
    async def get_class_summary(
        db: AsyncSession,
        classroom_id: int,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        result = await db.execute(
            select(DailyClass).filter(
                DailyClass.classroom_id == classroom_id,
                DailyClass.class_date >= start_date,
                DailyClass.class_date <= end_date,
            ),
        )
        classes = list(result.scalars().all())
        return {
            "classroom_id": classroom_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_classes": len(classes),
            "completed": len([c for c in classes if c.lecture_status == "Completed"]),
            "cancelled": len([c for c in classes if c.lecture_status == "Cancelled"]),
            # Legacy leaves this hardcoded with a "Calculate from attendance
            # records" TODO comment in `daily_class_routers.py::get_class_summary`
            # — it was never wired up in production. Preserved as-is, not
            # silently implemented, since real values here would be a new
            # behavior change, not a parity fix.
            "attendance_average": 0,
        }


# NOTE on StudentAttendance: the legacy production attendance-marking path
# (`daily_class_routers.py::mark_attendance`, ported above) never writes to
# the `student_attendance` aggregate table. Only the dead-code
# `AcademicService.mark_attendance` / `StudentAttendanceRepository` (never
# called by any router — confirmed via grep) maintain it. So in real legacy
# usage this table is effectively always empty. We preserve that gap rather
# than silently wiring the aggregate update into the live endpoint, since
# that would be new behavior, not migration parity. Flagging here for
# visibility in case the business wants it turned on going forward.


class TimetableService:
    """Weekday/timeslot/timetable/availability management, plus the
    student- and teacher-facing computed timetable views.

    Ported from legacy `app/services/timetable_service.py` (admin list/
    update/delete + student/teacher views) and `app/services/academic_service.py`
    (weekday/timeslot/timetable/availability create+read, the only parts of
    that service that ARE referenced by a router — see `timetable_routers.py`).
    """

    # -------------------------
    # Week day / time slot (thin passthroughs, no business logic in legacy)
    # -------------------------
    @staticmethod
    async def get_all_weekdays(db: AsyncSession) -> list[WeekDay]:
        result = await db.execute(
            select(WeekDay).filter(WeekDay.is_active).order_by(WeekDay.display_order),
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_weekday(db: AsyncSession, data: dict[str, Any]) -> WeekDay:
        return await weekday_crud.create(db, data)

    @staticmethod
    async def update_weekday(
        db: AsyncSession,
        weekday_id: int,
        data: dict[str, Any],
    ) -> WeekDay:
        """Was missing -- weekdays/timeslots had create+list only, no way
        to fix a typo or reorder without deleting and recreating (which
        wasn't possible either, since delete didn't exist).
        """
        await weekday_crud.get_or_raise(db, weekday_id)
        return await weekday_crud.update(db, weekday_id, data)

    @staticmethod
    async def deactivate_weekday(db: AsyncSession, weekday_id: int) -> None:
        await weekday_crud.get_or_raise(db, weekday_id)
        await weekday_crud.update(db, weekday_id, {"is_active": False})

    @staticmethod
    async def get_all_timeslots(db: AsyncSession) -> list[TimeSlot]:
        result = await db.execute(
            select(TimeSlot)
            .filter(TimeSlot.is_active)
            .order_by(TimeSlot.display_order),
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_timeslot(db: AsyncSession, data: dict[str, Any]) -> TimeSlot:
        return await timeslot_crud.create(db, data)

    @staticmethod
    async def update_timeslot(
        db: AsyncSession,
        timeslot_id: int,
        data: dict[str, Any],
    ) -> TimeSlot:
        await timeslot_crud.get_or_raise(db, timeslot_id)
        return await timeslot_crud.update(db, timeslot_id, data)

    @staticmethod
    async def deactivate_timeslot(db: AsyncSession, timeslot_id: int) -> None:
        await timeslot_crud.get_or_raise(db, timeslot_id)
        await timeslot_crud.update(db, timeslot_id, {"is_active": False})

    # -------------------------
    # Timetable (admin)
    # -------------------------
    @staticmethod
    async def create_timetable(
        db: AsyncSession,
        data: dict[str, Any],
    ) -> ClassTimeTable:
        return await timetable_crud.create(db, data)

    @staticmethod
    async def get_class_timetable(
        db: AsyncSession,
        classroom_id: int,
        session_id: int,
    ) -> list[ClassTimeTable]:
        result = await db.execute(
            select(ClassTimeTable).filter(
                ClassTimeTable.classroom_id == classroom_id,
                ClassTimeTable.academic_sessions_id == session_id,
                ClassTimeTable.is_active,
            ),
        )
        return list(result.scalars().all())

    @staticmethod
    async def admin_get_timetables(
        db: AsyncSession,
        classroom_id: int | None = None,
        teacher_subject_id: int | None = None,
        class_subject_id: int | None = None,
        week_day_id: int | None = None,
    ) -> list[ClassTimeTable]:
        query = select(ClassTimeTable).filter(ClassTimeTable.is_active)
        if classroom_id is not None:
            query = query.filter(ClassTimeTable.classroom_id == classroom_id)
        if teacher_subject_id is not None:
            query = query.filter(
                ClassTimeTable.teacher_subject_id == teacher_subject_id,
            )
        if class_subject_id is not None:
            query = query.filter(ClassTimeTable.class_subject_id == class_subject_id)
        if week_day_id is not None:
            query = query.filter(ClassTimeTable.week_day_id == week_day_id)

        query = query.order_by(
            ClassTimeTable.academic_sessions_id.asc(),
            ClassTimeTable.classroom_id.asc(),
            ClassTimeTable.week_day_id.asc(),
            ClassTimeTable.time_slot_id.asc(),
        )
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def admin_update_timetable(
        db: AsyncSession,
        timetable_id: int,
        update_fields: dict[str, Any],
    ) -> ClassTimeTable | None:
        entry = await timetable_crud.get(db, timetable_id)
        if not entry:
            return None

        allowed = {
            "room_number",
            "remarks",
            "academic_sessions_id",
            "classroom_id",
            "class_subject_id",
            "teacher_subject_id",
            "week_day_id",
            "time_slot_id",
            "is_active",
        }
        filtered = {k: v for k, v in update_fields.items() if k in allowed}
        return await timetable_crud.update(db, timetable_id, filtered)

    @staticmethod
    async def admin_delete_timetable(db: AsyncSession, timetable_id: int) -> bool:
        entry = await timetable_crud.get(db, timetable_id)
        if not entry:
            return False
        # Legacy soft-deletes (sets is_active = False), same as this model's
        # only "deletion" mechanism (ClassTimeTable has no is_deleted column).
        await timetable_crud.update(db, timetable_id, {"is_active": False})
        return True

    # -------------------------
    # Student timetable view
    # -------------------------
    @staticmethod
    async def _get_current_academic_session_id(db: AsyncSession) -> int:
        session = await db.scalar(select(AcademicSession).filter_by(is_current=True))
        if not session:
            raise ResourceNotFoundException("Current academic session not found")
        return session.id

    @staticmethod
    async def student_get_timetable(
        db: AsyncSession,
        student_user_id: int,
    ) -> list[dict[str, Any]]:
        current_session_id = await TimetableService._get_current_academic_session_id(db)

        student = await db.scalar(
            select(StudentProfile).filter_by(user_id=student_user_id),
        )
        if not student:
            raise ResourceNotFoundException("Student profile not found")

        result = await db.execute(
            select(StudentClass).filter(
                StudentClass.student_id == student_user_id,
                StudentClass.academic_sessions_id == current_session_id,
                StudentClass.status == "ACTIVE",
            ),
        )
        student_classes = list(result.scalars().all())
        if not student_classes:
            return []

        classroom_ids = [sc.classroom_id for sc in student_classes]

        query = (
            select(
                WeekDay.day_name.label("day"),
                TimeSlot.start_time.label("start_time"),
                TimeSlot.end_time.label("end_time"),
                Subject.subject_name.label("subject"),
                TeacherProfile.teacher_name.label("teacher"),
            )
            .select_from(ClassTimeTable)
            .join(WeekDay, WeekDay.id == ClassTimeTable.week_day_id)
            .join(TimeSlot, TimeSlot.id == ClassTimeTable.time_slot_id)
            .join(ClassSubject, ClassSubject.id == ClassTimeTable.class_subject_id)
            .join(Subject, Subject.id == ClassSubject.subject_id)
            .join(
                TeacherSubject,
                TeacherSubject.id == ClassTimeTable.teacher_subject_id,
            )
            .join(TeacherProfile, TeacherProfile.user_id == TeacherSubject.teacher_id)
            .filter(
                ClassTimeTable.is_active,
                ClassTimeTable.academic_sessions_id == current_session_id,
                ClassTimeTable.classroom_id.in_(classroom_ids),
            )
            .order_by(
                WeekDay.display_order.asc(),
                TimeSlot.display_order.asc(),
                ClassTimeTable.classroom_id.asc(),
            )
        )
        rows = (await db.execute(query)).all()
        return [
            {
                "day": r.day,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "subject": r.subject,
                "teacher": r.teacher,
            }
            for r in rows
        ]

    # -------------------------
    # Teacher timetable view
    # -------------------------
    @staticmethod
    async def teacher_get_timetable(
        db: AsyncSession,
        teacher_user_id: int,
    ) -> list[dict[str, Any]]:
        current_session_id = await TimetableService._get_current_academic_session_id(db)

        teacher = await db.scalar(
            select(TeacherProfile).filter_by(user_id=teacher_user_id),
        )
        if not teacher:
            raise ResourceNotFoundException("Teacher profile not found")

        result = await db.execute(
            select(TeacherSubject.id).filter(
                TeacherSubject.teacher_id == teacher_user_id,
                TeacherSubject.academic_sessions_id == current_session_id,
                TeacherSubject.is_active,
            ),
        )
        allowed_teacher_subject_ids = [x[0] for x in result.all()]
        if not allowed_teacher_subject_ids:
            return []

        query = (
            select(
                ClassRoom.display_name.label("classroom_display_name"),
                Subject.subject_name.label("subject"),
                WeekDay.day_name.label("day"),
                TimeSlot.start_time.label("start_time"),
                TimeSlot.end_time.label("end_time"),
            )
            .select_from(ClassTimeTable)
            .join(ClassRoom, ClassRoom.id == ClassTimeTable.classroom_id)
            .join(ClassSubject, ClassSubject.id == ClassTimeTable.class_subject_id)
            .join(Subject, Subject.id == ClassSubject.subject_id)
            .join(WeekDay, WeekDay.id == ClassTimeTable.week_day_id)
            .join(TimeSlot, TimeSlot.id == ClassTimeTable.time_slot_id)
            .filter(
                ClassTimeTable.is_active,
                ClassTimeTable.academic_sessions_id == current_session_id,
                ClassTimeTable.teacher_subject_id.in_(allowed_teacher_subject_ids),
            )
            .order_by(
                ClassRoom.class_name.asc(),
                WeekDay.display_order.asc(),
                TimeSlot.display_order.asc(),
            )
        )
        rows = (await db.execute(query)).all()
        # NOTE: legacy builds this same result as
        # `{"class": r.class_, "subject": ..., ...}` where the SQLAlchemy Row
        # label is "class" — `r.class_` doesn't exist on the Row (the label
        # is "class", not "class_"), so that line raises AttributeError on
        # every real call, and the endpoint is broken in the old codebase.
        # Since there's no documented intended alternate behavior to
        # preserve (this isn't a business rule, it's a typo), we fix it here
        # by reading the row correctly, and use TeacherTimetableItemResponse's
        # `class_`-aliased-to-`"class"` field so the JSON shape (`day`,
        # `subject`, `time`, `class`) still matches what the schema promised.
        return [
            {
                "class_": r.classroom_display_name,
                "subject": r.subject,
                "day": r.day,
                "time": f"{r.start_time} - {r.end_time}",
            }
            for r in rows
        ]

    # -------------------------
    # Teacher availability
    # -------------------------
    @staticmethod
    async def create_availability(
        db: AsyncSession,
        data: dict[str, Any],
    ) -> TeacherAvailability:
        return await availability_crud.create(db, data)

    @staticmethod
    async def get_teacher_availability(
        db: AsyncSession,
        teacher_subject_id: int,
        session_id: int,
    ) -> list[TeacherAvailability]:
        result = await db.execute(
            select(TeacherAvailability).filter(
                TeacherAvailability.teacher_subject_id == teacher_subject_id,
                TeacherAvailability.academic_sessions_id == session_id,
                TeacherAvailability.is_active,
            ),
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_availability(
        db: AsyncSession,
        availability_id: int,
        update_fields: dict[str, Any],
    ) -> TeacherAvailability | None:
        entry = await availability_crud.get(db, availability_id)
        if not entry:
            return None
        return await availability_crud.update(db, availability_id, update_fields)

    @staticmethod
    async def deactivate_availability(
        db: AsyncSession,
        availability_id: int,
    ) -> TeacherAvailability | None:
        """Was missing -- a teacher could mark themselves available/update
        it, but never withdraw an availability slot entirely.
        """
        entry = await availability_crud.get(db, availability_id)
        if not entry:
            return None
        return await availability_crud.update(db, availability_id, {"is_active": False})
