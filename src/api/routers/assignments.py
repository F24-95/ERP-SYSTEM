from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.assignments.schemas import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentResultCreate,
    AssignmentResultResponse,
    AssignmentUpdate,
)
from src.domain.assignments.service import AssignmentService
from src.domain.users.models import User

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post("/", response_model=AssignmentResponse)
async def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new assignment."""
    return await AssignmentService.create_assignment(db, assignment_data, current_user)


@router.get("/", response_model=list[AssignmentResponse])
async def get_assignments(
    classroom_id: int | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get assignments with filters. Teachers only see their own subjects'
    assignments; students only see their own class's (previously
    unfiltered for students -- any class's assignments were visible).
    """
    return await AssignmentService.get_assignments(
        db,
        current_user,
        classroom_id=classroom_id,
        status=status,
    )


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get assignment by ID. Teachers may only view assignments they teach;
    students may only view assignments for their own class (previously
    every non-admin, non-teacher role -- i.e. every student -- was denied
    outright with a 403 on this endpoint).
    """
    return await AssignmentService.get_assignment(db, assignment_id, current_user)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Update assignment. Only the creator or an admin may update."""
    return await AssignmentService.update_assignment(
        db,
        assignment_id,
        assignment_data,
        current_user,
    )


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete (soft) an assignment. Only the creator or an admin may delete."""
    await AssignmentService.delete_assignment(db, assignment_id, current_user)
    return {"success": True, "message": "Assignment deleted successfully"}


@router.post("/{assignment_id}/results", response_model=list[AssignmentResultResponse])
async def grade_assignment(
    assignment_id: int,
    results_data: list[AssignmentResultCreate],
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Grade students for an assignment."""
    return await AssignmentService.grade_assignment(
        db,
        assignment_id,
        results_data,
        current_user,
    )


@router.get("/{assignment_id}/results", response_model=list[AssignmentResultResponse])
async def get_assignment_results(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get assignment results. Admins see all; teachers only for assignments they teach."""
    return await AssignmentService.get_assignment_results(
        db,
        assignment_id,
        current_user,
    )


@router.get("/results/{result_id}", response_model=AssignmentResultResponse)
async def get_assignment_result(
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single assignment result. Was missing entirely -- a grade
    could only ever be fetched as part of the full class list.
    """
    return await AssignmentService.get_assignment_result(db, result_id, current_user)


@router.delete("/results/{result_id}")
async def delete_assignment_result(
    result_id: int,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single assignment result (e.g. graded against the wrong
    student). Was missing entirely -- only re-grading (overwrite) was
    possible, never removal.
    """
    await AssignmentService.delete_assignment_result(db, result_id, current_user)
    return {"success": True, "message": "Assignment result deleted successfully"}
