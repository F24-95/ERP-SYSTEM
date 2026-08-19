import io
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.enums import UserRole
from src.core.exceptions import (
    AuthorizationException,
    BusinessLogicException,
    ResourceNotFoundException,
)
from src.core.logger import get_logger
from src.domain.curriculum.models import Subject, Topic
from src.domain.khan_academy.models import KaSubjectProgress, KaTopicProgress
from src.domain.reports.crud import (
    student_activity_report_crud,
    student_report_crud,
    student_subject_progress_report_crud,
    student_topic_progress_report_crud,
    zoom_duration_report_crud,
    zoom_interaction_report_crud,
)
from src.domain.reports.models import (
    StudentReport,
    StudentSubjectProgressReport,
    StudentTopicProgressReport,
)
from src.domain.users.models import StudentProfile, User

logger = get_logger(__name__)


def _build_empty_report(profile: StudentProfile, student_profile_id: int) -> dict:
    """Return a zero-data report for students with no enrollment."""
    gender_val = None
    try:
        if profile.gender:
            gender_val = profile.gender.value if hasattr(profile.gender, 'value') else str(profile.gender)
    except Exception:
        gender_val = None

    return {
        "student": {
            "profile_id": profile.id,
            "user_id": profile.user_id,
            "name": getattr(profile, 'student_name', None) or "—",
            "admission_number": getattr(profile, 'admission_number', None),
            "registration_number": getattr(profile, 'registration_number', None),
            "gender": gender_val,
            "date_of_birth": str(profile.date_of_birth) if profile.date_of_birth else None,
            "parent_name": getattr(profile, 'parent_name', None),
            "parent_phone": getattr(profile, 'parent_phone', None),
            "address": getattr(profile, 'address', None),
        },
        "enrollment": {"classroom_id": None, "class_name": None, "roll_number": None, "status": None, "academic_session": None},
        "attendance": {"total_classes": 0, "present": 0, "absent": 0, "percentage": 0},
        "subjects": [],
        "exams": [],
        "assignments": [],
        "fees": {"total": 0, "paid": 0, "pending": 0, "records": []},
    }


def _build_full_report_dict(
    profile: StudentProfile,
    enrollment,
    classroom,
    attendance,
    subjects: list,
    exam_results: list,
    assignment_results: list,
    fees: list,
    session_name: str | None = None,
) -> dict:
    """Compose the full student report payload from pre-fetched data."""

    total_fee = 0.0
    paid_fee = 0.0
    fee_records = []
    try:
        total_fee = sum((float(getattr(f, 'total_amount', 0) or 0) for f in fees), 0.0)
        paid_fee = sum((float(getattr(f, 'paid_amount', 0) or 0) for f in fees), 0.0)
        fee_records = [
            {
                "id": getattr(f, 'id', 0),
                "month": getattr(f, 'fee_month', 0),
                "year": getattr(f, 'fee_year', 0),
                "total": float(getattr(f, 'total_amount', 0) or 0),
                "paid": float(getattr(f, 'paid_amount', 0) or 0),
                "status": getattr(f, 'status', 'UNKNOWN'),
                "due_date": str(getattr(f, 'due_date', '')) if getattr(f, 'due_date', None) else None,
            }
            for f in fees
        ]
    except Exception:
        pass

    gender_val = None
    try:
        if profile.gender:
            gender_val = profile.gender.value if hasattr(profile.gender, 'value') else str(profile.gender)
    except Exception:
        gender_val = None

    dob_val = None
    try:
        if profile.date_of_birth:
            dob_val = str(profile.date_of_birth)
    except Exception:
        dob_val = None

    return {
        "student": {
            "profile_id": profile.id,
            "user_id": profile.user_id,
            "name": getattr(profile, 'student_name', None) or "—",
            "admission_number": getattr(profile, 'admission_number', None),
            "registration_number": getattr(profile, 'registration_number', None),
            "gender": gender_val,
            "date_of_birth": dob_val,
            "parent_name": getattr(profile, 'parent_name', None),
            "parent_phone": getattr(profile, 'parent_phone', None),
            "address": getattr(profile, 'address', None),
        },
        "enrollment": {
            "classroom_id": getattr(enrollment, 'classroom_id', None),
            "class_name": getattr(classroom, 'display_name', None) if classroom else None,
            "roll_number": getattr(enrollment, 'roll_number', None),
            "status": getattr(enrollment, 'status', None),
            "academic_session": session_name,
        },
        "attendance": {
            "total_classes": getattr(attendance, 'total_classes', 0) or 0,
            "present": getattr(attendance, 'present_classes', 0) or 0,
            "absent": getattr(attendance, 'absent_classes', 0) or 0,
            "percentage": round(getattr(attendance, 'attendance_percentage', 0) or 0, 1),
        },
        "subjects": subjects or [],
        "exams": exam_results or [],
        "assignments": assignment_results or [],
        "fees": {
            "total": round(total_fee, 2),
            "paid": round(paid_fee, 2),
            "pending": round(total_fee - paid_fee, 2),
            "records": fee_records,
        },
    }


