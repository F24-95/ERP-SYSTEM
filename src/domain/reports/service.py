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
from src.domain.academics.models import Subject
from src.domain.khan_academy.models import KaSubjectProgress, KaTopicProgress, Topic
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
