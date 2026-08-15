"""CRUD helpers for the Exam Engine integration domain."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.exam_engine.models import ExamEngineReport, ExamEngineStudentFlag


class ExamEngineReportCrud:
    async def create(
        self,
        db: AsyncSession,
        *,
        report_public_id: str,
        report_type: str,
        student_id: int | None,
        exam_id: int | None,
        event: str,
        payload: dict | None,
    ) -> ExamEngineReport:
        """Insert a report webhook record. Dedups by report_public_id."""
        existing = await db.scalar(
            select(ExamEngineReport).filter_by(report_public_id=report_public_id),
        )
        if existing:
            return existing
        obj = ExamEngineReport(
            report_public_id=report_public_id,
            report_type=report_type,
            student_id=student_id,
            exam_id=exam_id,
            event=event,
            payload_json=payload,
        )
        db.add(obj)
        await db.flush()
        return obj

    async def list_recent(self, db: AsyncSession, limit: int = 50) -> list[ExamEngineReport]:
        result = await db.execute(
            select(ExamEngineReport).order_by(ExamEngineReport.received_at.desc()).limit(limit),
        )
        return list(result.scalars().all())

    async def count(self, db: AsyncSession) -> int:
        return await db.scalar(select(func.count()).select_from(ExamEngineReport)) or 0

    async def count_by_type(self, db: AsyncSession) -> dict[str, int]:
        rows = await db.execute(
            select(ExamEngineReport.report_type, func.count())
            .group_by(ExamEngineReport.report_type),
        )
        return {rtype: int(cnt) for rtype, cnt in rows.all()}


class ExamEngineStudentFlagCrud:
    async def create(
        self,
        db: AsyncSession,
        *,
        student_id: int,
        is_at_risk: bool,
        class_id: int | None,
        event: str,
        payload: dict | None,
    ) -> ExamEngineStudentFlag:
        obj = ExamEngineStudentFlag(
            student_id=student_id,
            is_at_risk=is_at_risk,
            class_id=class_id,
            event=event,
            payload_json=payload,
        )
        db.add(obj)
        await db.flush()
        return obj

    async def list_recent(self, db: AsyncSession, limit: int = 50) -> list[ExamEngineStudentFlag]:
        result = await db.execute(
            select(ExamEngineStudentFlag)
            .order_by(ExamEngineStudentFlag.received_at.desc())
            .limit(limit),
        )
        return list(result.scalars().all())

    async def count(self, db: AsyncSession) -> int:
        return await db.scalar(select(func.count()).select_from(ExamEngineStudentFlag)) or 0

    async def count_at_risk(self, db: AsyncSession) -> int:
        return (
            await db.scalar(
                select(func.count())
                .select_from(ExamEngineStudentFlag)
                .filter(ExamEngineStudentFlag.is_at_risk.is_(True)),
            )
            or 0
        )


exam_engine_report_crud = ExamEngineReportCrud()
exam_engine_student_flag_crud = ExamEngineStudentFlagCrud()
