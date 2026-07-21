from src.database.base_crud import AsyncBaseCRUD
from src.domain.assignments.models import Assignment, AssignmentResult


class AssignmentCRUD(AsyncBaseCRUD[Assignment]):
    pass


class AssignmentResultCRUD(AsyncBaseCRUD[AssignmentResult]):
    pass


assignment_crud = AssignmentCRUD(Assignment)
assignment_result_crud = AssignmentResultCRUD(AssignmentResult)
