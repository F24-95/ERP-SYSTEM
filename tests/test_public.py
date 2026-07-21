import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.domain.users.models import User
from src.core.enums import UserRole
from .helpers import (
    assert_success_response,
    assert_error_response,
    INVALID_EMAILS,
    SQL_INJECTION_PAYLOADS,
    XSS_PAYLOADS,
)


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert_success_response(response)
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"

    async def test_health_check_no_auth_required(self, client: AsyncClient):
        response = await client.get("/health", headers={"Authorization": ""})
        assert_success_response(response)


@pytest.mark.asyncio
class TestLoginEndpoint:
    async def test_login_success(self, client: AsyncClient, db: AsyncSession):

        user = User(
            email="logintest@test.com",
            phone="8888888888",
            password_hash=hash_password("TestPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_deleted=False,
        )
        db.add(user)
        await db.commit()
    
        response = await client.post(
            "/auth/login",
            json={
                "email": "logintest@test.com",
                "password": "TestPass123!",
            },
        )
        assert_success_response(response)
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data

    async def test_login_invalid_credentials(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "wrongpassword",
            },
        )
        assert_error_response(response, 401)

    async def test_login_missing_password(self, client: AsyncClient):
        response = await client.post("/auth/login", json={"email": "test@test.com"})
        assert_error_response(response, 422)

    async def test_login_missing_email(self, client: AsyncClient):
        response = await client.post("/auth/login", json={"password": "test123"})
        assert_error_response(response, 422)

    async def test_login_empty_email(self, client: AsyncClient):
        response = await client.post(
            "/auth/login", json={"email": "", "password": "test123"}
        )
        assert response.status_code in (401, 422)

    async def test_login_empty_password(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={
                "email": "test@test.com",
                "password": "",
            },
        )
        assert_error_response(response, 401)

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_login_sql_injection(self, client: AsyncClient, payload: str):
        response = await client.post(
            "/auth/login",
            json={
                "email": payload,
                "password": payload,
            },
        )
        assert response.status_code in (401, 422)

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    async def test_login_xss(self, client: AsyncClient, payload: str):
        response = await client.post(
            "/auth/login",
            json={
                "email": payload,
                "password": payload,
            },
        )
        assert response.status_code in (401, 422)

    @pytest.mark.parametrize("email", INVALID_EMAILS)
    async def test_login_invalid_emails(self, client: AsyncClient, email: str):
        response = await client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "test123",
            },
        )
        assert response.status_code in (401, 422)


@pytest.mark.asyncio
class TestTokenEndpoint:
    async def test_token_oauth2(self, client: AsyncClient, db: AsyncSession):

        user = User(
            email="tokenuser@test.com",
            phone="7777777777",
            password_hash=hash_password("TokenPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_deleted=False,
        )
        db.add(user)
        await db.commit()
    
        response = await client.post(
            "/auth/token",
            data={
                "username": "tokenuser@test.com",
                "password": "TokenPass123!",
            },
        )
        assert_success_response(response)
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_token_wrong_password(self, client: AsyncClient):
        response = await client.post(
            "/auth/token",
            data={
                "username": "any@test.com",
                "password": "wrong",
            },
        )
        assert_error_response(response, 401)


@pytest.mark.asyncio
class TestForgotPasswordEndpoint:
    async def test_forgot_password_always_204(self, client: AsyncClient):
        response = await client.post(
            "/auth/forgot-password",
            json={
                "email": "any@test.com",
            },
        )
        assert_success_response(response, 204)

    async def test_forgot_password_no_email_leakage(
        self, client: AsyncClient, db: AsyncSession
    ):

        user = User(
            email="existing@test.com",
            phone="6666666666",
            password_hash=hash_password("test123"),
            role=UserRole.TEACHER,
            is_active=True,
            is_deleted=False,
        )
        db.add(user)
        await db.commit()

        response_existing = await client.post(
            "/auth/forgot-password",
            json={
                "email": "existing@test.com",
            },
        )
        response_nonexisting = await client.post(
            "/auth/forgot-password",
            json={
                "email": "nonexisting@test.com",
            },
        )
        assert response_existing.status_code == 204
        assert response_nonexisting.status_code == 204

    async def test_forgot_password_missing_email(self, client: AsyncClient):
        response = await client.post("/auth/forgot-password", json={})
        assert_error_response(response, 422)

    async def test_forgot_password_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/auth/forgot-password", json={"email": "notanemail"}
        )
        assert response.status_code in (204, 422)

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_forgot_password_sql_injection(
        self, client: AsyncClient, payload: str
    ):
        response = await client.post("/auth/forgot-password", json={"email": payload})
        assert response.status_code in (204, 422)


