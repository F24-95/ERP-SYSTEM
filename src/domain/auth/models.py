from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from src.database.connection import Base


class RevokedToken(Base):
    """Backs POST /auth/logout. The system is otherwise pure stateless JWT
    (no session store), so without this table there was no way to
    invalidate a token before its natural expiry -- "logging out" would
    have done nothing server-side. Rows are looked up by `jti` (a random
    id embedded in every issued token, see core/security.py) on every
    authenticated request via get_current_user, so keep this table small:
    a cleanup job deleting rows where expires_at < now() is recommended in
    production, but isn't wired up here since no scheduler/cron infra exists
    yet in this project.
    """

    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(36), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)


class OtpCode(Base):
    """Backs the OTP-based auth flows (email verification + passwordless
    OTP login). core/email.py already had send_otp_email() fully
    implemented and core/security.py already had generate_otp(), but
    there was nowhere to persist an issued OTP so it could later be
    checked -- meaning none of that infrastructure could actually be
    wired into a working endpoint. The plaintext code is never stored,
    only its hash (via the same bcrypt helper used for passwords), so a
    DB read alone can't leak a valid code.
    """

    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code_hash = Column(String(255), nullable=False)
    purpose = Column(String(30), nullable=False, index=True)  # "email_verify" | "login"
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
