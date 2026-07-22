import os
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.email import send_otp_email, send_reset_email
from src.core.exceptions import (
    AuthenticationException,
    BusinessLogicException,
    ResourceNotFoundException,
)
from src.core.logger import get_logger
from src.core.security import (
    create_auth_tokens,
    create_purpose_token,
    decode_token_ignoring_expiry,
    generate_otp,
    hash_password,
    verify_password,
    verify_token,
)
from src.domain.auth.crud import otp_code_crud, revoked_token_crud
from src.domain.users.crud import user_crud
from src.domain.users.models import User

logger = get_logger(__name__)

RESET_TOKEN_EXPIRE_MINUTES = 30
OTP_EXPIRE_MINUTES = 10
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class AuthService:
    @staticmethod
    async def _revoke(db: AsyncSession, token: str) -> None:
        payload = decode_token_ignoring_expiry(token)
        if not payload:
            return
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            # Tokens issued before the jti claim existed have nothing to
            # revoke by -- nothing more we can do for those; they'll just
            # expire naturally.
            return
        if await revoked_token_crud.is_revoked(db, jti):
            return
        await revoked_token_crud.create(
            db,
            {
                "jti": jti,
                "expires_at": datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None),
            },
        )

    @staticmethod
    async def logout(
        db: AsyncSession,
        access_token: str,
        refresh_token: str = None,
    ) -> None:
        """Revokes the current access token, and the refresh token too if
        supplied, so neither can be used again even though both were
        already validly issued (previously: nothing revoked either --
        a stolen or accidentally-shared token would keep working until it
        naturally expired, with no way to cut it off).
        """
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
        """Was missing entirely -- once a user was created, there was no
        self-service way to change a password, only the admin create-user
        flow which sets it once at creation.
        """
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

    # ------------------------------------------------------------------
    # Forgot / reset password. Was missing entirely -- core/email.py
    # already had send_reset_email() fully implemented, with nothing
    # calling it. Uses a short-lived, purpose-scoped JWT as the reset
    # token (see create_purpose_token) rather than a new DB table, since
    # the existing RevokedToken table can double as the single-use guard:
    # once a reset token is consumed, its jti is recorded there so the
    # same email link can't be replayed.
    # ------------------------------------------------------------------

    @staticmethod
    async def forgot_password(db: AsyncSession, email: str) -> None:
        """Always returns success regardless of whether the email exists --
        confirming/denying an email's existence here would let an attacker
        enumerate registered accounts.
        """
        user = await user_crud.get_by_email(db, email)
        if not user or not user.is_active or user.is_deleted:
            logger.info(f"Password reset requested for unknown/inactive email={email}")
            return

        token = create_purpose_token(
            user.id,
            purpose="password_reset",
            expires_minutes=RESET_TOKEN_EXPIRE_MINUTES,
        )
        link = f"{FRONTEND_URL}/reset-password?token={token}"
        await send_reset_email(user.email, link)
        logger.info(f"Password reset email sent to user id={user.id}")

    @staticmethod
    async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
        try:
            payload = verify_token(token)
        except AuthenticationException:
            raise AuthenticationException("Reset link is invalid or has expired")

        if payload.get("purpose") != "password_reset":
            raise AuthenticationException("Invalid reset token")

        jti = payload.get("jti")
        if jti and await revoked_token_crud.is_revoked(db, jti):
            raise AuthenticationException("This reset link has already been used")

        user = await user_crud.get(db, int(payload["sub"]))
        if not user or not user.is_active or user.is_deleted:
            raise ResourceNotFoundException("User not found or inactive")

        await user_crud.update(
            db,
            user.id,
            {"password_hash": hash_password(new_password)},
        )

        # Burn the token so the same email link can't be reused.
        if jti:
            await revoked_token_crud.create(
                db,
                {
                    "jti": jti,
                    "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None),
                },
            )
        logger.info(f"Password reset completed for user id={user.id}")

    # ------------------------------------------------------------------
    # Email verification (OTP-based). Was missing entirely -- both
    # generate_otp() (core/security.py) and send_otp_email() (core/email.py)
    # already existed with nothing wiring them together, and User had no
    # is_verified column to record the result on (added in this pass).
    # ------------------------------------------------------------------

    @staticmethod
    async def _issue_otp(db: AsyncSession, user: User, purpose: str) -> str:
        code = generate_otp()
        await otp_code_crud.create(
            db,
            {
                "user_id": user.id,
                "code_hash": hash_password(code),
                "purpose": purpose,
                "expires_at": datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=OTP_EXPIRE_MINUTES),
                "is_used": False,
            },
        )
        return code

    @staticmethod
    async def send_verification_otp(db: AsyncSession, user: User) -> None:
        if user.is_verified:
            raise BusinessLogicException("Email is already verified")
        code = await AuthService._issue_otp(db, user, purpose="email_verify")
        await send_otp_email(user.email, code, purpose="verification")
        logger.info(f"Verification OTP sent to user id={user.id}")

    @staticmethod
    async def resend_otp(
        db: AsyncSession,
        user: User,
        purpose: str = "email_verify",
    ) -> None:
        """Functionally identical to send_verification_otp for the
        email_verify purpose -- kept as a separate method (rather than
        just aliasing the router to send_verification_otp) so a future
        "resend" also supporting the login-OTP purpose has somewhere to
        live without another router change.
        """
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
            raise AuthenticationException("OTP has expired. Please request a new one.")
        if not verify_password(code, otp.code_hash):
            raise AuthenticationException("Invalid OTP")
        await otp_code_crud.update(db, otp.id, {"is_used": True})

    @staticmethod
    async def verify_email(db: AsyncSession, user: User, otp: str) -> None:
        await AuthService._verify_otp(db, user, "email_verify", otp)
        await user_crud.update(db, user.id, {"is_verified": True})
        logger.info(f"Email verified for user id={user.id}")

    # ------------------------------------------------------------------
    # Passwordless OTP login. Was missing entirely -- a common pattern
    # for a school ERP where a parent/student may not want to remember a
    # password, alongside (not replacing) the existing password-based login.
    # ------------------------------------------------------------------

    @staticmethod
    async def send_login_otp(db: AsyncSession, email: str) -> None:
        """Same anti-enumeration behavior as forgot_password: always
        returns success regardless of whether the email exists.
        """
        user = await user_crud.get_by_email(db, email)
        if not user or not user.is_active or user.is_deleted:
            logger.info(f"Login OTP requested for unknown/inactive email={email}")
            return
        code = await AuthService._issue_otp(db, user, purpose="login")
        await send_otp_email(user.email, code, purpose="login")
        logger.info(f"Login OTP sent to user id={user.id}")

    @staticmethod
    async def verify_login_otp(db: AsyncSession, email: str, otp: str) -> dict:
        user = await user_crud.get_by_email(db, email)
        if not user or not user.is_active or user.is_deleted:
            raise AuthenticationException(
                "Invalid OTP",
            )  # deliberately same message as a bad code

        await AuthService._verify_otp(db, user, "login", otp)

        user.login_count += 1
        await db.flush()

        tokens = create_auth_tokens(user.id, user.role.value)
        logger.info(f"User id={user.id} logged in via OTP")
        return tokens
