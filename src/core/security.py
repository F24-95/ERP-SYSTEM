import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from src.core.exceptions import AuthenticationException

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Please set it in your .env file or environment. "
        "Example: SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')",
    )


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # jti (unique token id) lets a specific issued token be revoked on
    # logout without needing to invalidate every token for the user --
    # see src/domain/auth/models.py::RevokedToken.
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    """Verify standard access or refresh tokens and return the payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if "sub" not in payload:
            raise AuthenticationException("Invalid token payload")
        return payload
    except JWTError as e:
        raise AuthenticationException(f"Token validation failed: {e!s}")


def decode_token_ignoring_expiry(token: str) -> dict[str, Any] | None:
    """Used only by logout: we still want to record an *expired* token's
    jti as revoked (harmless -- it'll fail on expiry anyway) but must not
    blow up if the client sends a garbage/expired string. Returns None on
    any decode failure instead of raising, since logout should be
    best-effort and never block the client from clearing its local state.
    """
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
    except JWTError:
        return None


def create_auth_tokens(user_id: int, role: str) -> dict[str, str]:
    payload = {"sub": str(user_id), "role": role}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    return {"access_token": access_token, "refresh_token": refresh_token}


def create_purpose_token(user_id: int, purpose: str, expires_minutes: int) -> str:
    """A short-lived, single-use-by-convention token for out-of-band flows
    like password reset (clicked from an email link, not sent as a normal
    Authorization header). Distinct from access/refresh tokens via the
    `purpose` claim, which callers must check before honoring it -- this
    prevents a reset link from being usable as a regular access token.
    "Single-use" is enforced by the caller recording its `jti` in
    RevokedToken immediately after it's consumed (see AuthService.reset_password).
    """
    payload = {"sub": str(user_id), "purpose": purpose}
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def generate_otp(length: int = 6) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(length))
