from datetime import date, datetime, time

from pydantic import BaseModel, Field

from src.core.enums import ExamStatus


class BaseResponse(BaseModel):
    id: int
    is_active: bool
    model_config = {"from_attributes": True}


# ============================================================
# Exam
# ============================================================


class ExamBase(BaseModel):
    exam_name: str = Field(..., max_length=150)
    exam_type: str = Field(..., max_length=50)
    description: str | None = None
    exam_date: date
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = None
    room_number: str | None = Field(None, max_length=50)
    total_marks: float
    passing_marks: float
    status: ExamStatus = ExamStatus.DRAFT
    publish_at: datetime | None = None
    completed_at: datetime | None = None


class ExamCreate(ExamBase):
    # NOTE: exam_id is client-supplied here, matching the legacy behavior in
    # app/routers/exam_routers.py::create_exam, which takes exam_data.exam_id
    # verbatim rather than auto-generating it (unlike Fee, which the legacy
    # model auto-generated via a column default). Preserved as-is even
    # though it differs from the fee_id pattern — this is intentional
    # parity with existing production behavior, not an oversight.
    exam_id: str = Field(..., max_length=30)
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int


class ExamUpdate(BaseModel):
    exam_name: str | None = Field(None, max_length=150)
    exam_type: str | None = Field(None, max_length=50)
    description: str | None = None
    exam_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = None
    room_number: str | None = Field(None, max_length=50)
    total_marks: float | None = None
    passing_marks: float | None = None
    status: ExamStatus | None = None
    publish_at: datetime | None = None
    completed_at: datetime | None = None
    is_active: bool | None = None


class ExamResponse(BaseResponse, ExamBase):
    exam_id: str
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    created_by: int
    updated_by: int | None = None
    deleted_by: int | None = None
    total_students: int = 0
    result_uploaded: int = 0


# ============================================================
# ExamResult
# ============================================================


class ExamResultBase(BaseModel):
    obtained_marks: float = 0.0
    percentage: float = 0.0
    grade: str | None = Field(None, max_length=10)
    remarks: str | None = None
    rank_in_class: int | None = None
    is_absent: bool = False
    checked_at: datetime | None = None


class ExamResultCreate(ExamResultBase):
    student_class_id: int


class ExamResultUpdate(BaseModel):
    obtained_marks: float | None = None
    percentage: float | None = None
    grade: str | None = Field(None, max_length=10)
    remarks: str | None = None
    rank_in_class: int | None = None
    is_absent: bool | None = None
    checked_at: datetime | None = None


class ExamResultResponse(BaseResponse, ExamResultBase):
    exam_id: int
    student_class_id: int
    checked_by: int | None = None
