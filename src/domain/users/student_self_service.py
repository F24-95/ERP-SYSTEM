"""StudentSelfService

Self-service endpoints logic for the logged-in student: profile,
enrolled classes, attendance summary/daily records, assignment results,
exam results, fees. Ported from legacy `app/routers/student_routers.py`.

Key schema difference from legacy: `StudentClass.student_id` here is the
student's `users.id` (integer), not the string `student_profiles.student_id`
business code — so lookups filter by `current_user.id` directly instead of
resolving through a business-id string first.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ResourceNotFoundException
from src.core.logger import get_logger
from src.domain.assignments.models import Assignment, AssignmentResult
from src.domain.exams.models import Exam, ExamResult
from src.domain.fees.models import Fee
from src.domain.operations.models import (
    DailyClassStudent,
    StudentAttendance,
    StudentClass,
)
from src.domain.users.models import StudentProfile

logger = get_logger(__name__)


class StudentSelfService:
    @staticmethod
    async def _get_profile(db: AsyncSession, user_id: int) -> StudentProfile:
        profile = await db.scalar(select(StudentProfile).filter_by(user_id=user_id))
        if not profile:
            raise ResourceNotFoundException("Student profile not found")
        return profile

    @staticmethod
    async def _get_enrollment(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int,
    ) -> StudentClass:
        enrollment = await db.scalar(
            select(StudentClass).filter_by(
                student_id=user_id,
                academic_sessions_id=academic_sessions_id,
            ),
        )
        if not enrollment:
            enrollment = await db.scalar(
                select(StudentClass)
                .filter_by(student_id=user_id)
                .order_by(StudentClass.academic_sessions_id.desc()),
            )
        if not enrollment:
            raise ResourceNotFoundException("Student not enrolled in any session")
        return enrollment

    @staticmethod
    async def get_profile(db: AsyncSession, user_id: int) -> StudentProfile:
        return await StudentSelfService._get_profile(db, user_id)

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user_id: int,
        data: dict[str, Any],
    ) -> StudentProfile:
        profile = await StudentSelfService._get_profile(db, user_id)
        for key, value in data.items():
            setattr(profile, key, value)
        profile.updated_by = user_id
        await db.flush()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def get_classes(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int | None = None,
    ) -> list[StudentClass]:
        query = select(StudentClass).filter(StudentClass.student_id == user_id)
        if academic_sessions_id:
            query = query.filter(
                StudentClass.academic_sessions_id == academic_sessions_id,
            )
        query = query.order_by(StudentClass.academic_sessions_id.desc())
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_attendance_summary(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int,
    ) -> StudentAttendance:
        enrollment = await StudentSelfService._get_enrollment(
            db,
            user_id,
            academic_sessions_id,
        )

        attendance = await db.scalar(
            select(StudentAttendance).filter_by(student_class_id=enrollment.id),
        )
        if not attendance:
            attendance = StudentAttendance(
                student_class_id=enrollment.id,
                total_classes=0,
                present_classes=0,
                absent_classes=0,
                attendance_percentage=0.0,
            )
            db.add(attendance)
            await db.flush()
            await db.refresh(attendance)
        return attendance

    @staticmethod
    async def get_daily_attendance(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        from src.domain.operations.models import DailyClass, ClassTimeTable, TimeSlot

        enrollment = await StudentSelfService._get_enrollment(
            db,
            user_id,
            academic_sessions_id,
        )

        # Join: DailyClassStudent -> DailyClass to filter by class_date
        query = (
            select(DailyClassStudent, DailyClass.class_date, DailyClass.timetable_id)
            .join(DailyClass, DailyClassStudent.daily_class_id == DailyClass.id)
            .filter(DailyClassStudent.student_class_id == enrollment.id)
        )
        if start_date:
            query = query.filter(DailyClass.class_date >= start_date)
        if end_date:
            query = query.filter(DailyClass.class_date <= end_date)
        query = query.order_by(DailyClass.class_date.desc())
        rows = (await db.execute(query)).all()

        # Collect unique timetable_ids and resolve time slots in one query
        tt_ids = list({tt_id for _, _, tt_id in rows if tt_id})
        slot_map = {}
        if tt_ids:
            tts = (
                await db.execute(
                    select(ClassTimeTable.id, ClassTimeTable.time_slot_id)
                    .filter(ClassTimeTable.id.in_(tt_ids))
                )
            ).all()
            slot_ids = list({t.time_slot_id for t in tts})
            if slot_ids:
                slots = (
                    await db.execute(
                        select(TimeSlot.id, TimeSlot.slot_name)
                        .filter(TimeSlot.id.in_(slot_ids))
                    )
                ).all()
                slot_name_map = {s.id: s.slot_name for s in slots}
                for t in tts:
                    slot_map[t.id] = slot_name_map.get(t.time_slot_id, "—")

        results = []
        for r, class_date, timetable_id in rows:
            period_name = slot_map.get(timetable_id, "—") if timetable_id else "—"
            results.append({
                "date": class_date,
                "daily_class_id": r.daily_class_id,
                "status": r.attendance_status,
                "is_late": r.is_late,
                "late_minutes": r.late_minutes,
                "remarks": r.remarks,
                "period": period_name,
            })
        return results

    @staticmethod
    async def get_assignment_results(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int,
        subject_id: int | None = None,
    ) -> list[AssignmentResult]:
        enrollment = await StudentSelfService._get_enrollment(
            db,
            user_id,
            academic_sessions_id,
        )

        query = select(AssignmentResult).filter(
            AssignmentResult.student_class_id == enrollment.id,
        )
        if subject_id:
            query = query.join(Assignment).filter(
                Assignment.class_subject_id == subject_id,
            )
        query = query.order_by(AssignmentResult.created_at.desc())
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_exam_results(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int,
        subject_id: int | None = None,
    ) -> list[ExamResult]:
        enrollment = await StudentSelfService._get_enrollment(
            db,
            user_id,
            academic_sessions_id,
        )

        query = select(ExamResult).filter(ExamResult.student_class_id == enrollment.id)
        if subject_id:
            query = query.join(Exam).filter(Exam.class_subject_id == subject_id)
        query = query.order_by(ExamResult.created_at.desc())
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_fees(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int,
        fee_status: str | None = None,
    ) -> list[Fee]:
        enrollment = await StudentSelfService._get_enrollment(
            db,
            user_id,
            academic_sessions_id,
        )

        query = select(Fee).filter(Fee.student_class_id == enrollment.id)
        if fee_status:
            query = query.filter(Fee.status == fee_status)
        query = query.order_by(Fee.fee_year.desc(), Fee.fee_month.desc())
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_fee_summary(
        db: AsyncSession,
        user_id: int,
        academic_sessions_id: int,
    ) -> dict[str, Any]:
        enrollment = await StudentSelfService._get_enrollment(
            db,
            user_id,
            academic_sessions_id,
        )

        query = select(Fee).filter(Fee.student_class_id == enrollment.id)
        fees = list((await db.execute(query)).scalars().all())

        total_amount = sum((f.total_amount for f in fees), start=0)
        paid_amount = sum((f.paid_amount for f in fees), start=0)
        pending_amount = total_amount - paid_amount

        return {
            "total_amount": float(total_amount),
            "paid_amount": float(paid_amount),
            "pending_amount": float(pending_amount),
            "status": "Paid" if pending_amount == 0 else "Pending",
        }
