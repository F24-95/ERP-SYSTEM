from src.database.base_crud import AsyncBaseCRUD
from src.domain.reports.models import (
    StudentActivityReport,
    StudentReport,
    StudentSubjectProgressReport,
    StudentTopicProgressReport,
    ZoomDurationReport,
    ZoomInteractionReport,
)

student_report_crud = AsyncBaseCRUD[StudentReport](StudentReport)
student_activity_report_crud = AsyncBaseCRUD[StudentActivityReport](
    StudentActivityReport,
)
student_subject_progress_report_crud = AsyncBaseCRUD[StudentSubjectProgressReport](
    StudentSubjectProgressReport,
)
student_topic_progress_report_crud = AsyncBaseCRUD[StudentTopicProgressReport](
    StudentTopicProgressReport,
)
zoom_duration_report_crud = AsyncBaseCRUD[ZoomDurationReport](ZoomDurationReport)
zoom_interaction_report_crud = AsyncBaseCRUD[ZoomInteractionReport](
    ZoomInteractionReport,
)
