"""Exam Engine integration domain.

Tables owned here receive and store data pushed by the ns-exam (Exam Engine)
platform via outbound webhooks, so the ERP dashboard and reports can surface
exam-engine results:

  exam_engine_reports          — report-generated webhook events from ns-exam.
  exam_engine_student_flags    — student-at-risk flags pushed from ns-exam.

These tables were drafted fresh for this project; nothing in the legacy
`mmmmmm` codebase referenced them.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.database.connection import Base
from src.domain.common.mixins import TimestampMixin, UUIDMixin


class ExamEngineReport(Base, TimestampMixin, UUIDMixin):
    """One row = one `report_generated` webhook received from ns-exam.

    The ERP only stores metadata + the original payload for audit; the full
    report itself lives in ns-exam (Phase 15: PDFs are never stored
    permanently, only their metadata is kept).
    """

    __tablename__ = "exam_engine_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_public_id = Column(String(64), nullable=False, index=True)
    report_type = Column(String(40), nullable=False, index=True)
    student_id = Column(Integer, nullable=True)
    exam_id = Column(Integer, nullable=True)
    event = Column(String(40), nullable=False)
    payload_json = Column(JSON, nullable=True)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("report_public_id", name="uq_exam_engine_report_public_id"),
        Index("idx_exam_engine_report_type", "report_type"),
        Index("idx_exam_engine_report_received", "received_at"),
    )


class ExamEngineStudentFlag(Base, TimestampMixin, UUIDMixin):
    """One row = one `student_at_risk` webhook received from ns-exam."""

    __tablename__ = "exam_engine_student_flags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False, index=True)
    is_at_risk = Column(Boolean, nullable=False, default=False)
    class_id = Column(Integer, nullable=True, index=True)
    event = Column(String(40), nullable=False)
    payload_json = Column(JSON, nullable=True)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_exam_engine_flag_risk", "is_at_risk"),
        Index("idx_exam_engine_flag_received", "received_at"),
    )
