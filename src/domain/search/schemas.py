from pydantic import BaseModel, Field


class StudentSearchResultItem(BaseModel):
    display_name: str = Field(..., description="Student's full name, for display only")
    email: str | None = None
    student_code: str | None = Field(
        None,
        description="Human-facing code (admission number)",
    )
    # NOTE: legacy's internal_id was the string business ID (student_id).
    # This project's StudentProfile has no such column, so internal_id is
    # `str(StudentProfile.id)` -- the numeric PK, stringified for schema
    # parity -- and IS what the follow-up ID-card/enrollment/etc. endpoints
    # in this migration expect (they all key off StudentProfile.id now).
    internal_id: str = Field(
        ...,
        description="Internal identifier (StudentProfile.id) - use this in follow-up API calls",
    )

    registration_number: str | None = None
    phone: str | None = None
    profile_photo: str | None = None

    score: float = Field(..., description="Blended confidence, 0-100")
    confidence_label: str = Field(..., description='"high" | "medium" | "low"')
    match_type: str = Field(..., description='"exact" | "fuzzy"')
    matched_field: str
    signals: list[str] = Field(default_factory=list)


class StudentSearchResponse(BaseModel):
    query: str
    query_type: str = Field(..., description='"email" | "name_or_code", auto-detected')
    result_count: int
    results: list[StudentSearchResultItem]


class TeacherSearchResultItem(BaseModel):
    display_name: str
    email: str | None = None
    teacher_code: str | None = Field(
        None,
        description="Human-facing code (employee code)",
    )
    internal_id: str = Field(
        ...,
        description="Internal identifier (TeacherProfile.id) - use this in follow-up API calls",
    )

    department: str | None = None
    designation: str | None = None
    phone: str | None = None
    profile_photo: str | None = None

    score: float
    confidence_label: str
    match_type: str
    matched_field: str
    signals: list[str] = Field(default_factory=list)


class TeacherSearchResponse(BaseModel):
    query: str
    query_type: str
    result_count: int
    results: list[TeacherSearchResultItem]
