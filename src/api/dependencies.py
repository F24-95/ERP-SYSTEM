from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import AuthenticationException, AuthorizationException
from src.core.security import verify_token
from src.database.connection import get_db
from src.domain.auth.crud import revoked_token_crud
from src.domain.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to get the current authenticated user."""
    payload = verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Token payload missing subject identifier")

    jti = payload.get("jti")
    if jti and await revoked_token_crud.is_revoked(db, jti):
        raise AuthenticationException("Token has been revoked")

    result = await db.execute(
        select(User).filter_by(id=int(user_id), is_active=True, is_deleted=False),
    )
    user = result.scalars().first()

    if not user:
        raise AuthenticationException("User not found or inactive")

    return user


def require_role(*allowed_roles: UserRole):
    """Dependency to restrict access to specific roles.
    Usage: Depends(require_role(UserRole.ADMIN, UserRole.TEACHER))
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationException(
                f"Role {current_user.role} not authorized for this action",
            )
        return current_user

    return role_checker


async def require_super_admin(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to restrict access to Super Admins only (AdminProfile.is_super_admin)."""
    from src.domain.users.models import AdminProfile

    result = await db.execute(select(AdminProfile).filter_by(user_id=current_user.id))
    profile = result.scalars().first()

    if not profile or not profile.is_super_admin:
        raise AuthorizationException("Super admin privileges required for this action")

    return current_user
