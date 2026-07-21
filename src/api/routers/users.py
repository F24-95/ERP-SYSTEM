from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.database.connection import get_db
from src.domain.users.models import User
from src.domain.users.schemas import UserResponse, UserUpdate
from src.domain.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

# ------------------------------------------------------------------
# CRITICAL SECURITY FIX: this router used to also expose
# `POST /users/` with NO authentication at all, backed by
# `UserService.create_user` / `UserCreate`. `UserCreate` has a plain
# `role: UserRole` field the caller controls directly, so literally
# anyone -- unauthenticated -- could POST {"role": "admin", ...} and
# instantly have a fully working admin account, completely bypassing
# the properly `require_role(ADMIN)`-protected `POST /admin/user` flow.
# It was also functionally broken even for legitimate use: unlike
# `/admin/user` (AdminService.create_user_with_profile), it never
# created the matching StudentProfile/TeacherProfile/AdminProfile or
# assigned a business ID (student_id/teacher_id/admin_id), so anything
# downstream that expects a profile to exist (chat, ID cards, teacher
# assignments, registration numbers, ...) would break for any user
# created this way.
#
# Fix: removed. User creation now only happens through the properly
# guarded `POST /admin/user`. Since that route itself requires an
# existing admin to call it, bootstrapping the very first admin account
# on a fresh deployment now goes through `scripts/create_first_admin.py`
# (a one-time CLI script, not an API route -- see that file for why an
# API-level bootstrap escape hatch would just reintroduce this same
# vulnerability) instead.
# ------------------------------------------------------------------


# NOTE: /me must be registered before /{public_id}, otherwise FastAPI would
# match "GET /users/me" against the "/{public_id}" route first (same HTTP
# method, /me looks like a valid path param value) and this endpoint would
# be permanently unreachable.
@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's own profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the currently authenticated user's own profile.

    Self-service only: `is_active` is intentionally dropped here even
    though it's on the shared `UserUpdate` schema -- a user must not be
    able to (de)activate their own account. Admin-driven updates to
    is_active (and everything else) go through PATCH /admin/users/{public_id}.
    """
    update_data = data.model_dump(exclude_unset=True, exclude={"is_active"})
    return await UserService.update_user(db, current_user, update_data)


@router.get("/{public_id}", response_model=UserResponse)
async def get_user(
    public_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user by public ID. Requires authentication -- was previously
    open to anyone with a guessable/leaked public_id (a UUID, so not
    trivially guessable, but there's no reason this should be
    unauthenticated when nothing else in the API is).
    """
    return await UserService.get_user(db, public_id)
