from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base_crud import AsyncBaseCRUD
from src.domain.auth.models import OtpCode, RevokedToken


class RevokedTokenCRUD(AsyncBaseCRUD[RevokedToken]):
    async def is_revoked(self, session: AsyncSession, jti: str) -> bool:
        result = await session.execute(select(RevokedToken).filter_by(jti=jti))
        return result.scalars().first() is not None


class OtpCodeCRUD(AsyncBaseCRUD[OtpCode]):
    async def get_latest_unused(
        self,
        session: AsyncSession,
        user_id: int,
        purpose: str,
    ):
        result = await session.execute(
            select(OtpCode)
            .filter_by(
                user_id=user_id,
                purpose=purpose,
                is_used=False,
            )
            .order_by(OtpCode.id.desc()),
        )
        return result.scalars().first()


revoked_token_crud = RevokedTokenCRUD(RevokedToken)
otp_code_crud = OtpCodeCRUD(OtpCode)
