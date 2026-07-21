from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.academics.schemas import ClassRoomMinResponse
from src.domain.assignments.schemas import AssignmentResponse
from src.domain.operations.schemas import StudentClassResponse, TeacherSubjectResponse
from src.domain.users.models import User
from src.domain.users.schemas import TeacherProfileResponse, TeacherProfileUpdate
from src.domain.users.teacher_self_service import TeacherSelfService

router = APIRouter(prefix="/teacher", tags=["Teacher"])

# ============================================================
# TEACHER PROFILE (self-service)
# ============================================================


@router.get("/profile", response_model=TeacherProfileResponse)
async def get_teacher_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
):
    return await TeacherSelfService.get_profile(db, current_user.id)


@router.put("/profile", response_model=TeacherProfileResponse)
async def update_teacher_profile(
    profile_data: TeacherProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
):
    return await TeacherSelfService.update_profile(
        db,
        current_user.id,
        profile_data.model_dump(exclude_unset=True),
    )


# ============================================================
# TEACHER CLASSES / STUDENTS / SUBJECTS
# ============================================================


@router.get("/classes", response_model=list[ClassRoomMinResponse])
async def get_teacher_classes(
    academic_sessions_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
):
    return await TeacherSelfService.get_classes(
        db,
        current_user.id,
        academic_sessions_id,
    )


@router.get("/students", response_model=list[StudentClassResponse])
async def get_class_students(
    classroom_id: int,
    academic_sessions_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
):
    return await TeacherSelfService.get_class_students(
        db,
        current_user.id,
        classroom_id,
        academic_sessions_id,
    )


@router.get("/my-students", response_model=list[StudentClassResponse])
async def get_my_students(
    academic_sessions_id: int,
    classroom_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
):
    return await TeacherSelfService.get_my_students(
        db,
        current_user.id,
        academic_sessions_id,
        classroom_id,
    )


@router.get("/subjects", response_model=list[TeacherSubjectResponse])
async def get_teacher_subjects(
    academic_sessions_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
):
    return await TeacherSelfService.get_subjects(
        db,
        current_user.id,
        academic_sessions_id,
    )


# ============================================================
# ATTENDANCE MARKING
# ============================================================


@router.post("/attendance/mark")
async def mark_attendance(
    daily_class_id: int,
    attendance_list: list[dict],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
):
    return await TeacherSelfService.mark_attendance(
        db,
        current_user.id,
        daily_class_id,
        attendance_list,
    )


# ============================================================
# ASSIGNMENTS / DASHBOARD
# ============================================================


@router.get("/assignments", response_model=list[AssignmentResponse])
async def get_teacher_assignments(
    academic_sessions_id: int | None = None,
    classroom_id: int | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
):
    return await TeacherSelfService.get_assignments(
        db,
        current_user.id,
        academic_sessions_id,
        classroom_id,
        status,
    )


@router.get("/dashboard")
async def get_teacher_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
):
    return await TeacherSelfService.get_dashboard(db, current_user.id)
