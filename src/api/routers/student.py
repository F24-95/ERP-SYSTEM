from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.assignments.schemas import AssignmentResultResponse
from src.domain.exams.schemas import ExamResultResponse
from src.domain.fees.schemas import FeeResponse
from src.domain.operations.schemas import (
    StudentAttendanceResponse,
    StudentClassResponse,
)
from src.domain.users.models import User
from src.domain.users.schemas import StudentProfileResponse, StudentProfileUpdate
from src.domain.users.student_self_service import StudentSelfService

router = APIRouter(prefix="/student", tags=["Student"])

# ============================================================
# STUDENT PROFILE (self-service)
# ============================================================


@router.get("/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await StudentSelfService.get_profile(db, current_user.id)


@router.put("/profile", response_model=StudentProfileResponse)
async def update_student_profile(
    profile_data: StudentProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await StudentSelfService.update_profile(
        db,
        current_user.id,
        profile_data.model_dump(exclude_unset=True),
    )


# ============================================================
# STUDENT CLASSES
# ============================================================


@router.get("/classes", response_model=list[StudentClassResponse])
async def get_student_classes(
    academic_sessions_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await StudentSelfService.get_classes(
        db,
        current_user.id,
        academic_sessions_id,
    )


# ============================================================
# STUDENT ATTENDANCE
# ============================================================


@router.get("/attendance/summary", response_model=StudentAttendanceResponse)
async def get_attendance_summary(
    academic_sessions_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await StudentSelfService.get_attendance_summary(
        db,
        current_user.id,
        academic_sessions_id,
    )


@router.get("/attendance/daily", response_model=list[dict])
async def get_daily_attendance(
    academic_sessions_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await StudentSelfService.get_daily_attendance(
        db,
        current_user.id,
        academic_sessions_id,
        start_date,
        end_date,
    )


# ============================================================
# STUDENT ASSIGNMENTS / EXAMS
# ============================================================


@router.get("/assignments", response_model=list[AssignmentResultResponse])
async def get_student_assignments(
    academic_sessions_id: int,
    subject_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await StudentSelfService.get_assignment_results(
        db,
        current_user.id,
        academic_sessions_id,
        subject_id,
    )


@router.get("/exams", response_model=list[ExamResultResponse])
async def get_student_exams(
    academic_sessions_id: int,
    subject_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await StudentSelfService.get_exam_results(
        db,
        current_user.id,
        academic_sessions_id,
        subject_id,
    )


# ============================================================
# STUDENT FEES
# ============================================================


@router.get("/fees", response_model=list[FeeResponse])
async def get_student_fees(
    academic_sessions_id: int,
    fee_status: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await StudentSelfService.get_fees(
        db,
        current_user.id,
        academic_sessions_id,
        fee_status,
    )


@router.get("/fees/summary")
async def get_fee_summary(
    academic_sessions_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await StudentSelfService.get_fee_summary(
        db,
        current_user.id,
        academic_sessions_id,
    )