@pytest.mark.asyncio
class TestResetPasswordEndpoint:
    async def test_reset_password_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/auth/reset-password",
            json={
                "token": "invalid-token",
                "new_password": "NewPass123!",
            },
        )
        assert_error_response(response, 401)

    async def test_reset_password_missing_fields(self, client: AsyncClient):
        response = await client.post("/auth/reset-password", json={})
        assert_error_response(response, 422)

    async def test_reset_password_weak_password(self, client: AsyncClient):
        response = await client.post(
            "/auth/reset-password",
            json={
                "token": "some-token",
                "new_password": "123",
            },
        )
        assert response.status_code in (401, 422)


@pytest.mark.asyncio
class TestSendLoginOtpEndpoint:
    async def test_send_login_otp_always_204(self, client: AsyncClient):
        response = await client.post(
            "/auth/send-login-otp",
            json={
                "email": "any@test.com",
            },
        )
        assert_success_response(response, 204)

    async def test_send_login_otp_no_email_leakage(self, client: AsyncClient):
        response_existing = await client.post(
            "/auth/send-login-otp",
            json={
                "email": "exists@test.com",
            },
        )
        response_not = await client.post(
            "/auth/send-login-otp",
            json={
                "email": "notexists@test.com",
            },
        )
        assert response_existing.status_code == 204
        assert response_not.status_code == 204

    async def test_send_login_otp_missing_email(self, client: AsyncClient):
        response = await client.post("/auth/send-login-otp", json={})
        assert_error_response(response, 422)


@pytest.mark.asyncio
class TestVerifyLoginOtpEndpoint:
    async def test_verify_login_otp_invalid_otp(self, client: AsyncClient):
        response = await client.post(
            "/auth/verify-login-otp",
            json={
                "email": "test@test.com",
                "otp": "000000",
            },
        )
        assert_error_response(response, 401)

    async def test_verify_login_otp_missing_fields(self, client: AsyncClient):
        response = await client.post("/auth/verify-login-otp", json={})
        assert_error_response(response, 422)

    async def test_verify_login_otp_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/auth/verify-login-otp",
            json={
                "email": "notvalid",
                "otp": "123456",
            },
        )
        assert response.status_code in (401, 422)


@pytest.mark.asyncio
class TestRefreshTokenEndpoint:
    async def test_refresh_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/auth/refresh",
            json={
                "refresh_token": "invalid-token-here",
            },
        )
        assert_error_response(response, 401)

    async def test_refresh_missing_token(self, client: AsyncClient):
        response = await client.post("/auth/refresh", json={})
        assert_error_response(response, 422)

    async def test_refresh_empty_token(self, client: AsyncClient):
        response = await client.post("/auth/refresh", json={"refresh_token": ""})
        assert_error_response(response, 401)


@pytest.mark.asyncio
class TestLogoutEndpoint:
    async def test_logout_without_token(self, client: AsyncClient):
        response = await client.post("/auth/logout", json={"refresh_token": ""})
        assert_error_response(response, 401)

    async def test_logout_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/auth/logout",
            json={"refresh_token": ""},
            headers={"Authorization": "Bearer invalid"},
        )
        assert_error_response(response, 401)


@pytest.mark.asyncio
class TestValidateTokenEndpoint:
    async def test_validate_without_token(self, client: AsyncClient):
        response = await client.get("/auth/validate-token")
        assert_error_response(response, 401)

    async def test_validate_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/auth/validate-token",
            headers={"Authorization": "Bearer invalid"},
        )
        assert_error_response(response, 401)
