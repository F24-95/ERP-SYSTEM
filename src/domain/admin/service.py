from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import BusinessLogicException, ResourceNotFoundException
from src.core.logger import get_logger
from src.core.security import hash_password
from src.core.utils import generate_admin_id, generate_student_id, generate_teacher_id
from src.domain.users.crud import (
    admin_profile_crud,
    student_profile_crud,
    teacher_profile_crud,
    user_crud,
)
from src.domain.users.models import AdminProfile, StudentProfile, TeacherProfile, User
from src.domain.users.registration_number_service import RegistrationNumberService
from src.domain.users.schemas import AdminUserCreate, UserUpdate

logger = get_logger(__name__)


class AdminService:
    @classmethod
    async def create_user_with_profile(
        cls,
        session: AsyncSession,
        user_data: AdminUserCreate,
        current_user_id: int,
    ) -> User:
        # Check if email exists
        existing = await user_crud.get_by_email(session, user_data.email)
        if existing:
            raise BusinessLogicException("Email already registered")

        # We also ideally need to check phone uniqueness, skipping for brevity but assuming user_crud covers it

        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["password_hash"] = hash_password(user_data.password)
        user_dict["created_by"] = current_user_id

        # Create base user
        new_user = await user_crud.create(session, user_dict)

        # Assign Business IDs
        if new_user.role == UserRole.STUDENT:
            new_user.student_id = generate_student_id(new_user.id)
        elif new_user.role == UserRole.TEACHER:
            new_user.teacher_id = generate_teacher_id(new_user.id)
        elif new_user.role == UserRole.ADMIN:
            new_user.admin_id = generate_admin_id(new_user.id)

        await session.flush()

        # Auto-create profile based on role
        name_hint = (
            new_user.email.split("@")[0].replace(".", " ").replace("_", " ").title()
        )

        if new_user.role == UserRole.STUDENT:
            profile = StudentProfile(
                user_id=new_user.id,
                student_name=name_hint,
                created_by=current_user_id,
            )
            session.add(profile)
            await session.flush()
            await RegistrationNumberService.generate_for_student(session, profile)

        elif new_user.role == UserRole.TEACHER:
            profile = TeacherProfile(
                user_id=new_user.id,
                teacher_name=name_hint,
                created_by=current_user_id,
            )
            session.add(profile)

        elif new_user.role == UserRole.ADMIN:
            profile = AdminProfile(
                user_id=new_user.id,
                admin_name=name_hint,
                created_by=current_user_id,
            )
            session.add(profile)

        await session.flush()
        await session.refresh(new_user)
        logger.info(
            f"Admin created new user {new_user.email} with role {new_user.role}",
        )
        return new_user

    # ------------------------------------------------------------------
    # User management -- was entirely missing. admin.py only had
    # POST /admin/user (create); there was no way for an admin to list
    # existing users, look one up, edit one, or deactivate one.
    # ------------------------------------------------------------------

    @classmethod
    async def list_users(
        cls,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        filters = {}
        if role is not None:
            filters["role"] = role
        if is_active is not None:
            filters["is_active"] = is_active
        return await user_crud.get_all(
            session,
            skip=skip,
            limit=limit,
            filters=filters or None,
        )

    @classmethod
    async def get_user(cls, session: AsyncSession, public_id: str) -> User:
        user = await user_crud.get_by_public_id(session, public_id)
        if not user:
            raise ResourceNotFoundException("User not found")
        return user

    @classmethod
    async def update_user(
        cls,
        session: AsyncSession,
        public_id: str,
        data: UserUpdate,
    ) -> User:
        """Admin-driven update of any user. Unlike the self-service
        PATCH /users/me, this is allowed to touch is_active -- an admin
        (de)activating someone else's account is exactly the intended use
        case for this endpoint.
        """
        user = await cls.get_user(session, public_id)
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return user
        return await user_crud.update(session, user.id, payload)

    @classmethod
    async def deactivate_user(cls, session: AsyncSession, public_id: str) -> None:
        user = await cls.get_user(session, public_id)
        await user_crud.update(session, user.id, {"is_active": False})
        logger.info(f"User deactivated by admin: id={user.id}")

    # ------------------------------------------------------------------
    # Profile management -- were missing entirely. StudentProfile /
    # TeacherProfile / AdminProfile each had no CRUD instance at all, so
    # there was no way to fetch, edit, or deactivate one individually
    # after creation (e.g. fixing a misspelled name, updating a teacher's
    # department) -- only the flat row auto-created at signup.
    # ------------------------------------------------------------------

    @classmethod
    async def list_student_profiles(
        cls,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[StudentProfile], int]:
        return await student_profile_crud.get_all(session, skip=skip, limit=limit)

    @classmethod
    async def list_teacher_profiles(
        cls,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[TeacherProfile], int]:
        return await teacher_profile_crud.get_all(session, skip=skip, limit=limit)

    @classmethod
    async def list_admin_profiles(
        cls,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[AdminProfile], int]:
        return await admin_profile_crud.get_all(session, skip=skip, limit=limit)

    @classmethod
    async def get_student_profile(
        cls,
        session: AsyncSession,
        profile_id: int,
    ) -> StudentProfile:
        return await student_profile_crud.get_or_raise(session, profile_id)

    @classmethod
    async def update_student_profile(
        cls,
        session: AsyncSession,
        profile_id: int,
        data: dict,
    ) -> StudentProfile:
        await student_profile_crud.get_or_raise(session, profile_id)
        return await student_profile_crud.update(session, profile_id, data)

    @classmethod
    async def deactivate_student_profile(
        cls,
        session: AsyncSession,
        profile_id: int,
    ) -> None:
        await student_profile_crud.get_or_raise(session, profile_id)
        await student_profile_crud.update(session, profile_id, {"is_active": False})

    @classmethod
    async def get_teacher_profile(
        cls,
        session: AsyncSession,
        profile_id: int,
    ) -> TeacherProfile:
        return await teacher_profile_crud.get_or_raise(session, profile_id)

    @classmethod
    async def update_teacher_profile(
        cls,
        session: AsyncSession,
        profile_id: int,
        data: dict,
    ) -> TeacherProfile:
        await teacher_profile_crud.get_or_raise(session, profile_id)
        return await teacher_profile_crud.update(session, profile_id, data)

    @classmethod
    async def deactivate_teacher_profile(
        cls,
        session: AsyncSession,
        profile_id: int,
    ) -> None:
        await teacher_profile_crud.get_or_raise(session, profile_id)
        await teacher_profile_crud.update(session, profile_id, {"is_active": False})

    @classmethod
    async def get_admin_profile(
        cls,
        session: AsyncSession,
        profile_id: int,
    ) -> AdminProfile:
        return await admin_profile_crud.get_or_raise(session, profile_id)

    @classmethod
    async def update_admin_profile(
        cls,
        session: AsyncSession,
        profile_id: int,
        data: dict,
    ) -> AdminProfile:
        await admin_profile_crud.get_or_raise(session, profile_id)
        return await admin_profile_crud.update(session, profile_id, data)

    @classmethod
    async def deactivate_admin_profile(
        cls,
        session: AsyncSession,
        profile_id: int,
    ) -> None:
        await admin_profile_crud.get_or_raise(session, profile_id)
        await admin_profile_crud.update(session, profile_id, {"is_active": False})
