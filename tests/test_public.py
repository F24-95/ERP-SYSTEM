import pytest
from httpx import AsyncClient

from tests.helpers import (
    assert_no_content,
    assert_ok,
    assert_unauthorized,
)

pytestmark = pytest.mark.asyncio


class TestHealth:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert_ok(response)
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"


class TestAuthLogin:
    async def test_login_success(self, client: AsyncClient, admin_user, db_session):
        response = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "TestPass123!"},
        )
        assert_ok(response)
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@test.com"

    async def test_login_with_phone(self, client: AsyncClient, admin_user):
        response = await client.post(
            "/auth/login",
            json={"email": "9876543210", "password": "TestPass123!"},
        )
        assert_ok(response)
        data = response.json()
        assert "access_token" in data

    async def test_login_invalid_password(self, client: AsyncClient, admin_user):
        response = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "WrongPass"},
        )
        assert_unauthorized(response)

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={"email": "noone@test.com", "password": "TestPass123!"},
        )
        assert_unauthorized(response)

    async def test_login_empty_password(self, client: AsyncClient, admin_user):
        response = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": ""},
        )
        assert_unauthorized(response)


class TestAuthToken:
    async def test_token_endpoint(self, client: AsyncClient, admin_user):
        response = await client.post(
            "/auth/token",
            data={"username": "admin@test.com", "password": "TestPass123!"},
        )
        assert_ok(response)
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestAuthRefresh:
    async def test_refresh_token(self, client: AsyncClient, admin_user):
        login_resp = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "TestPass123!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert_ok(response)
        data = response.json()
        assert "access_token" in data

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert_unauthorized(response)


class TestAuthLogout:
    async def test_logout(self, client: AsyncClient, admin_user, admin_headers):
        response = await client.post(
            "/auth/logout",
            json={"refresh_token": None},
            headers=admin_headers,
        )
        assert_no_content(response)

    async def test_logout_unauthenticated(self, client: AsyncClient):
        response = await client.post(
            "/auth/logout",
            json={"refresh_token": None},
        )
        assert_unauthorized(response)


class TestAuthChangePassword:
    async def test_change_password(
        self, client: AsyncClient, admin_user, admin_headers
    ):
        response = await client.post(
            "/auth/change-password",
            json={"old_password": "TestPass123!", "new_password": "NewPass456!"},
            headers=admin_headers,
        )
        assert_no_content(response)

        login_resp = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "NewPass456!"},
        )
        assert_ok(login_resp)

    async def test_change_password_wrong_old(
        self, client: AsyncClient, admin_user, admin_headers
    ):
        response = await client.post(
            "/auth/change-password",
            json={"old_password": "WrongPass", "new_password": "NewPass456!"},
            headers=admin_headers,
        )
        assert_unauthorized(response)

    async def test_change_password_same_password(
        self, client: AsyncClient, admin_user, admin_headers
    ):
        response = await client.post(
            "/auth/change-password",
            json={"old_password": "TestPass123!", "new_password": "TestPass123!"},
            headers=admin_headers,
        )
        assert response.status_code in (400, 409)

    async def test_change_password_unauthenticated(self, client: AsyncClient):
        response = await client.post(
            "/auth/change-password",
            json={"old_password": "x", "new_password": "y" * 8},
        )
        assert_unauthorized(response)


class TestAuthForgotPassword:
    async def test_forgot_password(self, client: AsyncClient, admin_user):
        response = await client.post(
            "/auth/forgot-password",
            json={"email": "admin@test.com"},
        )
        assert_no_content(response)

    async def test_forgot_password_nonexistent(self, client: AsyncClient):
        response = await client.post(
            "/auth/forgot-password",
            json={"email": "noone@test.com"},
        )
        assert_no_content(response)

    async def test_forgot_password_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/auth/forgot-password",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422


class TestAuthValidateToken:
    async def test_validate_token(self, client: AsyncClient, admin_user, admin_headers):
        response = await client.get("/auth/validate-token", headers=admin_headers)
        assert_ok(response)
        data = response.json()
        assert data["valid"] is True
        assert data["role"] == "admin"

    async def test_validate_token_no_auth(self, client: AsyncClient):
        response = await client.get("/auth/validate-token")
        assert_unauthorized(response)
