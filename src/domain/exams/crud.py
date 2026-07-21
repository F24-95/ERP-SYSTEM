from src.database.base_crud import AsyncBaseCRUD
from src.domain.exams.models import Exam, ExamResult


class ExamCRUD(AsyncBaseCRUD[Exam]):
    pass


class ExamResultCRUD(AsyncBaseCRUD[ExamResult]):
    pass


exam_crud = ExamCRUD(Exam)
exam_result_crud = ExamResultCRUD(ExamResult)
