from src.database.base_crud import AsyncBaseCRUD
from src.domain.khan_academy.models import (
    KaStudentActivity,
    KaSubjectActivity,
    KaSubjectProgress,
    KaTopicProgress,
    Topic,
)

topic_crud = AsyncBaseCRUD[Topic](Topic)
ka_student_activity_crud = AsyncBaseCRUD[KaStudentActivity](KaStudentActivity)
ka_subject_activity_crud = AsyncBaseCRUD[KaSubjectActivity](KaSubjectActivity)
ka_subject_progress_crud = AsyncBaseCRUD[KaSubjectProgress](KaSubjectProgress)
ka_topic_progress_crud = AsyncBaseCRUD[KaTopicProgress](KaTopicProgress)
