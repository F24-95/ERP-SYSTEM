from datetime import date

from pydantic import BaseModel, Field

from src.core.enums import NoticeAudience, NoticeType


class BaseResponse(BaseModel):
    id: int
    is_active: bool
    model_config = {"from_attributes": True}


class NoticeResponse(BaseResponse):
    notice_id: str
    title: str = Field(..., max_length=250)
    description: str
    notice_type: NoticeType
    audience: NoticeAudience
    publish_date: date
    expiry_date: date | None = None
    attachment_name: str | None = None
    attachment_path: str | None = None
    attachment_size: int | None = None
    mime_type: str | None = None
    is_pinned: bool

    academic_sessions_id: int
    classroom_id: int | None = None
    created_by: int
    updated_by: int | None = None
    deleted_by: int | None = None
