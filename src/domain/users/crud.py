from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base_crud import AsyncBaseCRUD
from src.domain.users.models import AdminProfile, StudentProfile, TeacherProfile, User


class UserCRUD(AsyncBaseCRUD[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        query = select(self.model).filter_by(email=email, is_deleted=False)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_by_public_id(
        self,
        session: AsyncSession,
        public_id: str,
    ) -> User | None:
        query = select(self.model).filter_by(public_id=public_id, is_deleted=False)
        result = await session.execute(query)
        return result.scalars().first()


user_crud = UserCRUD()

# Were missing entirely -- StudentProfile/TeacherProfile/AdminProfile had
# no CRUD instances at all, so there was no admin-facing way to fetch,
# edit, or deactivate a profile individually (e.g. fixing a misspelled
# student_name after creation) -- only the flat auto-created-at-signup
# row, plus each user's own self-service /users/me update (which doesn't
# touch profile fields at all, only User.phone).
student_profile_crud = AsyncBaseCRUD[StudentProfile](StudentProfile)
teacher_profile_crud = AsyncBaseCRUD[TeacherProfile](TeacherProfile)
admin_profile_crud = AsyncBaseCRUD[AdminProfile](AdminProfile)
