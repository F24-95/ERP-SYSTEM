from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.exams.schemas import (
    ExamCreate,
    ExamResponse,
    ExamResultCreate,
    ExamResultResponse,
    ExamUpdate,
)
from src.domain.exams.service import ExamService
from src.domain.users.models import User

router = APIRouter(prefix="/exams", tags=["Exams"])


@router.post("/", response_model=ExamResponse)
async def create_exam(
    exam_data: ExamCreate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new exam."""
    return await ExamService.create_exam(db, exam_data, current_user)


@router.get("/", response_model=list[ExamResponse])
async def get_exams(
    classroom_id: int | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get exams with filters. Teachers only see exams for their own subjects."""
    return await ExamService.get_exams(
        db,
        current_user,
        classroom_id=classroom_id,
        status=status,
    )


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get exam by ID."""
    return await ExamService.get_exam(db, exam_id)


@router.put("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: int,
    exam_data: ExamUpdate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Update exam. Only the creator or an admin may update."""
    return await ExamService.update_exam(db, exam_id, exam_data, current_user)


@router.delete("/{exam_id}")
async def delete_exam(
    exam_id: int,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete (soft) an exam. Only the creator or an admin may delete."""
    await ExamService.delete_exam(db, exam_id, current_user)
    return {"success": True, "message": "Exam deleted successfully"}


@router.post("/{exam_id}/results", response_model=list[ExamResultResponse])
async def upload_exam_results(
    exam_id: int,
    results_data: list[ExamResultCreate],
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Upload (create or update) results for an exam."""
    return await ExamService.upload_exam_results(
        db,
        exam_id,
        results_data,
        current_user,
    )


@router.get("/{exam_id}/results", response_model=list[ExamResultResponse])
async def get_exam_results(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get results for an exam. Admin sees everyone; a teacher only for
    exams they own; a student only their own result (previously any
    authenticated user got the full class list, including every other
    student's marks).
    """
    return await ExamService.get_exam_results(db, exam_id, current_user)


@router.get("/results/{result_id}", response_model=ExamResultResponse)
async def get_exam_result(
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single exam result. Was missing entirely -- a result could
    only ever be fetched as part of the full class list.
    """
    return await ExamService.get_exam_result(db, result_id, current_user)


@router.delete("/results/{result_id}")
async def delete_exam_result(
    result_id: int,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single exam result (e.g. uploaded against the wrong
    student). Was missing entirely -- the only "update" path was
    re-uploading the whole class's results, which can overwrite a row but
    never remove one.
    """
    await ExamService.delete_exam_result(db, result_id, current_user)
    return {"success": True, "message": "Exam result deleted successfully"}
