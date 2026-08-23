from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: str  # Can be email or phone
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: dict[str, Any]
    profile: dict[str, Any] | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


def _validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not any(c.isupper() for c in value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one digit")
    return value


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class VerifyEmailRequest(BaseModel):
    otp: str = Field(..., min_length=4, max_length=10)


class SendLoginOtpRequest(BaseModel):
    email: EmailStr


class VerifyLoginOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=10)


class ValidateTokenResponse(BaseModel):
    valid: bool
    user_id: int
    role: str
    public_id: str
