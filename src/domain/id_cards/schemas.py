from datetime import date
from typing import Any

from pydantic import BaseModel


class StudentIDCardGenerateResponse(BaseModel):
    success: bool
    card_id: int
    student_profile_id: int
    academic_sessions_id: int
    pdf_path: str | None = None
    qr_code_path: str | None = None


class StudentIDCardResponse(BaseModel):
    id: int
    student_profile_id: int
    academic_sessions_id: int

    institute_logo_path: str | None = None
    institute_name: str
    institute_contact_number: str
    academic_session_label: str | None = None

    date_of_joining: date | None = None
    valid_till: date | None = None

    student_photo_path: str | None = None
    student_name: str
    parent_name: str | None = None

    class_display_name: str | None = None
    student_id_business: str

    qr_code_path: str | None = None
    pdf_path: str | None = None

    class Config:
        from_attributes = True


class StudentIDCardDownloadResponse(BaseModel):
    success: bool
    download_url: str
    pdf_path: str


class PaginatedStudentIDCardListResponse(BaseModel):
    success: bool
    data: list[StudentIDCardResponse]
    pagination: dict[str, Any]
