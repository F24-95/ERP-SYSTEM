from src.database.base_crud import AsyncBaseCRUD
from src.domain.academics.models import AcademicSession, ClassRoom, ClassSubject


class AcademicSessionCRUD(AsyncBaseCRUD[AcademicSession]):
    def __init__(self):
        super().__init__(AcademicSession)


class ClassRoomCRUD(AsyncBaseCRUD[ClassRoom]):
    def __init__(self):
        super().__init__(ClassRoom)


class ClassSubjectCRUD(AsyncBaseCRUD[ClassSubject]):
    def __init__(self):
        super().__init__(ClassSubject)


academic_session_crud = AcademicSessionCRUD()
classroom_crud = ClassRoomCRUD()
class_subject_crud = ClassSubjectCRUD()
