"""Webhook receivers for the ns-exam (Exam Engine) platform.

ns-exam pushes outbound sync events here (Phase 16 of the exam-engine report):
  POST /webhooks/report-generated   — a report was generated in ns-exam.
  POST /webhooks/student-at-risk    — a student's at-risk flag changed.

The ERP stores the metadata + payload so its dashboards and reports can
surface exam-engine data. Admin GET endpoints are provided for review.
"""

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.exam_engine.crud import (
    exam_engine_report_crud,
    exam_engine_student_flag_crud,
)
from src.domain.exam_engine.schemas import (
    ExamEngineReportResponse,
    ExamEngineStudentFlagResponse,
    ReportGeneratedWebhook,
    StudentAtRiskWebhook,
    WebhookResponse,
)
from src.domain.exam_engine.service import ExamEngineIntegrationService

router = APIRouter(tags=["Exam Engine Integration"])


@router.post(
    "/webhooks/report-generated",
    response_model=WebhookResponse,
    summary="Receive a report-generated event from ns-exam",
)
async def webhook_report_generated(
    body: ReportGeneratedWebhook,
    x_webhook_token: str | None = Header(default=None, alias="X-Webhook-Token"),
    db: AsyncSession = Depends(get_db),
):
    ExamEngineIntegrationService.check_webhook_token(x_webhook_token)
    result = await ExamEngineIntegrationService.receive_report_generated(
        db,
        report_public_id=body.report_public_id,
        report_type=body.report_type,
        student_id=body.student_id,
        exam_id=body.exam_id,
        event=body.event,
        payload=body.model_dump(),
    )
    return WebhookResponse(stored_id=result["stored_id"])


@router.post(
    "/webhooks/student-at-risk",
    response_model=WebhookResponse,
    summary="Receive a student-at-risk event from ns-exam",
)
async def webhook_student_at_risk(
    body: StudentAtRiskWebhook,
    x_webhook_token: str | None = Header(default=None, alias="X-Webhook-Token"),
    db: AsyncSession = Depends(get_db),
):
    ExamEngineIntegrationService.check_webhook_token(x_webhook_token)
    result = await ExamEngineIntegrationService.receive_student_at_risk(
        db,
        student_id=body.student_id,
        is_at_risk=body.is_at_risk,
        class_id=body.class_id,
        event=body.event,
        payload=body.model_dump(),
    )
    return WebhookResponse(stored_id=result["stored_id"])


@router.get(
    "/webhooks/reports",
    response_model=list[ExamEngineReportResponse],
    summary="List exam-engine report webhooks (admin)",
)
async def list_report_webhooks(
    limit: int = 50,
    _: None = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await exam_engine_report_crud.list_recent(db, limit=limit)


@router.get(
    "/webhooks/student-flags",
    response_model=list[ExamEngineStudentFlagResponse],
    summary="List exam-engine student flags (admin)",
)
async def list_student_flag_webhooks(
    limit: int = 50,
    _: None = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await exam_engine_student_flag_crud.list_recent(db, limit=limit)
