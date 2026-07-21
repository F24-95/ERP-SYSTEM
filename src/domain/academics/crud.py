from src.database.base_crud import AsyncBaseCRUD
from src.domain.academics.models import (
    AcademicSession,
    ClassRoom,
    ClassSubject,
    Subject,
)


class AcademicSessionCRUD(AsyncBaseCRUD[AcademicSession]):
    def __init__(self):
        super().__init__(AcademicSession)


class ClassRoomCRUD(AsyncBaseCRUD[ClassRoom]):
    def __init__(self):
        super().__init__(ClassRoom)


class SubjectCRUD(AsyncBaseCRUD[Subject]):
    def __init__(self):
        super().__init__(Subject)


class ClassSubjectCRUD(AsyncBaseCRUD[ClassSubject]):
    def __init__(self):
        super().__init__(ClassSubject)


academic_session_crud = AcademicSessionCRUD()
classroom_crud = ClassRoomCRUD()
subject_crud = SubjectCRUD()
class_subject_crud = ClassSubjectCRUD()
