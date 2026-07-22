from datetime import date

from pydantic import BaseModel


class StudentReportGenerateRequest(BaseModel):
    student_profile_id: int
    data_start_date: date
    data_end_date: date


class StudentReportResponse(BaseModel):
    id: int
    student_profile_id: int
    report_date: date
    data_start_date: date
    data_end_date: date
    has_pdf: bool = False
    has_html: bool = False
    has_png: bool = False
    subject_progress_count: int = 0
    topic_progress_count: int = 0

    model_config = {"from_attributes": True}


# =============================================================================
# Manual sub-report management -- merged in from the other project variant.
# generate_report() above auto-populates subject/topic progress from KA
# snapshots, but activity aggregates and Zoom duration/interaction stats
# aren't sourced from anywhere automatically yet, so an admin/teacher needs
# a way to set them by hand until an automated feed exists.
# =============================================================================


class StudentActivityReportCreate(BaseModel):
    mean_duration_minutes: int | None = None
    total_duration_minutes: int | None = None
    total_worked_hours: int | None = None
    total_attempted: int | None = None
    total_familiar: int | None = None
    total_proficient: int | None = None
    total_leveled_up: int | None = None
    total_mastered: int | None = None


class StudentActivityReportResponse(StudentActivityReportCreate):
    id: int
    report_id: int
    model_config = {"from_attributes": True}


class SubjectProgressItemResponse(BaseModel):
    id: int
    report_id: int
    subject_id: int | None = None
    subject_progress_id: int | None = None
    model_config = {"from_attributes": True}


class TopicProgressItemResponse(BaseModel):
    id: int
    report_id: int
    topic_id: int
    study_material_id: int | None = None
    topic_progress_id: int | None = None
    model_config = {"from_attributes": True}


class ZoomDurationReportCreate(BaseModel):
    mean_duration_minutes: int | None = None
    min_duration_minutes: int | None = None
    max_duration_minutes: int | None = None


class ZoomDurationReportResponse(ZoomDurationReportCreate):
    id: int
    report_id: int
    model_config = {"from_attributes": True}


class ZoomInteractionReportCreate(BaseModel):
    mean_interaction_count: int | None = None
    min_interaction_count: int | None = None
    max_interaction_count: int | None = None


class ZoomInteractionReportResponse(ZoomInteractionReportCreate):
    id: int
    report_id: int
    model_config = {"from_attributes": True}
