from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.core.exceptions import ResourceNotFoundException
from src.database.connection import get_db
from src.domain.common.schemas import MessageResponse
from src.domain.operations.schemas import (
    DailyClassCreate,
    DailyClassResponse,
    DailyClassStudentCreate,
    DailyClassStudentResponse,
    DailyClassStudentUpdate,
    DailyClassUpdate,
    StudentAttendanceResponse,
)
from src.domain.operations.service import DailyClassService

router = APIRouter(prefix="/daily-class", tags=["Daily Class"])


# ============================================================
# DAILY CLASS CRUD
# ============================================================


@router.post(
    "/",
    response_model=DailyClassResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_daily_class(
    class_data: DailyClassCreate,
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a daily class. Teacher-only, matching legacy (no admin path here)."""
    return await DailyClassService.create_daily_class(db, class_data, current_user)


@router.get("/", response_model=list[DailyClassResponse])
async def get_daily_classes(
    classroom_id: int | None = None,
    class_date: date | None = None,
    lecture_status: str | None = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily classes with filters. Teachers only see their own classes."""
    return await DailyClassService.get_daily_classes(
        db,
        current_user,
        classroom_id=classroom_id,
        class_date=class_date,
        lecture_status=lecture_status,
    )


@router.get("/{daily_class_id}", response_model=DailyClassResponse)
async def get_daily_class(
    daily_class_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily class by ID."""
    return await DailyClassService.get_daily_class(db, daily_class_id)


@router.put("/{daily_class_id}", response_model=DailyClassResponse)
async def update_daily_class(
    daily_class_id: int,
    class_data: DailyClassUpdate,
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Update daily class. Only the owning teacher may update."""
    return await DailyClassService.update_daily_class(
        db,
        daily_class_id,
        class_data,
        current_user,
    )


@router.delete("/{daily_class_id}")
async def delete_daily_class(
    daily_class_id: int,
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete daily class. Only the owning teacher may delete."""
    await DailyClassService.delete_daily_class(db, daily_class_id, current_user)
    return {"success": True, "message": "Class deleted successfully"}


# ============================================================
# ATTENDANCE MANAGEMENT
# ============================================================


@router.post(
    "/{daily_class_id}/students",
    response_model=list[DailyClassStudentResponse],
)
async def mark_attendance(
    daily_class_id: int,
    attendance_data: list[DailyClassStudentCreate],
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Mark attendance for students in a daily class (bulk upsert)."""
    items = [item.model_dump() for item in attendance_data]
    return await DailyClassService.mark_attendance(
        db,
        daily_class_id,
        items,
        current_user,
    )


@router.get(
    "/{daily_class_id}/students",
    response_model=list[DailyClassStudentResponse],
)
async def get_attendance(
    daily_class_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance for a daily class. Admin/teacher see the full roster;
    a student only sees their own record (previously any authenticated
    user got everyone's attendance status).
    """
    return await DailyClassService.get_attendance(db, daily_class_id, current_user)


@router.get("/students/{record_id}", response_model=DailyClassStudentResponse)
async def get_attendance_record(
    record_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single attendance record. Was missing entirely -- only the
    full per-session roster (bulk mark_attendance) existed.
    """
    return await DailyClassService.get_attendance_record(db, record_id, current_user)


@router.put("/students/{record_id}", response_model=DailyClassStudentResponse)
async def update_attendance_record(
    record_id: int,
    data: DailyClassStudentUpdate,
    current_user=Depends(require_role(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Correct a single student's attendance record. Teacher/Admin only."""
    return await DailyClassService.update_attendance_record(
        db,
        record_id,
        data.model_dump(exclude_unset=True),
        current_user,
    )


@router.delete("/students/{record_id}", response_model=MessageResponse)
async def delete_attendance_record(
    record_id: int,
    current_user=Depends(require_role(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single attendance record. Teacher/Admin only."""
    await DailyClassService.delete_attendance_record(db, record_id, current_user)
    return MessageResponse(message="Attendance record deleted")


# ============================================================
# ATTENDANCE SUMMARY (aggregate) -- were missing entirely. The
# StudentAttendance table (total/present/absent/percentage) already
# existed with a CRUD instance, but nothing ever wrote to it -- it was
# always empty, which is also why get_class_summary's attendance_average
# field is hardcoded to 0 (a documented, preserved legacy gap).
# ============================================================


@router.post(
    "/attendance/recalculate/{student_class_id}",
    response_model=StudentAttendanceResponse,
)
async def recalculate_attendance_summary(
    student_class_id: int,
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Recompute a student's attendance totals/percentage from their
    DailyClassStudent history. Computed on demand rather than via a
    scheduled job, since no scheduler/cron infra exists in this project.
    """
    return await DailyClassService.recalculate_attendance_summary(db, student_class_id)


@router.get(
    "/attendance/summary/{student_class_id}",
    response_model=StudentAttendanceResponse,
)
async def get_attendance_summary(
    student_class_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a student's cached attendance summary (call the recalculate
    endpoint above first, or after any attendance changes, to refresh it).
    """
    summary = await DailyClassService.get_attendance_summary(
        db,
        student_class_id,
        current_user,
    )
    if not summary:
        raise ResourceNotFoundException(
            f"No attendance summary yet for student_class_id={student_class_id}. "
            "POST /daily-class/attendance/recalculate/{student_class_id} first.",
        )
    return summary


# ============================================================
# CLASS DASHBOARD
# ============================================================


@router.get("/classroom/{classroom_id}/summary")
async def get_class_summary(
    classroom_id: int,
    start_date: date,
    end_date: date,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get class summary for a date range."""
    return await DailyClassService.get_class_summary(
        db,
        classroom_id,
        start_date,
        end_date,
    )
