"""DashboardService

Cross-domain aggregate summaries for student/teacher/admin landing pages.
Ported from legacy `app/routers/dashboard_routers.py` (the active,
non-commented-out half of that file — the top block referencing
AlumnusDetail/SubjectProgress/AssignmentSubmission was already fully
commented out in the legacy source and referenced tables that don't exist
in this schema, so it is intentionally not revived here).
"""

from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import AssignmentStatus, ExamStatus
from src.core.exceptions import ResourceNotFoundException
from src.domain.academics.models import AcademicSession, ClassRoom, Subject
from src.domain.assignments.models import Assignment
from src.domain.exams.models import Exam
from src.domain.fees.models import Fee
from src.domain.notices.models import Notice
from src.domain.operations.models import (
    DailyClass,
    StudentAttendance,
    StudentClass,
    TeacherSubject,
)
from src.domain.users.models import StudentProfile, TeacherProfile, User


class DashboardService:
    @staticmethod
    async def _get_current_session(db: AsyncSession) -> AcademicSession:
        session = await db.scalar(select(AcademicSession).filter_by(is_current=True))
        if not session:
            raise ResourceNotFoundException("No current academic session found")
        return session

    @staticmethod
    async def get_student_dashboard(db: AsyncSession, user_id: int) -> dict[str, Any]:
        student = await db.scalar(select(StudentProfile).filter_by(user_id=user_id))
        if not student:
            raise ResourceNotFoundException("Student profile not found")

        current_session = await DashboardService._get_current_session(db)

        student_class = await db.scalar(
            select(StudentClass).filter_by(
                student_id=user_id,
                academic_sessions_id=current_session.id,
            ),
        )
        if not student_class:
            raise ResourceNotFoundException("Student not enrolled in current session")

        attendance = await db.scalar(
            select(StudentAttendance).filter_by(student_class_id=student_class.id),
        )

        upcoming_assignments = list(
            (
                await db.execute(
                    select(Assignment)
                    .filter(
                        Assignment.classroom_id == student_class.classroom_id,
                        Assignment.due_date >= date.today(),
                        Assignment.status.in_(
                            [AssignmentStatus.PUBLISHED, AssignmentStatus.DRAFT],
                        ),
                    )
                    .order_by(Assignment.due_date)
                    .limit(5),
                )
            )
            .scalars()
            .all(),
        )

        upcoming_exams = list(
            (
                await db.execute(
                    select(Exam)
                    .filter(
                        Exam.classroom_id == student_class.classroom_id,
                        Exam.exam_date >= date.today(),
                        Exam.status.in_([ExamStatus.PUBLISHED, ExamStatus.DRAFT]),
                    )
                    .order_by(Exam.exam_date)
                    .limit(5),
                )
            )
            .scalars()
            .all(),
        )

        fees = list(
            (await db.execute(select(Fee).filter_by(student_class_id=student_class.id)))
            .scalars()
            .all(),
        )
        total_fee = sum((f.total_amount for f in fees), start=0)
        paid_fee = sum((f.paid_amount for f in fees), start=0)

        classroom = await db.get(ClassRoom, student_class.classroom_id)

        return {
            "student": {
                "name": student.student_name,
                # NOTE: fixed from the ported version, which referenced a
                # non-existent `StudentProfile.student_id` attribute (that
                # field lives on User, not StudentProfile, and is never
                # populated). admission_number is the actual populated
                # business identifier on the profile itself.
                "student_id": student.admission_number,
                "class": classroom.display_name if classroom else "",
                "roll_number": student_class.roll_number,
            },
            "attendance": {
                "total_classes": attendance.total_classes if attendance else 0,
                "present": attendance.present_classes if attendance else 0,
                "percentage": attendance.attendance_percentage if attendance else 0,
            },
            "upcoming_assignments": [
                {
                    "id": a.id,
                    "title": a.title,
                    "due_date": a.due_date,
                    "status": a.status,
                }
                for a in upcoming_assignments
            ],
            "upcoming_exams": [
                {
                    "id": e.id,
                    "exam_name": e.exam_name,
                    "exam_date": e.exam_date,
                    "status": e.status,
                }
                for e in upcoming_exams
            ],
            "fees": {
                "total": float(total_fee),
                "paid": float(paid_fee),
                "pending": float(total_fee - paid_fee),
            },
        }

    @staticmethod
    async def get_teacher_dashboard(db: AsyncSession, user_id: int) -> dict[str, Any]:
        teacher = await db.scalar(select(TeacherProfile).filter_by(user_id=user_id))
        if not teacher:
            raise ResourceNotFoundException("Teacher profile not found")

        current_session = await DashboardService._get_current_session(db)

        teacher_subjects = list(
            (
                await db.execute(
                    select(TeacherSubject).filter_by(
                        teacher_id=user_id,
                        academic_sessions_id=current_session.id,
                    ),
                )
            )
            .scalars()
            .all(),
        )
        class_ids = [ts.classroom_id for ts in teacher_subjects]
        teacher_subject_ids = [ts.id for ts in teacher_subjects]

        today = date.today()
        today_classes = (
            await db.scalar(
                select(func.count())
                .select_from(DailyClass)
                .filter(
                    DailyClass.teacher_subject_id.in_(teacher_subject_ids),
                    DailyClass.class_date == today,
                ),
            )
            or 0
        )

        total_students = (
            await db.scalar(
                select(func.count())
                .select_from(StudentClass)
                .filter(
                    StudentClass.classroom_id.in_(class_ids),
                    StudentClass.academic_sessions_id == current_session.id,
                    StudentClass.status == "ACTIVE",
                ),
            )
            or 0
        )

        pending_assignments = (
            await db.scalar(
                select(func.count())
                .select_from(Assignment)
                .filter(
                    Assignment.teacher_subject_id.in_(teacher_subject_ids),
                    Assignment.status == AssignmentStatus.DRAFT,
                ),
            )
            or 0
        )

        upcoming_exams = (
            await db.scalar(
                select(func.count())
                .select_from(Exam)
                .filter(
                    Exam.teacher_subject_id.in_(teacher_subject_ids),
                    Exam.exam_date >= date.today(),
                    Exam.status.in_([ExamStatus.PUBLISHED, ExamStatus.DRAFT]),
                ),
            )
            or 0
        )

        last_7_days_classes = (
            await db.scalar(
                select(func.count())
                .select_from(DailyClass)
                .filter(
                    DailyClass.teacher_subject_id.in_(teacher_subject_ids),
                    DailyClass.class_date >= today - timedelta(days=7),
                ),
            )
            or 0
        )

        return {
            "teacher": {
                "name": teacher.teacher_name,
                # NOTE: fixed for the same reason as the student dashboard
                # above -- TeacherProfile has no `teacher_id` column;
                # employee_code is the real business identifier here.
                "teacher_id": teacher.employee_code,
                "designation": teacher.designation,
            },
            "summary": {
                "total_classes": len(class_ids),
                "total_students": total_students,
                "today_classes": today_classes,
                "pending_assignments": pending_assignments,
                "upcoming_exams": upcoming_exams,
            },
            "recent_activity": {"last_7_days_classes": last_7_days_classes},
        }

    @staticmethod
    async def get_admin_dashboard(db: AsyncSession) -> dict[str, Any]:
        current_session = await db.scalar(
            select(AcademicSession).filter_by(is_current=True),
        )

        total_users = (
            await db.scalar(
                select(func.count()).select_from(User).filter(not User.is_deleted),
            )
            or 0
        )
        total_students = (
            await db.scalar(
                select(func.count())
                .select_from(StudentProfile)
                .filter(StudentProfile.is_active),
            )
            or 0
        )
        total_teachers = (
            await db.scalar(
                select(func.count())
                .select_from(TeacherProfile)
                .filter(TeacherProfile.is_active),
            )
            or 0
        )
        total_classes = (
            await db.scalar(
                select(func.count()).select_from(ClassRoom).filter(ClassRoom.is_active),
            )
            or 0
        )
        total_subjects = (
            await db.scalar(
                select(func.count()).select_from(Subject).filter(Subject.is_active),
            )
            or 0
        )

        if current_session:
            session_classes = (
                await db.scalar(
                    select(func.count())
                    .select_from(ClassRoom)
                    .filter(ClassRoom.academic_sessions_id == current_session.id),
                )
                or 0
            )
            session_students = (
                await db.scalar(
                    select(func.count())
                    .select_from(StudentClass)
                    .filter(
                        StudentClass.academic_sessions_id == current_session.id,
                        StudentClass.status == "ACTIVE",
                    ),
                )
                or 0
            )
        else:
            session_classes = 0
            session_students = 0

        recent_users = list(
            (await db.execute(select(User).order_by(User.created_at.desc()).limit(5)))
            .scalars()
            .all(),
        )
        recent_notices = list(
            (
                await db.execute(
                    select(Notice).order_by(Notice.created_at.desc()).limit(5),
                )
            )
            .scalars()
            .all(),
        )

        return {
            "system": {
                "total_user": total_users,
                "total_students": total_students,
                "total_teachers": total_teachers,
                "total_classes": total_classes,
                "total_subjects": total_subjects,
            },
            "current_session": {
                "session_name": current_session.session_name
                if current_session
                else "None",
                "total_classes": session_classes,
                "total_students": session_students,
            },
            "recent_activity": {
                "recent_user": [
                    {
                        "id": u.id,
                        "email": u.email,
                        "role": u.role,
                        "created_at": u.created_at,
                    }
                    for u in recent_users
                ],
                "recent_notices": [
                    {"id": n.id, "title": n.title, "created_at": n.created_at}
                    for n in recent_notices
                ],
            },
        }
