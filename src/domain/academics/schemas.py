from datetime import date

from pydantic import BaseModel


# ====================
# Academic Session
# ====================


class AcademicSessionBase(BaseModel):
    session_code: str
    session_name: str
    start_year: int
    end_year: int
    start_date: date
    end_date: date
    is_current: bool = False
    description: str | None = None


class AcademicSessionCreate(AcademicSessionBase):
    pass


class AcademicSessionUpdate(BaseModel):
    session_code: str | None = None
    session_name: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    description: str | None = None
    is_active: bool | None = None


class AcademicSessionResponse(AcademicSessionBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


# ====================
# ClassRoom
# ====================


class ClassRoomBase(BaseModel):
    class_code: str
    class_name: str
    section: str
    display_name: str
    description: str | None = None
    academic_sessions_id: int
    class_teacher_id: str | None = None


class ClassRoomCreate(ClassRoomBase):
    pass


class ClassRoomUpdate(BaseModel):
    class_code: str | None = None
    class_name: str | None = None
    section: str | None = None
    display_name: str | None = None
    description: str | None = None
    academic_sessions_id: int | None = None
    class_teacher_id: str | None = None
    is_active: bool | None = None


class ClassRoomResponse(ClassRoomBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


class ClassRoomMinResponse(BaseModel):
    """Lightweight classroom shape for self-service listings (e.g.
    teacher's own classes) that don't need the full ClassRoomResponse.
    """

    id: int
    class_name: str
    section: str
    display_name: str

    model_config = {"from_attributes": True}


# ====================
# ClassSubject (classroom <-> subject mapping for a session)
# ====================
# This was previously modeled (src/domain/academics/models.py) but had NO
# schemas and NO API at all. It's a hard dependency for other domains --
# TeacherSubject.class_subject_id and StudyMaterial.class_subject_id are
# both required (non-nullable) foreign keys to this table, so without this
# endpoint, teachers could never be assigned to a class+subject and study
# material could never be uploaded.


class ClassSubjectBase(BaseModel):
    academic_sessions_id: int
    classroom_id: int
    subject_id: int
    display_order: int = 1


class ClassSubjectCreate(ClassSubjectBase):
    pass


class ClassSubjectUpdate(BaseModel):
    display_order: int | None = None
    is_active: bool | None = None


class ClassSubjectResponse(ClassSubjectBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}
