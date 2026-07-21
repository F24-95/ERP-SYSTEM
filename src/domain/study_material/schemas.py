from pydantic import BaseModel, Field

from src.core.enums import MaterialType


class BaseResponse(BaseModel):
    id: int
    is_active: bool
    model_config = {"from_attributes": True}


class StudyMaterialResponse(BaseResponse):
    material_id: str
    title: str
    description: str | None = None
    material_type: MaterialType
    file_name: str
    file_url: str
    file_size: int | None = None
    mime_type: str | None = None
    download_count: int = 0

    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    uploaded_by: int


class StudyMaterialUpdate(BaseModel):
    """Only metadata fields — file replacement is handled separately in the
    router via an optional `file: UploadFile` form param, same split as
    legacy `update_study_material`.
    """

    title: str | None = Field(None, max_length=200)
    description: str | None = None
    material_type: str | None = None
    academic_sessions_id: int | None = None
    classroom_id: int | None = None
    class_subject_id: int | None = None
    teacher_subject_id: int | None = None
