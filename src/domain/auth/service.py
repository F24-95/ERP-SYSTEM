import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.email import send_otp_email, send_reset_email
from src.core.enums import UserRole
from src.core.exceptions import (
    AuthenticationException,
    BusinessLogicException,
    ResourceNotFoundException,
)
from src.core.logger import get_logger
from src.core.security import (
    create_access_token,
    create_auth_tokens,
    create_purpose_token,
    decode_token_ignoring_expiry,
    generate_otp,
    hash_password,
    verify_password,
    verify_purpose_token,
    verify_token,
)
from src.domain.auth.crud import otp_code_crud, revoked_token_crud
from src.domain.users.crud import user_crud
from src.domain.users.models import (
    AdminProfile,
    StudentProfile,
    TeacherProfile,
    User,
)
from src.domain.users.schemas import UserResponse

logger = get_logger(__name__)

RESET_TOKEN_EXPIRE_MINUTES = 30
OTP_EXPIRE_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class AuthService:
    @staticmethod
    async def get_user_profile_data(db: AsyncSession, user: User) -> dict:
        """Fetch role-specific profile information for the user."""
        profile_data = {}
        if user.role == UserRole.STUDENT:
            res = await db.execute(
                select(StudentProfile).filter_by(user_id=user.id),
            )
            prof = res.scalars().first()
            if prof:
                profile_data = {
                    "student_name": prof.student_name,
                    "admission_number": prof.admission_number,
                }
        elif user.role == UserRole.TEACHER:
            res = await db.execute(
                select(TeacherProfile).filter_by(user_id=user.id),
            )
            prof = res.scalars().first()
            if prof:
                profile_data = {
                    "teacher_name": prof.teacher_name,
                    "employee_code": prof.employee_code,
                }
        elif user.role == UserRole.ADMIN:
            res = await db.execute(
                select(AdminProfile).filter_by(user_id=user.id),
            )
            prof = res.scalars().first()
            if prof:
                profile_data = {"admin_name": prof.admin_name}
        return profile_data

    @staticmethod
    async def login(
        db: AsyncSession,
        identifier: str,
        password: str,
    ) -> dict:
        """Authenticate user by email or phone, enforce lockout on repeated failures."""
        clean_id = identifier.strip()
        res = await db.execute(
            select(User).filter(
                or_(
                    User.email == clean_id.lower(),
                    User.phone == clean_id,
                ),
            ),
        )
        user = res.scalars().first()

        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

        if user and user.locked_until:
            if user.locked_until > now_utc:
                diff_sec = (user.locked_until - now_utc).total_seconds()
                mins_left = max(1, int(diff_sec // 60) + 1)
                logger.warning(
                    f"Locked user id={user.id} attempted login. "
                    f"Locked for {mins_left} more min.",
                )
                raise AuthenticationException(
                    "Account is temporarily locked due to multiple "
                    "failed login attempts. Please try again in "
                    f"{mins_left} minute(s).",
                )
            else:
                # Lockout expired, reset counter
                user.locked_until = None
                user.failed_login_count = 0
                await db.flush()

        if not user or not verify_password(password, user.password_hash):
            if user:
                user.failed_login_count += 1
                if user.failed_login_count >= MAX_FAILED_LOGIN_ATTEMPTS:
                    user.locked_until = now_utc + timedelta(
                        minutes=LOCKOUT_DURATION_MINUTES,
                    )
                    logger.warning(
                        f"User id={user.id} reached "
                        f"{user.failed_login_count} failed logins. "
                        f"Locked until {user.locked_until}",
                    )
                await db.flush()
            raise AuthenticationException("Invalid credentials")

        if not user.is_active or user.is_deleted:
            raise AuthenticationException("Account is disabled or deleted")

        user.failed_login_count = 0
        user.locked_until = None
        user.login_count += 1
        user.last_login = now_utc
        await db.flush()

        tokens = create_auth_tokens(user.id, user.role.value)
        profile_data = await AuthService.get_user_profile_data(db, user)

        return {
            **tokens,
            "user": UserResponse.model_validate(user).model_dump(),
            "profile": profile_data,
        }

    @staticmethod
    async def refresh(db: AsyncSession, refresh_token: str) -> dict:
        """Validate refresh token and mint a new access token."""
        payload = verify_token(refresh_token)
        user_id = payload.get("sub")

        jti = payload.get("jti")
        if jti and await revoked_token_crud.is_revoked(db, jti):
            raise AuthenticationException("Refresh token has been revoked")

        res = await db.execute(select(User).filter_by(id=int(user_id)))
        user = res.scalars().first()

        if not user or not user.is_active or user.is_deleted:
            raise AuthenticationException("User not found or inactive")

        new_access_token = create_access_token(
            {"sub": str(user.id), "role": user.role.value},
        )

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,
        }

    @staticmethod
    async def _revoke(db: AsyncSession, token: str) -> None:
        payload = decode_token_ignoring_expiry(token)
        if not payload:
            return
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            return
        if await revoked_token_crud.is_revoked(db, jti):
            return
        await revoked_token_crud.create(
            db,
            {
                "jti": jti,
                "expires_at": datetime.fromtimestamp(
                    exp,
                    tz=timezone.utc,
                ).replace(tzinfo=None),
            },
        )

    @staticmethod
    async def logout(
        db: AsyncSession,
        access_token: str,
        refresh_token: str = None,
    ) -> None:
        """Revokes the current access token, and the refresh token too if supplied."""
        await AuthService._revoke(db, access_token)
        if refresh_token:
            await AuthService._revoke(db, refresh_token)
        logger.info("User logged out, token(s) revoked")

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        old_password: str,
        new_password: str,
    ) -> None:
        """Self-service password update."""
        if not verify_password(old_password, user.password_hash):
            raise AuthenticationException("Current password is incorrect")
        if old_password == new_password:
            raise BusinessLogicException(
                "New password must be different from the current password",
            )
        await user_crud.update(
            db,
            user.id,
            {"password_hash": hash_password(new_password)},
        )
        logger.info(f"Password changed for user id={user.id}")

    @staticmethod
    async def forgot_password(db: AsyncSession, email: str) -> None:
        """Always returns success regardless of whether the email exists to prevent enumeration."""
        user = await user_crud.get_by_email(db, email)
        if not user or not user.is_active or user.is_deleted:
            logger.info(
                f"Password reset requested for unknown/inactive email={email}",
            )
            return

        token = create_purpose_token(
            user.id,
            purpose="password_reset",
            expires_minutes=RESET_TOKEN_EXPIRE_MINUTES,
        )
        link = f"{FRONTEND_URL}/reset-password?token={token}"
        sent = await send_reset_email(user.email, link)
        if not sent:
            logger.error(
                f"Failed to send password reset email to "
                f"user id={user.id} ({user.email})",
            )
        else:
            logger.info(f"Password reset email sent to user id={user.id}")

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str,
    ) -> None:
        try:
            payload = verify_purpose_token(token, "password_reset")
        except AuthenticationException:
            raise AuthenticationException("Reset link is invalid or has expired")

        jti = payload.get("jti")
        if jti and await revoked_token_crud.is_revoked(db, jti):
            raise AuthenticationException("This reset link has already been used")

        user = await user_crud.get(db, int(payload["sub"]))
        if not user or not user.is_active or user.is_deleted:
            raise ResourceNotFoundException("User not found or inactive")

        await user_crud.update(
            db,
            user.id,
            {
                "password_hash": hash_password(new_password),
                "failed_login_count": 0,
                "locked_until": None,
            },
        )

        # Burn the token so the same email link can't be reused.
        if jti:
            await revoked_token_crud.create(
                db,
                {
                    "jti": jti,
                    "expires_at": datetime.fromtimestamp(
                        payload["exp"],
                        tz=timezone.utc,
                    ).replace(tzinfo=None),
                },
            )
        logger.info(f"Password reset completed for user id={user.id}")

    @staticmethod
    async def _issue_otp(
        db: AsyncSession,
        user: User,
        purpose: str,
    ) -> str:
        code = generate_otp()
        await otp_code_crud.create(
            db,
            {
                "user_id": user.id,
                "code_hash": hash_password(code),
                "purpose": purpose,
                "expires_at": datetime.now(timezone.utc).replace(tzinfo=None)
                + timedelta(minutes=OTP_EXPIRE_MINUTES),
                "is_used": False,
            },
        )
        return code

    @staticmethod
    async def send_verification_otp(db: AsyncSession, user: User) -> None:
        if user.is_verified:
            raise BusinessLogicException("Email is already verified")
        code = await AuthService._issue_otp(db, user, purpose="email_verify")
        sent = await send_otp_email(user.email, code, purpose="verification")
        if not sent:
            logger.error(f"Failed to send verification OTP to user id={user.id}")
        else:
            logger.info(f"Verification OTP sent to user id={user.id}")

    @staticmethod
    async def resend_otp(
        db: AsyncSession,
        user: User,
        purpose: str = "email_verify",
    ) -> None:
        if purpose == "email_verify":
            await AuthService.send_verification_otp(db, user)
        elif purpose == "login":
            await AuthService.send_login_otp(db, user.email)
        else:
            raise BusinessLogicException(f"Unknown OTP purpose: {purpose}")

    @staticmethod
    async def _verify_otp(
        db: AsyncSession,
        user: User,
        purpose: str,
        code: str,
    ) -> None:
        otp = await otp_code_crud.get_latest_unused(db, user.id, purpose)
        if not otp:
            raise AuthenticationException(
                "No active OTP found. Please request a new one.",
            )
        if datetime.now(timezone.utc).replace(tzinfo=None) > otp.expires_at:
            raise AuthenticationException(
                "OTP has expired. Please request a new one.",
            )
        if not verify_password(code, otp.code_hash):
            if hasattr(otp, "attempts"):
                otp.attempts = getattr(otp, "attempts", 0) + 1
                if otp.attempts >= OTP_MAX_ATTEMPTS:
                    await otp_code_crud.update(
                        db,
                        otp.id,
                        {"is_used": True},
                    )
                    raise AuthenticationException(
                        "Too many failed attempts. "
                        "Please request a new OTP.",
                    )
                await db.flush()
            raise AuthenticationException("Invalid OTP")
        await otp_code_crud.update(db, otp.id, {"is_used": True})

    @staticmethod
    async def verify_email(
        db: AsyncSession,
        user: User,
        otp: str,
    ) -> None:
        await AuthService._verify_otp(db, user, "email_verify", otp)
        await user_crud.update(db, user.id, {"is_verified": True})
        logger.info(f"Email verified for user id={user.id}")

    @staticmethod
    async def send_login_otp(db: AsyncSession, email: str) -> None:
        """Anti-enumeration passwordless login OTP dispatch."""
        user = await user_crud.get_by_email(db, email)
        if not user or not user.is_active or user.is_deleted:
            logger.info(
                f"Login OTP requested for unknown/inactive email={email}",
            )
            return
        code = await AuthService._issue_otp(db, user, purpose="login")
        sent = await send_otp_email(user.email, code, purpose="login")
        if not sent:
            logger.error(f"Failed to send login OTP to user id={user.id}")
        else:
            logger.info(f"Login OTP sent to user id={user.id}")

    @staticmethod
    async def verify_login_otp(
        db: AsyncSession,
        email: str,
        otp: str,
    ) -> dict:
        user = await user_crud.get_by_email(db, email)
        if not user or not user.is_active or user.is_deleted:
            raise AuthenticationException("Invalid OTP")

        await AuthService._verify_otp(db, user, "login", otp)

        user.login_count += 1
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.flush()

        tokens = create_auth_tokens(user.id, user.role.value)
        logger.info(f"User id={user.id} logged in via OTP")
        return tokens
