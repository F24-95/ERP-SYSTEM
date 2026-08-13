from src.database.base_crud import AsyncBaseCRUD
from src.domain.curriculum.models import Subject, Topic

subject_crud = AsyncBaseCRUD[Subject](Subject)
topic_crud = AsyncBaseCRUD[Topic](Topic)
