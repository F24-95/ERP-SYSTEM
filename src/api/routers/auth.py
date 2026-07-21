from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, oauth2_scheme
from src.core.enums import UserRole
from src.core.exceptions import AuthenticationException
from src.core.security import (
    create_access_token,
    create_auth_tokens,
    verify_password,
    verify_token,
)
from src.database.connection import get_db
from src.domain.auth.crud import revoked_token_crud
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
from src.domain.users.models import AdminProfile, StudentProfile, TeacherProfile, User
from src.domain.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_user_profile_data(db: AsyncSession, user: User) -> dict:
    profile_data = {}
    if user.role == UserRole.STUDENT:
        res = await db.execute(select(StudentProfile).filter_by(user_id=user.id))
        prof = res.scalars().first()
        if prof:
            profile_data = {
                "student_name": prof.student_name,
                "admission_number": prof.admission_number,
            }
    elif user.role == UserRole.TEACHER:
        res = await db.execute(select(TeacherProfile).filter_by(user_id=user.id))
        prof = res.scalars().first()
        if prof:
            profile_data = {
                "teacher_name": prof.teacher_name,
                "employee_code": prof.employee_code,
            }
    elif user.role == UserRole.ADMIN:
        res = await db.execute(select(AdminProfile).filter_by(user_id=user.id))
        prof = res.scalars().first()
        if prof:
            profile_data = {"admin_name": prof.admin_name}
    return profile_data


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(User).filter(
            or_(
                User.email == request.email.lower().strip(),
                User.phone == request.email.strip(),
            ),
        ),
    )
    user = res.scalars().first()

    if not user or not verify_password(request.password, user.password_hash):
        if user:
            user.failed_login_count += 1
            # Use flush instead of commit — get_db dependency handles the final commit
            await db.flush()
        raise AuthenticationException("Invalid credentials")

    if not user.is_active or user.is_deleted:
        raise AuthenticationException("Account is disabled or deleted")

    user.failed_login_count = 0
    user.login_count += 1
    # Use flush instead of commit — get_db dependency handles the final commit
    await db.flush()

    tokens = create_auth_tokens(user.id, user.role.value)
    profile_data = await get_user_profile_data(db, user)

    return {
        **tokens,
        "user": UserResponse.model_validate(user).model_dump(),
        "profile": profile_data,
    }


@router.post("/token", include_in_schema=False)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    request = LoginRequest(email=form_data.username, password=form_data.password)
    response = await login(request, db)
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
    payload = verify_token(request.refresh_token)
    user_id = payload.get("sub")

    # A revoked refresh token (e.g. from a prior /auth/logout) must not be
    # able to keep minting new access tokens forever -- this check was
    # missing entirely before token revocation existed at all.
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
        "refresh_token": request.refresh_token,
        "token_type": "bearer",
        "expires_in": 3600,
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: LogoutRequest,
    access_token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the current access token (and refresh token, if supplied).
    Was missing entirely -- there was no way to invalidate a token before
    its natural expiry, so a logged-out or compromised token kept working
    until it expired on its own.
    """
    await AuthService.logout(db, access_token, request.refresh_token)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Was missing entirely -- once created, a user had no self-service way
    to change their own password.
    """
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
    """Was missing entirely -- core/email.py's send_reset_email() was fully
    implemented but nothing called it. Always returns 204 regardless of
    whether the email is registered, to avoid leaking which emails exist.
    """
    await AuthService.forgot_password(db, request.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Consumes the token sent by /forgot-password (single-use, ~30 min
    expiry) and sets a new password.
    """
    await AuthService.reset_password(db, request.token, request.new_password)


@router.post("/send-verification-otp", status_code=status.HTTP_204_NO_CONTENT)
async def send_verification_otp(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Was missing entirely -- generate_otp() and send_otp_email() both
    already existed with nothing wiring them together, and User had no
    is_verified column to record the result on (added in this pass).
    """
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
    """Consumes the OTP sent by /send-verification-otp and marks the
    account verified.
    """
    await AuthService.verify_email(db, current_user, request.otp)


@router.post("/send-login-otp", status_code=status.HTTP_204_NO_CONTENT)
async def send_login_otp(
    request: SendLoginOtpRequest,
    db: AsyncSession = Depends(get_db),
):
    """Passwordless login, step 1: email an OTP. Was missing entirely --
    a common pattern for a school ERP where a parent/student may not want
    to remember a password. Public endpoint (no auth) since this *is* a
    login mechanism; always returns 204 regardless of whether the email
    is registered, same anti-enumeration reasoning as /forgot-password.
    """
    await AuthService.send_login_otp(db, request.email)


@router.post("/verify-login-otp", response_model=LoginResponse)
async def verify_login_otp(
    request: VerifyLoginOtpRequest,
    db: AsyncSession = Depends(get_db),
):
    """Passwordless login, step 2: exchange the OTP for access/refresh
    tokens, same response shape as POST /auth/login.
    """
    tokens = await AuthService.verify_login_otp(db, request.email, request.otp)
    res = await db.execute(select(User).filter_by(email=request.email.lower().strip()))
    user = res.scalars().first()
    profile_data = await get_user_profile_data(db, user)
    return {
        **tokens,
        "user": UserResponse.model_validate(user).model_dump(),
        "profile": profile_data,
    }


@router.get("/validate-token", response_model=ValidateTokenResponse)
async def validate_token(current_user: User = Depends(get_current_user)):
    """Was missing entirely -- a lightweight way for a client to check
    "is my stored token still good" (e.g. on app startup) without needing
    to call a heavier endpoint like /users/me and infer validity from
    whether it 401s.
    """
    return ValidateTokenResponse(
        valid=True,
        user_id=current_user.id,
        role=current_user.role.value,
        public_id=current_user.public_id,
    )
