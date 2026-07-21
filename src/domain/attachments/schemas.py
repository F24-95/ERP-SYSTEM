from datetime import datetime

from pydantic import BaseModel, Field


class AttachmentUploadRequest(BaseModel):
    entity_type: str = Field(..., max_length=30)
    entity_id: int
    file_name: str
    mime_type: str
    file_data: str  # base64-encoded, raw or data-URL format


class AttachmentUploadResponse(BaseModel):
    success: bool
    attachment_id: int
    attachment_code: str
    file_name: str
    file_size: int


class AttachmentMetaResponse(BaseModel):
    id: int
    attachment_code: str
    file_name: str
    mime_type: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True


class AttachmentListResponse(BaseModel):
    success: bool
    data: list[AttachmentMetaResponse]
