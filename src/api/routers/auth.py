from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, oauth2_scheme
from src.database.connection import get_db
from src.domain.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ResetPasswordRequest,
    SendLoginOtpRequest,
    ValidateTokenResponse,
    VerifyEmailRequest,
    VerifyLoginOtpRequest,
)
from src.domain.auth.service import AuthService
from src.domain.users.models import User
from src.domain.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user with email or phone and password."""
    return await AuthService.login(db, request.email, request.password)


@router.post("/token", include_in_schema=False)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2 password form compatible login endpoint."""
    response = await AuthService.login(db, form_data.username, form_data.password)
    return {
        "access_token": response["access_token"],
        "token_type": "bearer",
        "refresh_token": response["refresh_token"],
    }


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token."""
    return await AuthService.refresh(db, request.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: LogoutRequest,
    access_token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the current access token (and refresh token, if supplied)."""
    await AuthService.logout(db, access_token, request.refresh_token)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the authenticated user's password."""
    await AuthService.change_password(
        db,
        current_user,
        request.old_password,
        request.new_password,
    )


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a password reset email token."""
    await AuthService.forgot_password(db, request.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using a valid reset purpose-token."""
    await AuthService.reset_password(db, request.token, request.new_password)


@router.post("/send-verification-otp", status_code=status.HTTP_204_NO_CONTENT)
async def send_verification_otp(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send an email verification OTP to the authenticated user."""
    await AuthService.send_verification_otp(db, current_user)


@router.post("/resend-otp", status_code=status.HTTP_204_NO_CONTENT)
async def resend_otp(
    purpose: str = "email_verify",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resend an OTP. purpose="email_verify" (default) or "login"."""
    await AuthService.resend_otp(db, current_user, purpose=purpose)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    request: VerifyEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify email address with the OTP."""
    await AuthService.verify_email(db, current_user, request.otp)


@router.post("/send-login-otp", status_code=status.HTTP_204_NO_CONTENT)
async def send_login_otp(
    request: SendLoginOtpRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send OTP for passwordless login."""
    await AuthService.send_login_otp(db, request.email)


@router.post("/verify-login-otp", response_model=LoginResponse)
async def verify_login_otp(
    request: VerifyLoginOtpRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange login OTP for auth tokens and profile data."""
    tokens = await AuthService.verify_login_otp(db, request.email, request.otp)
    from src.domain.users.crud import user_crud
    user = await user_crud.get_by_email(db, request.email.lower().strip())
    profile_data = await AuthService.get_user_profile_data(db, user)
    return {
        **tokens,
        "user": UserResponse.model_validate(user).model_dump(),
        "profile": profile_data,
    }


@router.get("/validate-token", response_model=ValidateTokenResponse)
async def validate_token(current_user: User = Depends(get_current_user)):
    """Lightweight check to verify active token validity."""
    return ValidateTokenResponse(
        valid=True,
        user_id=current_user.id,
        role=current_user.role.value,
        public_id=current_user.public_id,
    )
