"""ExamEngineIntegrationService — receive & query data pushed by ns-exam.

Service layer for the Exam Engine webhook receivers and the dashboard/report
surfacing that consumes the stored records.
"""

import os

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import get_logger
from src.domain.exam_engine.crud import (
    exam_engine_report_crud,
    exam_engine_student_flag_crud,
)

logger = get_logger(__name__)


class ExamEngineIntegrationService:
    @staticmethod
    def check_webhook_token(token: str | None) -> None:
        """Validate the optional shared webhook token.

        If `EXAM_ENGINE_WEBHOOK_TOKEN` is set in the ERP env, the incoming
        request must present it. When unset, the endpoint is open (local dev
        convenience) — set it in any non-dev deployment.
        """
        expected = os.getenv("EXAM_ENGINE_WEBHOOK_TOKEN", "")
        if expected and token != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook token",
            )

    @staticmethod
    async def receive_report_generated(
        db: AsyncSession,
        *,
        report_public_id: str,
        report_type: str,
        student_id: int | None,
        exam_id: int | None,
        event: str,
        payload: dict,
    ) -> dict:
        record = await exam_engine_report_crud.create(
            db,
            report_public_id=report_public_id,
            report_type=report_type,
            student_id=student_id,
            exam_id=exam_id,
            event=event,
            payload=payload,
        )
        logger.info(
            f"exam_engine.webhook.report_generated report_public_id={report_public_id} report_type={report_type}"
        )
        return {"stored_id": record.id}

    @staticmethod
    async def receive_student_at_risk(
        db: AsyncSession,
        *,
        student_id: int,
        is_at_risk: bool,
        class_id: int | None,
        event: str,
        payload: dict,
    ) -> dict:
        record = await exam_engine_student_flag_crud.create(
            db,
            student_id=student_id,
            is_at_risk=is_at_risk,
            class_id=class_id,
            event=event,
            payload=payload,
        )
        logger.info(
            f"exam_engine.webhook.student_at_risk student_id={student_id} is_at_risk={is_at_risk}"
        )
        return {"stored_id": record.id}

    # ------------------------------------------------------------------
    # Queries for dashboard / reports
    # ------------------------------------------------------------------

    @staticmethod
    async def get_dashboard_summary(db: AsyncSession) -> dict:
        """Aggregated ns-exam stats for the admin dashboard."""
        reports = await exam_engine_report_crud.count(db)
        flags = await exam_engine_student_flag_crud.count(db)
        at_risk = await exam_engine_student_flag_crud.count_at_risk(db)
        by_type = await exam_engine_report_crud.count_by_type(db)
        recent_reports = await exam_engine_report_crud.list_recent(db, limit=5)
        recent_flags = await exam_engine_student_flag_crud.list_recent(db, limit=5)
        return {
            "total_reports": reports,
            "total_student_flags": flags,
            "at_risk_students": at_risk,
            "reports_by_type": by_type,
            "recent_reports": [
                {
                    "id": r.id,
                    "report_public_id": r.report_public_id,
                    "report_type": r.report_type,
                    "student_id": r.student_id,
                    "exam_id": r.exam_id,
                    "received_at": r.received_at,
                }
                for r in recent_reports
            ],
            "recent_flags": [
                {
                    "id": f.id,
                    "student_id": f.student_id,
                    "is_at_risk": f.is_at_risk,
                    "class_id": f.class_id,
                    "received_at": f.received_at,
                }
                for f in recent_flags
            ],
        }
