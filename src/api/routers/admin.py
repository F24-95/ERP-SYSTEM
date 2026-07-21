from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.admin.service import AdminService
from src.domain.users.models import User
from src.domain.users.schemas import (
    AdminProfileResponse,
    AdminProfileUpdate,
    AdminUserCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
    TeacherProfileResponse,
    TeacherProfileUpdate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (Admin only). Auto-creates the corresponding Profile."""
    return await AdminService.create_user_with_profile(db, user_data, current_user.id)


# ------------------------------------------------------------------
# User management
# ------------------------------------------------------------------


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    role: UserRole | None = None,
    is_active: bool | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all users (Admin only), optionally filtered by role and/or active status."""
    items, _total = await AdminService.list_users(
        db,
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active,
    )
    return items


@router.get("/users/{public_id}", response_model=UserResponse)
async def get_user(
    public_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get any user by public ID (Admin only)."""
    return await AdminService.get_user(db, public_id)


@router.patch("/users/{public_id}", response_model=UserResponse)
async def update_user(
    public_id: str,
    data: UserUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update any user's phone / active status (Admin only)."""
    return await AdminService.update_user(db, public_id, data)


@router.delete("/users/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    public_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate (disable login for) any user (Admin only)."""
    await AdminService.deactivate_user(db, public_id)


# ------------------------------------------------------------------
# Profile listing & management
# Admin/Teacher/Student can view profiles; only Admin can modify
# ------------------------------------------------------------------


@router.get("/students", response_model=list[StudentProfileResponse])
async def list_student_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT),
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all student profiles. Accessible by Admin, Teacher, and Student."""
    items, _total = await AdminService.list_student_profiles(db, skip=skip, limit=limit)
    return items


@router.get("/students/{profile_id}", response_model=StudentProfileResponse)
async def get_student_profile(
    profile_id: int,
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT),
    ),
    db: AsyncSession = Depends(get_db),
):
    """View any student profile. Accessible by Admin, Teacher, and Student."""
    return await AdminService.get_student_profile(db, profile_id)


@router.patch("/students/{profile_id}", response_model=StudentProfileResponse)
async def update_student_profile(
    profile_id: int,
    data: StudentProfileUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.update_student_profile(
        db,
        profile_id,
        data.model_dump(exclude_unset=True),
    )


@router.delete("/students/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_student_profile(
    profile_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await AdminService.deactivate_student_profile(db, profile_id)


@router.get("/teachers", response_model=list[TeacherProfileResponse])
async def list_teacher_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT),
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all teacher profiles. Accessible by Admin, Teacher, and Student."""
    items, _total = await AdminService.list_teacher_profiles(db, skip=skip, limit=limit)
    return items


@router.get("/teachers/{profile_id}", response_model=TeacherProfileResponse)
async def get_teacher_profile(
    profile_id: int,
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT),
    ),
    db: AsyncSession = Depends(get_db),
):
    """View any teacher profile. Accessible by Admin, Teacher, and Student."""
    return await AdminService.get_teacher_profile(db, profile_id)


@router.patch("/teachers/{profile_id}", response_model=TeacherProfileResponse)
async def update_teacher_profile(
    profile_id: int,
    data: TeacherProfileUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.update_teacher_profile(
        db,
        profile_id,
        data.model_dump(exclude_unset=True),
    )


@router.delete("/teachers/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_teacher_profile(
    profile_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await AdminService.deactivate_teacher_profile(db, profile_id)


@router.get("/admins", response_model=list[AdminProfileResponse])
async def list_admin_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT),
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all admin profiles. Accessible by Admin, Teacher, and Student."""
    items, _total = await AdminService.list_admin_profiles(db, skip=skip, limit=limit)
    return items


@router.get("/admins/{profile_id}", response_model=AdminProfileResponse)
async def get_admin_profile(
    profile_id: int,
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT),
    ),
    db: AsyncSession = Depends(get_db),
):
    """View any admin profile. Accessible by Admin, Teacher, and Student."""
    return await AdminService.get_admin_profile(db, profile_id)


@router.patch("/admins/{profile_id}", response_model=AdminProfileResponse)
async def update_admin_profile(
    profile_id: int,
    data: AdminProfileUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Note: this includes is_super_admin. An ordinary admin can grant/revoke
    super-admin status via this route -- acceptable within this project's
    existing trust model (all admins are already fully trusted; there's no
    tiered-admin permission system elsewhere either), but worth flagging if
    a stricter model is wanted later (e.g. only an existing super-admin may
    grant it).
    """
    return await AdminService.update_admin_profile(
        db,
        profile_id,
        data.model_dump(exclude_unset=True),
    )


@router.delete("/admins/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_admin_profile(
    profile_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await AdminService.deactivate_admin_profile(db, profile_id)
