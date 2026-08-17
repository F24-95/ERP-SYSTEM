from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.dashboard.service import DashboardService
from src.domain.users.models import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/student")
async def get_student_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await DashboardService.get_student_dashboard(db, current_user.id)


@router.get("/teacher")
async def get_teacher_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
):
    return await DashboardService.get_teacher_dashboard(db, current_user.id)


@router.get("/admin")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    return await DashboardService.get_admin_dashboard(db)


@router.get("/admin/overview")
async def get_admin_overview(
    session_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """School-wide ERP summary: totals, fees, attendance for admin report."""
    return await DashboardService.get_admin_overview(db, session_id)


@router.get("/admin/class-stats")
async def get_admin_class_stats(
    session_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Per-class breakdown: students, attendance, exam avg, fees for admin report."""
    return await DashboardService.get_admin_class_stats(db, session_id)
