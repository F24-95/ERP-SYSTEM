"""DashboardService

Cross-domain aggregate summaries for student/teacher/admin landing pages.
Ported from legacy `app/routers/dashboard_routers.py`.

Optimized with:
- Grouped SQL aggregations eliminating N+1 queries.
- Database-level SUM / AVG calculations (func.sum, func.avg, func.coalesce).
- Correct boolean column expression filters (User.is_deleted.is_(False)).
- Consolidated imports at module level.
"""

from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import AssignmentStatus, ExamStatus
from src.core.exceptions import ResourceNotFoundException
from src.domain.academics.models import AcademicSession, ClassRoom, ClassSubject
from src.domain.assignments.models import Assignment
from src.domain.curriculum.models import Subject
from src.domain.exam_engine.service import ExamEngineIntegrationService
from src.domain.exams.models import Exam, ExamResult
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
    async def _session_fee_summary(
        db: AsyncSession,
        session_id: int,
    ) -> tuple[float, float]:
        """Aggregate total and collected fees for a given academic session using SQL."""
        stmt = (
            select(
                func.coalesce(func.sum(Fee.total_amount), 0),
                func.coalesce(func.sum(Fee.paid_amount), 0),
            )
            .join(StudentClass, Fee.student_class_id == StudentClass.id)
            .filter(StudentClass.academic_sessions_id == session_id)
        )
        res = await db.execute(stmt)
        total_fee, paid_fee = res.first() or (0, 0)
        return float(total_fee), float(paid_fee)

    # =================================================================
    # Admin ERP Summary — class-wise stats + school-wide overview
    # =================================================================

    @staticmethod
    async def get_admin_overview(
        db: AsyncSession,
        session_id: int | None = None,
    ) -> dict[str, Any]:
        """School-wide overview for the ERP Summary page. Returns total
        students, teachers, classes, subjects, fees collected/pending, and
        overall attendance percentage for the given (or current) session.
        """
        if session_id:
            session = await db.get(AcademicSession, session_id)
        else:
            session = await db.scalar(select(AcademicSession).filter_by(is_current=True))

        total_students = (
            await db.scalar(
                select(func.count()).select_from(StudentProfile).filter(StudentProfile.is_active),
            )
            or 0
        )
        total_teachers = (
            await db.scalar(
                select(func.count()).select_from(TeacherProfile).filter(TeacherProfile.is_active),
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

        # Session-scoped stats
        session_students = 0
        total_fees = 0.0
        paid_fees = 0.0
        total_attendance_classes = 0
        total_attendance_present = 0

        if session:
            session_students = (
                await db.scalar(
                    select(func.count())
                    .select_from(StudentClass)
                    .filter(
                        StudentClass.academic_sessions_id == session.id,
                        StudentClass.status == "ACTIVE",
                    ),
                )
                or 0
            )

            total_fees, paid_fees = await DashboardService._session_fee_summary(
                db, session.id,
            )

            # Attendance across all students in session via SQL aggregation
            att_stmt = (
                select(
                    func.coalesce(func.sum(StudentAttendance.total_classes), 0),
                    func.coalesce(func.sum(StudentAttendance.present_classes), 0),
                )
                .join(StudentClass, StudentAttendance.student_class_id == StudentClass.id)
                .filter(StudentClass.academic_sessions_id == session.id)
            )
            att_res = await db.execute(att_stmt)
            tot_cls, tot_pres = att_res.first() or (0, 0)
            total_attendance_classes = int(tot_cls)
            total_attendance_present = int(tot_pres)

        overall_attendance = (
            round(total_attendance_present / total_attendance_classes * 100, 1)
            if total_attendance_classes > 0
            else 0
        )

        return {
            "session_name": session.session_name if session else "None",
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_classes": total_classes,
            "total_subjects": total_subjects,
            "session_students": session_students,
            "fees": {
                "total": round(total_fees, 2),
                "collected": round(paid_fees, 2),
                "pending": round(total_fees - paid_fees, 2),
            },
            "attendance": {
                "total_classes": total_attendance_classes,
                "present": total_attendance_present,
                "overall_percentage": overall_attendance,
            },
        }

    @staticmethod
    async def get_admin_class_stats(
        db: AsyncSession,
        session_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Per-class breakdown: student count, avg attendance, avg exam
        marks, fee total/collected/pending for each classroom in the
        given (or current) session. (Optimized with grouped SQL aggregations).
        """
        if session_id:
            session = await db.get(AcademicSession, session_id)
        else:
            session = await db.scalar(select(AcademicSession).filter_by(is_current=True))

        if not session:
            return []

        classrooms = list(
            (
                await db.execute(
                    select(ClassRoom).filter_by(
                        academic_sessions_id=session.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        if not classrooms:
            return []

        # 1. Student count per class
        st_count_stmt = (
            select(StudentClass.classroom_id, func.count(StudentClass.id))
            .filter(
                StudentClass.academic_sessions_id == session.id,
                StudentClass.status == "ACTIVE",
            )
            .group_by(StudentClass.classroom_id)
        )
        st_counts = dict((await db.execute(st_count_stmt)).all())

        # 2. Attendance per class
        att_stmt = (
            select(
                StudentClass.classroom_id,
                func.coalesce(func.sum(StudentAttendance.total_classes), 0),
                func.coalesce(func.sum(StudentAttendance.present_classes), 0),
            )
            .join(StudentAttendance, StudentAttendance.student_class_id == StudentClass.id)
            .filter(
                StudentClass.academic_sessions_id == session.id,
                StudentClass.status == "ACTIVE",
            )
            .group_by(StudentClass.classroom_id)
        )
        att_rows = (await db.execute(att_stmt)).all()
        att_map = {
            cid: round(float(pres) / float(tot) * 100, 1) if tot > 0 else 0
            for cid, tot, pres in att_rows
        }

        # 3. Exam results per class
        exam_stmt = (
            select(
                StudentClass.classroom_id,
                func.count(ExamResult.id),
                func.coalesce(func.avg(ExamResult.percentage), 0),
            )
            .join(ExamResult, ExamResult.student_class_id == StudentClass.id)
            .filter(
                StudentClass.academic_sessions_id == session.id,
                ExamResult.is_absent.is_(False),
            )
            .group_by(StudentClass.classroom_id)
        )
        exam_rows = (await db.execute(exam_stmt)).all()
        exam_map = {
            cid: (int(cnt), round(float(avg_p), 1))
            for cid, cnt, avg_p in exam_rows
        }

        # 4. Fees per class
        fee_stmt = (
            select(
                StudentClass.classroom_id,
                func.coalesce(func.sum(Fee.total_amount), 0),
                func.coalesce(func.sum(Fee.paid_amount), 0),
            )
            .join(Fee, Fee.student_class_id == StudentClass.id)
            .filter(StudentClass.academic_sessions_id == session.id)
            .group_by(StudentClass.classroom_id)
        )
        fee_rows = (await db.execute(fee_stmt)).all()
        fee_map = {
            cid: (float(tot), float(paid))
            for cid, tot, paid in fee_rows
        }

        result = []
        for cr in classrooms:
            student_count = st_counts.get(cr.id, 0)
            avg_attendance = att_map.get(cr.id, 0)
            exam_count, avg_exam_marks = exam_map.get(cr.id, (0, 0))
            total_fee, paid_fee = fee_map.get(cr.id, (0.0, 0.0))

            result.append({
                "classroom_id": cr.id,
                "class_name": cr.display_name,
                "student_count": student_count,
                "avg_attendance": avg_attendance,
                "avg_exam_marks": avg_exam_marks,
                "exam_count": exam_count,
                "fees_total": round(total_fee, 2),
                "fees_collected": round(paid_fee, 2),
                "fees_pending": round(total_fee - paid_fee, 2),
            })

        return result

    @staticmethod
    async def get_student_dashboard(
        db: AsyncSession,
        user_id: int,
    ) -> dict[str, Any]:
        student = await db.scalar(select(StudentProfile).filter_by(user_id=user_id))
        if not student:
            raise ResourceNotFoundException("Student profile not found")

        current_session = await db.scalar(
            select(AcademicSession).filter_by(is_current=True),
        )

        student_class = None
        if current_session:
            student_class = await db.scalar(
                select(StudentClass).filter_by(
                    student_id=user_id,
                    academic_sessions_id=current_session.id,
                ),
            )
        if not student_class:
            student_class = await db.scalar(
                select(StudentClass)
                .filter_by(student_id=user_id)
                .order_by(StudentClass.academic_sessions_id.desc()),
            )
        if not student_class:
            raise ResourceNotFoundException(
                "Student is not enrolled in any session",
            )

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
    async def get_teacher_dashboard(
        db: AsyncSession,
        user_id: int,
    ) -> dict[str, Any]:
        teacher = await db.scalar(select(TeacherProfile).filter_by(user_id=user_id))
        if not teacher:
            raise ResourceNotFoundException("Teacher profile not found")

        current_session = await db.scalar(
            select(AcademicSession).filter_by(is_current=True),
        )

        teacher_subjects = []
        if current_session:
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
        if not teacher_subjects:
            last_session_id = await db.scalar(
                select(TeacherSubject.academic_sessions_id)
                .filter_by(teacher_id=user_id)
                .order_by(TeacherSubject.academic_sessions_id.desc())
                .limit(1),
            )
            if last_session_id:
                teacher_subjects = list(
                    (
                        await db.execute(
                            select(TeacherSubject).filter_by(
                                teacher_id=user_id,
                                academic_sessions_id=last_session_id,
                            ),
                        )
                    )
                    .scalars()
                    .all(),
                )

        # Assigned classes
        class_subject_ids = [ts.class_subject_id for ts in teacher_subjects]
        classrooms_data = []
        if class_subject_ids:
            class_subjects = list(
                (
                    await db.execute(
                        select(ClassSubject).filter(
                            ClassSubject.id.in_(class_subject_ids),
                        ),
                    )
                )
                .scalars()
                .all(),
            )
            for cs in class_subjects:
                cr = await db.get(ClassRoom, cs.classroom_id)
                subj = await db.get(Subject, cs.subject_id)
                if cr and subj:
                    classrooms_data.append(
                        {
                            "class_subject_id": cs.id,
                            "classroom": cr.display_name,
                            "subject": subj.subject_name,
                        },
                    )

        # Pending assignments to grade
        pending_assignments = list(
            (
                await db.execute(
                    select(Assignment)
                    .filter_by(created_by=user_id)
                    .order_by(Assignment.due_date.desc())
                    .limit(5),
                )
            )
            .scalars()
            .all(),
        )

        # Today's daily classes
        todays_classes = list(
            (
                await db.execute(
                    select(DailyClass).filter_by(
                        teacher_id=user_id,
                        class_date=date.today(),
                    ),
                )
            )
            .scalars()
            .all(),
        )

        return {
            "teacher": {
                "name": teacher.teacher_name,
                "employee_code": teacher.employee_code,
                "department": teacher.department,
            },
            "assigned_classes": classrooms_data,
            "todays_classes": [
                {
                    "id": dc.id,
                    "date": dc.class_date,
                    "status": dc.status,
                    "remarks": dc.remarks,
                }
                for dc in todays_classes
            ],
            "recent_assignments": [
                {
                    "id": a.id,
                    "title": a.title,
                    "due_date": a.due_date,
                    "status": a.status,
                }
                for a in pending_assignments
            ],
        }

    @staticmethod
    async def get_teacher_class_analytics(
        db: AsyncSession,
        user_id: int,
        classroom_id: int | None = None,
        academic_sessions_id: int | None = None,
    ) -> dict[str, Any]:
        teacher = await db.scalar(select(TeacherProfile).filter_by(user_id=user_id))
        if not teacher:
            raise ResourceNotFoundException("Teacher profile not found")

        current_session = (
            await db.get(AcademicSession, academic_sessions_id)
            if academic_sessions_id
            else await db.scalar(select(AcademicSession).filter_by(is_current=True))
        )

        # Get all teacher's class subjects in current session
        ts_query = select(TeacherSubject)
        if current_session:
            ts_query = ts_query.filter_by(
                teacher_id=user_id,
                academic_sessions_id=current_session.id,
            )
        else:
            ts_query = ts_query.filter_by(teacher_id=user_id)

        teacher_subjects = list((await db.execute(ts_query)).scalars().all())
        if not teacher_subjects:
            return {
                "overview": {
                    "total_classes_assigned": 0,
                    "total_students": 0,
                    "avg_attendance": 0,
                },
                "classes": [],
                "recent_activity": {"last_7_days_classes": 0},
            }

        class_subject_ids = [ts.class_subject_id for ts in teacher_subjects]
        cs_query = select(ClassSubject).filter(
            ClassSubject.id.in_(class_subject_ids),
        )
        if classroom_id:
            cs_query = cs_query.filter_by(classroom_id=classroom_id)

        class_subjects = list((await db.execute(cs_query)).scalars().all())

        classes_data = []
        all_student_ids = set()
        total_attendance_pcts = []

        for cs in class_subjects:
            cr = await db.get(ClassRoom, cs.classroom_id)
            subj = await db.get(Subject, cs.subject_id)
            if not cr or not subj:
                continue

            # Student count in this classroom
            sc_query = select(StudentClass).filter_by(
                classroom_id=cr.id,
                status="ACTIVE",
            )
            if current_session:
                sc_query = sc_query.filter_by(
                    academic_sessions_id=current_session.id,
                )
            students = list((await db.execute(sc_query)).scalars().all())
            student_ids = [s.student_id for s in students]
            all_student_ids.update(student_ids)

            # Attendance for these students
            att_query = select(StudentAttendance).filter(
                StudentAttendance.student_class_id.in_([s.id for s in students]),
            )
            attendances = list((await db.execute(att_query)).scalars().all())
            avg_att = (
                sum(a.attendance_percentage for a in attendances) / len(attendances)
                if attendances
                else 0
            )
            if attendances:
                total_attendance_pcts.extend(
                    [a.attendance_percentage for a in attendances],
                )

            # Assignments created for this class
            ass_count = await db.scalar(
                select(func.count(Assignment.id)).filter_by(
                    classroom_id=cr.id,
                    created_by=user_id,
                ),
            )

            # Daily classes logged
            dc_count = await db.scalar(
                select(func.count(DailyClass.id)).filter_by(
                    classroom_id=cr.id,
                    teacher_id=user_id,
                ),
            )

            classes_data.append(
                {
                    "class_subject_id": cs.id,
                    "classroom_id": cr.id,
                    "classroom_name": cr.display_name,
                    "subject_name": subj.subject_name,
                    "student_count": len(students),
                    "avg_attendance": round(avg_att, 1),
                    "assignments_created": ass_count or 0,
                    "classes_logged": dc_count or 0,
                },
            )

        # Recent daily classes (last 7 days)
        seven_days_ago = date.today() - timedelta(days=7)
        last_7_days_classes = (
            await db.scalar(
                select(func.count(DailyClass.id)).filter(
                    DailyClass.teacher_id == user_id,
                    DailyClass.class_date >= seven_days_ago,
                ),
            )
            or 0
        )

        avg_overall_att = (
            sum(total_attendance_pcts) / len(total_attendance_pcts)
            if total_attendance_pcts
            else 0
        )

        return {
            "overview": {
                "total_classes_assigned": len(class_subjects),
                "total_students": len(all_student_ids),
                "avg_attendance": round(avg_overall_att, 1),
            },
            "classes": classes_data,
            "recent_activity": {"last_7_days_classes": last_7_days_classes},
        }

    @staticmethod
    async def get_admin_dashboard(db: AsyncSession) -> dict[str, Any]:
        current_session = await db.scalar(
            select(AcademicSession).filter_by(is_current=True),
        )

        total_users = (
            await db.scalar(
                select(func.count()).select_from(User).filter(User.is_deleted.is_(False)),
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
                    .filter(
                        ClassRoom.academic_sessions_id == current_session.id,
                    ),
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
            total_fees, paid_fees = await DashboardService._session_fee_summary(
                db, current_session.id,
            )
        else:
            session_classes = 0
            session_students = 0
            total_fees = 0.0
            paid_fees = 0.0

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

        exam_engine = await ExamEngineIntegrationService.get_dashboard_summary(db)

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
            "fees": {
                "total": round(total_fees, 2),
                "collected": round(paid_fees, 2),
                "pending": round(total_fees - paid_fees, 2),
            },
            "exam_engine": exam_engine,
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
