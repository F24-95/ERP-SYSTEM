from datetime import date

from pydantic import BaseModel


class BaseResponse(BaseModel):
    id: int
    is_active: bool | None = None

    model_config = {"from_attributes": True}


# ===========================
# KA progress snapshots (read-mostly; written by a sync job via the CRUD
# singletons directly -- these Create schemas exist for that job's own
# ingestion endpoint, not for end-user data entry)
# ===========================
class KaSubjectProgressIngest(BaseModel):
    student_profile_id: int
    subject_id: int | None = None
    point_available: int = 0
    point_earned: int = 0
    percentage_earned: float = 0.0
    snapshot_date: date


class KaSubjectProgressResponse(BaseModel):
    id: int
    student_profile_id: int
    subject_id: int | None = None
    point_available: int
    point_earned: int
    percentage_earned: float
    snapshot_date: date

    model_config = {"from_attributes": True}


class KaTopicProgressIngest(BaseModel):
    student_profile_id: int
    subject_id: int | None = None
    topic_id: int | None = None
    study_material_id: int | None = None
    point_available: int = 0
    point_earned: int = 0
    percentage_earned: float = 0.0
    snapshot_date: date


class KaTopicProgressResponse(BaseModel):
    id: int
    student_profile_id: int
    subject_id: int | None = None
    topic_id: int | None = None
    point_available: int
    point_earned: int
    percentage_earned: float
    snapshot_date: date

    model_config = {"from_attributes": True}


class StudentKaProgressSummaryResponse(BaseModel):
    student_profile_id: int
    subject_progress: list[KaSubjectProgressResponse] = []
    topic_progress: list[KaTopicProgressResponse] = []


# ===========================
# KA activity logs -- same "landing point for a sync job" contract as the
# progress snapshots above. Were completely missing: the models
# (KaStudentActivity, KaSubjectActivity) and their CRUD singletons existed
# (src/domain/khan_academy/crud.py), but there were no schemas, no service
# methods, and no routes at all -- nothing could ever write to these two
# tables.
# ===========================
class KaStudentActivityIngest(BaseModel):
    student_profile_id: int
    from_date: date
    to_date: date
    worked_on: int = 0
    attempted: int = 0
    familiar: int = 0
    proficient: int = 0
    leveled_to_proficient: int = 0
    leveled_up: int = 0
    mastered: int = 0
    minutes: int = 0
    minutes_target_status: str | None = None


class KaStudentActivityResponse(BaseModel):
    id: int
    student_profile_id: int
    from_date: date
    to_date: date
    worked_on: int
    attempted: int
    familiar: int
    proficient: int
    leveled_to_proficient: int
    leveled_up: int
    mastered: int
    minutes: int
    minutes_target_status: str | None = None

    model_config = {"from_attributes": True}


class KaSubjectActivityIngest(BaseModel):
    student_profile_id: int
    subject_id: int | None = None
    topic_id: int | None = None
    study_material_id: int | None = None
    activity_date: date


class KaSubjectActivityResponse(BaseModel):
    id: int
    student_profile_id: int
    subject_id: int | None = None
    topic_id: int | None = None
    study_material_id: int | None = None
    activity_date: date

    model_config = {"from_attributes": True}


class StudentKaActivitySummaryResponse(BaseModel):
    student_profile_id: int
    student_activity: list[KaStudentActivityResponse] = []
    subject_activity: list[KaSubjectActivityResponse] = []
