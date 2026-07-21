from typing import Any

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ResourceNotFoundException
from src.domain.users.crud import user_crud
from src.domain.users.models import User


class UserService:
    """Note: user *creation* deliberately does not live here anymore -- see
    the removal note in src/api/routers/users.py. All user creation goes
    through AdminService.create_user_with_profile (POST /admin/user), which
    is properly role-guarded and also creates the matching Student/Teacher
    /AdminProfile + business ID. This class only handles reads/updates on
    an already-existing user.
    """

    @staticmethod
    def get_password_hash(password: str) -> str:
        pwd_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
        return hashed_password.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        password_byte_enc = plain_password.encode("utf-8")
        hashed_password_byte_enc = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

    @classmethod
    async def get_user(cls, session: AsyncSession, public_id: str):
        user = await user_crud.get_by_public_id(session, public_id)
        if not user:
            raise ResourceNotFoundException("User not found")
        return user

    @classmethod
    async def update_user(
        cls,
        session: AsyncSession,
        user: User,
        data: dict[str, Any],
    ) -> User:
        """Update mutable fields on a user. Caller is responsible for
        deciding which fields are allowed for the calling context (e.g. a
        self-service /users/me update must not be allowed to pass
        is_active/role -- see the router).
        """
        if not data:
            return user
        return await user_crud.update(session, user.id, data)
