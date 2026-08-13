from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.khan_academy.schemas import (
    KaStudentActivityIngest,
    KaStudentActivityResponse,
    KaSubjectActivityIngest,
    KaSubjectActivityResponse,
    KaSubjectProgressIngest,
    KaSubjectProgressResponse,
    KaTopicProgressIngest,
    KaTopicProgressResponse,
    StudentKaActivitySummaryResponse,
    StudentKaProgressSummaryResponse,
)
from src.domain.khan_academy.service import KaProgressService

router = APIRouter(prefix="/khan-academy", tags=["Khan Academy"])


# ==================== KA PROGRESS ====================


@router.post("/progress/subject", response_model=KaSubjectProgressResponse)
async def ingest_subject_progress(
    data: KaSubjectProgressIngest,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Upsert a KA subject-progress snapshot."""
    return await KaProgressService.ingest_subject_progress(db, data.model_dump())


@router.post("/progress/topic", response_model=KaTopicProgressResponse)
async def ingest_topic_progress(
    data: KaTopicProgressIngest,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Upsert a KA topic-progress snapshot."""
    return await KaProgressService.ingest_topic_progress(db, data.model_dump())


@router.get(
    "/progress/student/{student_profile_id}",
    response_model=StudentKaProgressSummaryResponse,
)
async def get_student_progress(
    student_profile_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a student's KA subject + topic progress history. Students may
    only view their own; Admin/Teacher may view any.
    """
    return await KaProgressService.get_student_progress_summary(
        db,
        student_profile_id,
        current_user,
    )


# ==================== KA ACTIVITY LOGS ====================
# Were completely missing: KaStudentActivity/KaSubjectActivity models and
# CRUD singletons existed, but there were no schemas, service methods, or
# routes at all -- nothing could ever write to these two tables.


@router.post("/activity/student", response_model=KaStudentActivityResponse)
async def ingest_student_activity(
    data: KaStudentActivityIngest,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Upsert a KA daily-activity-summary snapshot."""
    return await KaProgressService.ingest_student_activity(db, data.model_dump())


@router.post("/activity/subject", response_model=KaSubjectActivityResponse)
async def ingest_subject_activity(
    data: KaSubjectActivityIngest,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Log a single per-topic KA activity event."""
    return await KaProgressService.ingest_subject_activity(db, data.model_dump())


@router.get(
    "/activity/student/{student_profile_id}",
    response_model=StudentKaActivitySummaryResponse,
)
async def get_student_activity(
    student_profile_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a student's KA activity logs. Students may only view their own;
    Admin/Teacher may view any.
    """
    return await KaProgressService.get_student_activities(
        db,
        student_profile_id,
        current_user,
    )