def _render_report_pdf(
    student_name: str,
    data_start_date: date,
    data_end_date: date,
    subject_rows: list,
    topic_rows: list,
) -> bytes:
    """Minimal progress-report PDF. There's no legacy report template to
    port (this feature is new to this project), so this renders a plain
    summary table rather than inventing a specific design without a spec to
    follow. Falls back to a text placeholder if reportlab isn't usable, same
    fallback pattern used in id_cards/generators.py.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        y = height - 50

        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, y, f"Progress Report: {student_name}")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(
            40,
            y,
            f"Period: {data_start_date.isoformat()} to {data_end_date.isoformat()}",
        )
        y -= 30

        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Subject Progress")
        y -= 18
        c.setFont("Helvetica", 10)
        for row in subject_rows:
            c.drawString(
                50,
                y,
                f"{row['subject_name']}: {row['point_earned']}/{row['point_available']} ({row['percentage_earned']:.1f}%)",
            )
            y -= 14
            if y < 60:
                c.showPage()
                y = height - 50

        y -= 16
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Topic Progress")
        y -= 18
        c.setFont("Helvetica", 10)
        for row in topic_rows:
            c.drawString(
                50,
                y,
                f"{row['topic_name']}: {row['point_earned']}/{row['point_available']} ({row['percentage_earned']:.1f}%)",
            )
            y -= 14
            if y < 60:
                c.showPage()
                y = height - 50

        c.showPage()
        c.save()
        return buf.getvalue()
    except Exception:
        text = f"Progress Report: {student_name}\nPeriod: {data_start_date} to {data_end_date}\nSubjects: {subject_rows}\nTopics: {topic_rows}"
        return text.encode("utf-8")


class StudentReportService:
    @staticmethod
    async def _check_view_access(
        db: AsyncSession,
        student_profile_id: int,
        current_user: User,
    ) -> None:
        if current_user.role == UserRole.STUDENT:
            own_profile = await db.scalar(
                select(StudentProfile).filter_by(user_id=current_user.id),
            )
            if not own_profile or own_profile.id != student_profile_id:
                raise AuthorizationException("You can only access your own reports")

    @staticmethod
    async def generate_report(
        db: AsyncSession,
        student_profile_id: int,
        data_start_date: date,
        data_end_date: date,
        current_user: User,
    ) -> StudentReport:
        if data_end_date < data_start_date:
            raise BusinessLogicException(
                "data_end_date must be on or after data_start_date",
            )

        await StudentReportService._check_view_access(
            db,
            student_profile_id,
            current_user,
        )

        student = await db.get(StudentProfile, student_profile_id)
        if not student:
            raise ResourceNotFoundException("Student not found")

        existing = await db.scalar(
            select(StudentReport).filter_by(
                student_profile_id=student_profile_id,
                data_start_date=data_start_date,
                data_end_date=data_end_date,
            ),
        )

        subject_progress = list(
            (
                await db.execute(
                    select(KaSubjectProgress).filter(
                        KaSubjectProgress.student_profile_id == student_profile_id,
                        KaSubjectProgress.snapshot_date >= data_start_date,
                        KaSubjectProgress.snapshot_date <= data_end_date,
                    ),
                )
            )
            .scalars()
            .all(),
        )

        topic_progress = list(
            (
                await db.execute(
                    select(KaTopicProgress).filter(
                        KaTopicProgress.student_profile_id == student_profile_id,
                        KaTopicProgress.snapshot_date >= data_start_date,
                        KaTopicProgress.snapshot_date <= data_end_date,
                    ),
                )
            )
            .scalars()
            .all(),
        )

        subject_rows, topic_rows = [], []
        for sp in subject_progress:
            subject = await db.get(Subject, sp.subject_id) if sp.subject_id else None
            subject_rows.append(
                {
                    "subject_name": subject.subject_name if subject else "Unknown",
                    "point_earned": sp.point_earned or 0,
                    "point_available": sp.point_available or 0,
                    "percentage_earned": sp.percentage_earned or 0.0,
                },
            )
        for tp in topic_progress:
            topic = await db.get(Topic, tp.topic_id) if tp.topic_id else None
            topic_rows.append(
                {
                    "topic_name": topic.topic_name if topic else "Unknown",
                    "point_earned": tp.point_earned or 0,
                    "point_available": tp.point_available or 0,
                    "percentage_earned": tp.percentage_earned or 0.0,
                },
            )

        pdf_bytes = _render_report_pdf(
            student.student_name,
            data_start_date,
            data_end_date,
            subject_rows,
            topic_rows,
        )

        if existing:
            report = existing
            report.pdf_document = pdf_bytes
            report.report_date = date.today()
            # NOTE: touching `report.subject_progress_items` / `.topic_progress_items`
            # here would trigger an implicit lazy-load, which isn't supported
            # on an async session (raises MissingGreenlet) -- query the link
            # rows explicitly instead of going through the lazy relationship.
            old_subject_links = (
                (
                    await db.execute(
                        select(StudentSubjectProgressReport).filter_by(
                            report_id=report.id,
                        ),
                    )
                )
                .scalars()
                .all()
            )
            for link in old_subject_links:
                await db.delete(link)
            old_topic_links = (
                (
                    await db.execute(
                        select(StudentTopicProgressReport).filter_by(
                            report_id=report.id,
                        ),
                    )
                )
                .scalars()
                .all()
            )
            for link in old_topic_links:
                await db.delete(link)
            await db.flush()
        else:
            report = StudentReport(
                student_profile_id=student_profile_id,
                report_date=date.today(),
                data_start_date=data_start_date,
                data_end_date=data_end_date,
                pdf_document=pdf_bytes,
            )
            db.add(report)
            await db.flush()

        for sp in subject_progress:
            db.add(
                StudentSubjectProgressReport(
                    report_id=report.id,
                    subject_id=sp.subject_id,
                    subject_progress_id=sp.id,
                ),
            )
        for tp in topic_progress:
            db.add(
                StudentTopicProgressReport(
                    report_id=report.id,
                    topic_id=tp.topic_id,
                    study_material_id=tp.study_material_id,
                    topic_progress_id=tp.id,
                ),
            )

        await db.flush()
        logger.info(
            f"Report generated for student_profile={student_profile_id} period={data_start_date}..{data_end_date}",
        )

        # Re-fetch with eager-loaded link collections so the caller (the
        # router's response serialization) never triggers an implicit lazy
        # load, which isn't supported on an async session.
        return await db.scalar(
            select(StudentReport)
            .options(
                selectinload(StudentReport.subject_progress_items),
                selectinload(StudentReport.topic_progress_items),
            )
            .filter_by(id=report.id),
        )

    @staticmethod
    async def list_reports(
        db: AsyncSession,
        student_profile_id: int,
        current_user: User,
    ) -> list[StudentReport]:
        await StudentReportService._check_view_access(
            db,
            student_profile_id,
            current_user,
        )
        result = await db.execute(
            select(StudentReport)
            .options(
                selectinload(StudentReport.subject_progress_items),
                selectinload(StudentReport.topic_progress_items),
            )
            .filter_by(student_profile_id=student_profile_id)
            .order_by(StudentReport.report_date.desc()),
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_report(
        db: AsyncSession,
        report_id: int,
        current_user: User,
    ) -> StudentReport:
        report = await db.scalar(
            select(StudentReport)
            .options(
                selectinload(StudentReport.subject_progress_items),
                selectinload(StudentReport.topic_progress_items),
            )
            .filter_by(id=report_id),
        )
        if not report:
            raise ResourceNotFoundException("Report not found")
        await StudentReportService._check_view_access(
            db,
            report.student_profile_id,
            current_user,
        )
        return report

    # =========================================================================
    # Manual sub-report management -- merged in from the other project
    # variant. generate_report() auto-populates subject/topic progress from
    # KA snapshots, but activity aggregates and Zoom duration/interaction
    # stats have no automated source yet, so Admin/Teacher can set them here
    # by hand. Mutations are intentionally admin/teacher-only (enforced in
    # the router via require_role) -- students only ever read reports.
    # =========================================================================

    @staticmethod
    async def delete_report(
        db: AsyncSession,
        report_id: int,
        current_user: User,
    ) -> None:
        report = await StudentReportService.get_report(db, report_id, current_user)
        await student_report_crud.delete(db, report.id)

    @staticmethod
    async def get_activity_report(db: AsyncSession, report_id: int, current_user: User):
        await StudentReportService.get_report(db, report_id, current_user)
        return await student_activity_report_crud.get_by(db, report_id=report_id)

    @staticmethod
    async def set_activity_report(
        db: AsyncSession,
        report_id: int,
        data: dict,
        current_user: User,
    ):
        await StudentReportService.get_report(db, report_id, current_user)
        existing = await student_activity_report_crud.get_by(db, report_id=report_id)
        if existing:
            return await student_activity_report_crud.update(db, existing.id, data)
        return await student_activity_report_crud.create(
            db,
            {**data, "report_id": report_id},
        )

    @staticmethod
    async def get_subject_progress_items(
        db: AsyncSession,
        report_id: int,
        current_user: User,
    ) -> list:
        await StudentReportService.get_report(db, report_id, current_user)
        query = select(StudentSubjectProgressReport).filter(
            StudentSubjectProgressReport.report_id == report_id,
        )
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def delete_subject_progress_item(
        db: AsyncSession,
        item_id: int,
        current_user: User,
    ) -> None:
        item = await student_subject_progress_report_crud.get(db, item_id)
        if not item:
            raise ResourceNotFoundException("Subject progress report item not found")
        await StudentReportService._check_view_access(
            db,
            (
                await StudentReportService.get_report(db, item.report_id, current_user)
            ).student_profile_id,
            current_user,
        )
        await student_subject_progress_report_crud.delete(db, item_id)

    @staticmethod
    async def get_topic_progress_items(
        db: AsyncSession,
        report_id: int,
        current_user: User,
    ) -> list:
        await StudentReportService.get_report(db, report_id, current_user)
        query = select(StudentTopicProgressReport).filter(
            StudentTopicProgressReport.report_id == report_id,
        )
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def delete_topic_progress_item(
        db: AsyncSession,
        item_id: int,
        current_user: User,
    ) -> None:
        item = await student_topic_progress_report_crud.get(db, item_id)
        if not item:
            raise ResourceNotFoundException("Topic progress report item not found")
        await StudentReportService.get_report(db, item.report_id, current_user)
        await student_topic_progress_report_crud.delete(db, item_id)

    @staticmethod
    async def get_zoom_duration_report(
        db: AsyncSession,
        report_id: int,
        current_user: User,
    ):
        await StudentReportService.get_report(db, report_id, current_user)
        return await zoom_duration_report_crud.get_by(db, report_id=report_id)

    @staticmethod
    async def set_zoom_duration_report(
        db: AsyncSession,
        report_id: int,
        data: dict,
        current_user: User,
    ):
        await StudentReportService.get_report(db, report_id, current_user)
        existing = await zoom_duration_report_crud.get_by(db, report_id=report_id)
        if existing:
            return await zoom_duration_report_crud.update(db, existing.id, data)
        return await zoom_duration_report_crud.create(
            db,
            {**data, "report_id": report_id},
        )

    @staticmethod
    async def get_zoom_interaction_report(
        db: AsyncSession,
        report_id: int,
        current_user: User,
    ):
        await StudentReportService.get_report(db, report_id, current_user)
        return await zoom_interaction_report_crud.get_by(db, report_id=report_id)

    @staticmethod
    async def set_zoom_interaction_report(
        db: AsyncSession,
        report_id: int,
        data: dict,
        current_user: User,
    ):
        await StudentReportService.get_report(db, report_id, current_user)
        existing = await zoom_interaction_report_crud.get_by(db, report_id=report_id)
        if existing:
            return await zoom_interaction_report_crud.update(db, existing.id, data)
        return await zoom_interaction_report_crud.create(
            db,
            {**data, "report_id": report_id},
        )

    @staticmethod
    async def attach_document(
        db: AsyncSession,
        report_id: int,
        doc_type: str,
        content: bytes,
        current_user: User,
    ) -> StudentReport:
        await StudentReportService.get_report(db, report_id, current_user)
        field = {
            "pdf": "pdf_document",
            "html": "html_document",
            "png": "png_document",
        }.get(doc_type)
        if not field:
            raise BusinessLogicException("doc_type must be one of: pdf, html, png")
        return await student_report_crud.update(db, report_id, {field: content})

    @staticmethod
    async def get_document(
        db: AsyncSession,
        report_id: int,
        doc_type: str,
        current_user: User,
    ) -> bytes:
        report = await StudentReportService.get_report(db, report_id, current_user)
        field = {
            "pdf": "pdf_document",
            "html": "html_document",
            "png": "png_document",
        }.get(doc_type)
        if not field:
            raise BusinessLogicException("doc_type must be one of: pdf, html, png")
        content = getattr(report, field)
        if not content:
            raise ResourceNotFoundException(
                f"No {doc_type} document generated for this report yet",
            )
        return content

    # =========================================================================
    # Full Student Report — aggregated ERP-native data for the report page.
    # =========================================================================

    @staticmethod
    async def get_full_student_report(
        db: AsyncSession,
        student_profile_id: int,
        current_user: User,
        session_id: int | None = None,
    ) -> dict:
        """Return a single aggregated payload containing the student's
        profile, enrollment, attendance, subject-wise exam & assignment
        results, and fee summary for the selected academic session.
        """
        from src.domain.academics.models import AcademicSession, ClassRoom, ClassSubject
        from src.domain.assignments.models import Assignment, AssignmentResult
        from src.domain.curriculum.models import Subject
        from src.domain.exams.models import Exam, ExamResult
        from src.domain.fees.models import Fee
        from src.domain.operations.models import (
            StudentAttendance,
            StudentClass,
        )

        await StudentReportService._check_view_access(
            db, student_profile_id, current_user,
        )

        profile = await db.get(StudentProfile, student_profile_id)
        if not profile:
            raise ResourceNotFoundException("Student profile not found")

        # Find enrollment: use explicit session_id if provided, else current session, else latest
        enrollment = None
        target_session = None

        if session_id:
            target_session = await db.get(AcademicSession, session_id)
            enrollment = await db.scalar(
                select(StudentClass).filter_by(
                    student_id=profile.user_id,
                    academic_sessions_id=session_id,
                ),
            )
        if not enrollment:
            current_session = await db.scalar(
                select(AcademicSession).filter_by(is_current=True),
            )
            if current_session:
                target_session = current_session
                enrollment = await db.scalar(
                    select(StudentClass).filter_by(
                        student_id=profile.user_id,
                        academic_sessions_id=current_session.id,
                    ),
                )
        if not enrollment:
            enrollment = await db.scalar(
                select(StudentClass)
                .filter_by(student_id=profile.user_id)
                .order_by(StudentClass.academic_sessions_id.desc()),
            )
            if enrollment and not target_session:
                target_session = await db.get(AcademicSession, enrollment.academic_sessions_id)
        if not enrollment:
            return _build_empty_report(profile, student_profile_id)

        # Classroom
        classroom = await db.get(ClassRoom, enrollment.classroom_id)

        # Resolve session name without touching the unloaded relationship
        session_name = None
        if target_session:
            session_name = getattr(target_session, 'session_name', None)
        elif enrollment.academic_sessions_id:
            try:
                _sess = await db.get(AcademicSession, enrollment.academic_sessions_id)
                session_name = getattr(_sess, 'session_name', None) if _sess else None
            except Exception:
                session_name = None

        # Attendance
        attendance = await db.scalar(
            select(StudentAttendance).filter_by(student_class_id=enrollment.id),
        )

        # Subjects for this classroom — build maps keyed by class_subject_id AND subject_id
        class_subjects = list(
            (
                await db.execute(
                    select(ClassSubject).filter_by(
                        classroom_id=enrollment.classroom_id,
                    )
                )
            )
            .scalars()
            .all()
        )

        # cs_id -> {subject_id, subject_name, subject_code}
        cs_to_subject = {}
        # subject_id -> {subject_id, subject_name, subject_code}
        subject_id_map = {}
        for cs in class_subjects:
            try:
                subj = await db.get(Subject, cs.subject_id)
            except Exception:
                subj = None
            if subj:
                info = {
                    "class_subject_id": cs.id,
                    "subject_id": subj.id,
                    "subject_name": subj.subject_name,
                    "subject_code": subj.subject_code,
                }
                cs_to_subject[cs.id] = info
                subject_id_map[subj.id] = info

        async def _resolve_subject_for_class_subject(csid):
            """Look up subject info for a class_subject_id."""
            if csid in cs_to_subject:
                return cs_to_subject[csid]
            try:
                cs_obj = await db.get(ClassSubject, csid)
            except Exception:
                cs_obj = None
            if cs_obj and cs_obj.subject_id in subject_id_map:
                return subject_id_map[cs_obj.subject_id]
            return {}

        # Exam results for this enrollment
        exam_results_raw = list(
            (
                await db.execute(
                    select(ExamResult).filter_by(student_class_id=enrollment.id)
                )
            )
            .scalars()
            .all()
        )
        exam_results = []
        for er in exam_results_raw:
            exam = None
            if er.exam_id:
                try:
                    exam = await db.get(Exam, er.exam_id)
                except Exception:
                    exam = None
            subj_info = {}
            if exam:
                subj_info = await _resolve_subject_for_class_subject(exam.class_subject_id)
            obtained = er.obtained_marks or 0
            total = (getattr(exam, 'total_marks', None) or 0) if exam else 0
            pct = er.percentage if er.percentage is not None else (round(obtained / total * 100, 1) if total > 0 else 0)
            exam_results.append({
                "exam_id": er.exam_id,
                "subject_id": subj_info.get("subject_id"),
                "exam_name": getattr(exam, 'exam_name', None) or "\u2014",
                "exam_type": getattr(exam, 'exam_type', None) or "\u2014",
                "exam_date": str(getattr(exam, 'exam_date', None)) if getattr(exam, 'exam_date', None) else None,
                "subject_name": subj_info.get("subject_name", "\u2014"),
                "obtained_marks": obtained,
                "total_marks": total,
                "percentage": pct,
                "grade": er.grade,
                "is_absent": er.is_absent,
            })

        # Assignment results for this enrollment
        assignment_results_raw = list(
            (
                await db.execute(
                    select(AssignmentResult).filter_by(student_class_id=enrollment.id)
                )
            )
            .scalars()
            .all()
        )
        assignment_results = []
        for ar in assignment_results_raw:
            assignment = None
            if ar.assignment_id:
                try:
                    assignment = await db.get(Assignment, ar.assignment_id)
                except Exception:
                    assignment = None
            subj_info = {}
            if assignment:
                subj_info = await _resolve_subject_for_class_subject(assignment.class_subject_id)
            obtained = ar.obtained_marks or 0
            total = (getattr(assignment, 'total_marks', None) or 0) if assignment else 0
            pct = ar.percentage if ar.percentage is not None else (round(obtained / total * 100, 1) if total > 0 else 0)
            assignment_results.append({
                "assignment_id": ar.assignment_id,
                "subject_id": subj_info.get("subject_id"),
                "title": getattr(assignment, 'title', None) or "\u2014",
                "due_date": str(getattr(assignment, 'due_date', None)) if getattr(assignment, 'due_date', None) else None,
                "subject_name": subj_info.get("subject_name", "\u2014"),
                "obtained_marks": obtained,
                "total_marks": total,
                "percentage": pct,
                "grade": ar.grade,
                "is_checked": ar.is_checked,
            })

        # Subject-wise aggregation — match by subject_id (not name)
        subject_stats = {}
        for subj_id_key, subj_info in subject_id_map.items():
            sname = subj_info["subject_name"]
            sub_exams = [e for e in exam_results if e.get("subject_id") == subj_id_key]
            sub_assignments = [a for a in assignment_results if a.get("subject_id") == subj_id_key]

            avg_exam = 0
            if sub_exams:
                avg_exam = round(
                    sum((e["percentage"] or 0) for e in sub_exams) / len(sub_exams), 1
                )

            checked_assignments = [a for a in sub_assignments if a.get("is_checked")]
            avg_assignment = 0
            if checked_assignments:
                avg_assignment = round(
                    sum((a["percentage"] or 0) for a in checked_assignments) / len(checked_assignments), 1
                )

            subject_stats[subj_id_key] = {
                "subject_name": sname,
                "subject_code": subj_info.get("subject_code"),
                "exam_count": len(sub_exams),
                "exam_avg_percentage": avg_exam,
                "assignment_count": len(sub_assignments),
                "assignments_checked": len(checked_assignments),
                "assignment_avg_percentage": avg_assignment,
            }

        # Fees
        fees = list(
            (
                await db.execute(
                    select(Fee).filter_by(student_class_id=enrollment.id)
                )
            )
            .scalars()
            .all()
        )

        return _build_full_report_dict(
            profile=profile,
            enrollment=enrollment,
            classroom=classroom,
            attendance=attendance,
            subjects=list(subject_stats.values()),
            exam_results=exam_results,
            assignment_results=assignment_results,
            fees=fees,
            session_name=session_name,
        )
