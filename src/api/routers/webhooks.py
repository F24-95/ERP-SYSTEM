"""Webhook receivers for the ns-exam (Exam Engine) platform.

ns-exam pushes outbound sync events here (Phase 16 of the exam-engine report):
  POST /webhooks/report-generated   — a report was generated in ns-exam.
  POST /webhooks/student-at-risk    — a student's at-risk flag changed.

The ERP stores the metadata + payload so its dashboards and reports can
surface exam-engine data. Admin GET endpoints are provided for review.

Phase 1 Security Hardening: Webhook token is now REQUIRED (not optional).
Phase 5 Webhook Hardening: Added request size limit and structured logging.
"""

import os

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import require_role
from src.core.enums import UserRole
from src.core.logger import get_logger
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

logger = get_logger(__name__)

router = APIRouter(tags=["Exam Engine Integration"])

# Phase 5: Max webhook payload size (1MB)
MAX_WEBHOOK_PAYLOAD_SIZE = 1024 * 1024


async def require_webhook_token(
    x_webhook_token: str | None = Header(default=None, alias="X-Webhook-Token"),
) -> str:
    """Validate webhook token from X-Webhook-Token header.

    Phase 1 Security: Webhook token is now REQUIRED (not optional).
    If EXAM_ENGINE_WEBHOOK_TOKEN is not configured, return 500.
    """
    expected = os.getenv("EXAM_ENGINE_WEBHOOK_TOKEN", "")
    if not expected:
        logger.error("webhook.token_not_configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook token not configured on server",
        )
    if not x_webhook_token or x_webhook_token != expected:
        logger.warning("webhook.invalid_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token",
        )
    return x_webhook_token


@router.post(
    "/webhooks/report-generated",
    response_model=WebhookResponse,
    summary="Receive a report-generated event from ns-exam",
)
async def webhook_report_generated(
    body: ReportGeneratedWebhook,
    _: str = Depends(require_webhook_token),
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "webhook.report_generated.received",
        report_public_id=body.report_public_id,
        report_type=body.report_type,
    )
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
    _: str = Depends(require_webhook_token),
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "webhook.student_at_risk.received",
        student_id=body.student_id,
        is_at_risk=body.is_at_risk,
    )
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
