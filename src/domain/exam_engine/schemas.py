"""Pydantic schemas for the Exam Engine integration domain (webhooks + sync)."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Webhook request payloads (received FROM ns-exam)
# =============================================================================


class ReportGeneratedWebhook(BaseModel):
    event: str = Field(default="report_generated")
    report_public_id: str
    student_id: Optional[int] = None
    exam_id: Optional[int] = None
    report_type: str = "UNKNOWN"
    forced_resync: Optional[bool] = None


class StudentAtRiskWebhook(BaseModel):
    event: str = Field(default="student_at_risk")
    student_id: int
    is_at_risk: bool = False
    class_id: Optional[int] = None


class WebhookResponse(BaseModel):
    success: bool = True
    received: bool = True
    stored_id: Optional[int] = None


# =============================================================================
# Webhook stored-record responses
# =============================================================================


class ExamEngineReportResponse(BaseModel):
    id: int
    public_id: str
    report_public_id: str
    report_type: str
    student_id: Optional[int] = None
    exam_id: Optional[int] = None
    event: str
    payload_json: Optional[Any] = None
    received_at: datetime

    model_config = {"from_attributes": True}


class ExamEngineStudentFlagResponse(BaseModel):
    id: int
    public_id: str
    student_id: int
    is_at_risk: bool
    class_id: Optional[int] = None
    event: str
    payload_json: Optional[Any] = None
    received_at: datetime

    model_config = {"from_attributes": True}
