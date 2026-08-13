from datetime import date, datetime, time

from pydantic import BaseModel, Field

from src.core.enums import AssignmentStatus


class BaseResponse(BaseModel):
    id: int
    is_active: bool
    model_config = {"from_attributes": True}


# ============================================================
# Assignment
# ============================================================


class AssignmentBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    instructions: str | None = None
    due_date: date
    due_time: time | None = None
    total_marks: float = 0.0
    passing_marks: float = 0.0
    file_name: str | None = Field(None, max_length=255)
    file_path: str | None = Field(None, max_length=500)
    file_type: str | None = Field(None, max_length=100)
    file_size: int | None = None
    status: AssignmentStatus = AssignmentStatus.DRAFT
    publish_at: datetime | None = None
    close_at: datetime | None = None


class AssignmentCreate(AssignmentBase):
    # NOTE: assignment_id is server-generated (Assignment.assignment_id has a
    # column default of generate_assignment_id, same as legacy) — unlike
    # exam_id, which legacy always accepted from the client. Do not add
    # assignment_id here; passing it would be silently ignored by the CRUD
    # layer's `create`, since the model already assigns it via its default.
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int


class AssignmentUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    instructions: str | None = None
    due_date: date | None = None
    due_time: time | None = None
    total_marks: float | None = None
    passing_marks: float | None = None
    file_name: str | None = Field(None, max_length=255)
    file_path: str | None = Field(None, max_length=500)
    file_type: str | None = Field(None, max_length=100)
    file_size: int | None = None
    status: AssignmentStatus | None = None
    publish_at: datetime | None = None
    close_at: datetime | None = None
    is_active: bool | None = None


class AssignmentResponse(BaseResponse, AssignmentBase):
    assignment_id: str
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    uploaded_by: int | None = None
    created_by: int | None = None
    updated_by: int | None = None
    deleted_by: int | None = None
    total_students: int = 0
    checked_students: int = 0


# ============================================================
# AssignmentResult
# ============================================================


class AssignmentResultBase(BaseModel):
    obtained_marks: float = 0.0
    percentage: float = 0.0
    grade: str | None = Field(None, max_length=10)
    remarks: str | None = None
    is_checked: bool = False
    checked_at: datetime | None = None


class AssignmentResultCreate(AssignmentResultBase):
    student_class_id: int


class AssignmentResultUpdate(BaseModel):
    obtained_marks: float | None = None
    percentage: float | None = None
    grade: str | None = Field(None, max_length=10)
    remarks: str | None = None
    is_checked: bool | None = None
    checked_at: datetime | None = None


class AssignmentResultResponse(BaseResponse, AssignmentResultBase):
    assignment_id: int
    student_class_id: int
    checked_by: int | None = None
