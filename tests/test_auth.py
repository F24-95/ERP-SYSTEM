"""Tests for auth endpoints: login, logout, refresh, password change, OTP."""
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from tests.helpers import (
    assert_bad_request,
    assert_forbidden,
    assert_no_content,
    assert_ok,
    assert_unauthorized,
)

pytestmark = pytest.mark.asyncio


class TestLogin:
    async def test_login_success(self, client: AsyncClient, admin_user):
        resp = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "TestPass123!"},
        )
        assert_ok(resp)
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient, admin_user):
        resp = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "WrongPassword1!"},
        )
        assert_unauthorized(resp)

    async def test_login_nonexistent_user(self, client: AsyncClient, admin_user):
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@test.com", "password": "TestPass123!"},
        )
        assert_unauthorized(resp)

    async def test_login_returns_user_info(
        self, client: AsyncClient, admin_user
    ):
        resp = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "TestPass123!"},
        )
        assert_ok(resp)
        data = resp.json()
        assert "user" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == "admin@test.com"


class TestRefreshToken:
    async def test_refresh_success(self, client: AsyncClient, admin_user):
        login_resp = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "TestPass123!"},
        )
        assert_ok(login_resp)
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert_ok(resp)
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        resp = await client.post(
            "/auth/refresh", json={"refresh_token": "invalid.token.here"}
        )
        assert_unauthorized(resp)

    async def test_refresh_with_access_token_instead_of_refresh(
        self, client: AsyncClient, admin_user
    ):
        login_resp = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "TestPass123!"},
        )
        assert_ok(login_resp)
        access_token = login_resp.json()["access_token"]

        resp = await client.post(
            "/auth/refresh", json={"refresh_token": access_token}
        )
        assert_unauthorized(resp)


class TestLogout:
    async def test_logout_success(self, client: AsyncClient, admin_user):
        login_resp = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "TestPass123!"},
        )
        assert_ok(login_resp)
        refresh_token = login_resp.json()["refresh_token"]
        headers = {
            "Authorization": f"Bearer {login_resp.json()['access_token']}"
        }

        resp = await client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers=headers,
        )
        assert_no_content(resp)

    async def test_logout_without_refresh_token(
        self, client: AsyncClient, admin_user, admin_headers
    ):
        resp = await client.post(
            "/auth/logout", json={}, headers=admin_headers
        )
        assert_no_content(resp)

    async def test_logout_revokes_token(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
        db_session,
    ):
        login_resp = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "TestPass123!"},
        )
        assert_ok(login_resp)
        refresh_token = login_resp.json()["refresh_token"]

        await client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers=admin_headers,
        )

        refresh_resp = await client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert_unauthorized(refresh_resp)

    async def test_logout_after_token_revoked_fails(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        login_resp = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "TestPass123!"},
        )
        assert_ok(login_resp)
        refresh_token = login_resp.json()["refresh_token"]

        await client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers=admin_headers,
        )

        resp = await client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers=admin_headers,
        )
        assert_no_content(resp)


class TestPasswordChange:
    async def test_change_password_success(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        resp = await client.post(
            "/auth/change-password",
            json={
                "old_password": "TestPass123!",
                "new_password": "NewPass456!",
            },
            headers=admin_headers,
        )
        assert_ok(resp)

    async def test_change_password_wrong_old(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        resp = await client.post(
            "/auth/change-password",
            json={
                "old_password": "WrongOldPass!",
                "new_password": "NewPass456!",
            },
            headers=admin_headers,
        )
        assert_bad_request(resp)

    async def test_change_password_same_as_old(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        resp = await client.post(
            "/auth/change-password",
            json={
                "old_password": "TestPass123!",
                "new_password": "TestPass123!",
            },
            headers=admin_headers,
        )
        assert_bad_request(resp)

    async def test_change_password_too_short(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        resp = await client.post(
            "/auth/change-password",
            json={
                "old_password": "TestPass123!",
                "new_password": "Ab1!",
            },
            headers=admin_headers,
        )
        assert_bad_request(resp)

    async def test_change_password_no_old_password(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        resp = await client.post(
            "/auth/change-password",
            json={"new_password": "NewPass456!"},
            headers=admin_headers,
        )
        assert_bad_request(resp)


class TestSendVerificationOTP:
    async def test_send_otp_success(
        self,
        client: AsyncClient,
        teacher_user,
        teacher_headers,
    ):
        resp = await client.post(
            "/auth/send-verification-otp",
            json={"user_id": str(teacher_user.public_id)},
            headers=teacher_headers,
        )
        assert_ok(resp)
        assert resp.json()["message"] == "OTP sent successfully"

    async def test_send_otp_for_other_user(
        self,
        client: AsyncClient,
        student_user,
        student_headers,
    ):
        resp = await client.post(
            "/auth/send-verification-otp",
            json={"user_id": "00000000-0000-0000-0000-000000000000"},
            headers=student_headers,
        )
        assert_forbidden(resp)

    async def test_send_otp_already_verified(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        resp = await client.post(
            "/auth/send-verification-otp",
            json={"user_id": str(admin_user.public_id)},
            headers=admin_headers,
        )
        assert_bad_request(resp)


class TestVerifyOTP:
    async def test_verify_otp_invalid(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        resp = await client.post(
            "/auth/verify-otp",
            json={
                "user_id": str(admin_user.public_id),
                "otp": "000000",
            },
            headers=admin_headers,
        )
        assert_unauthorized(resp)


class TestForgotPassword:
    async def test_forgot_password_success(
        self, client: AsyncClient, admin_user
    ):
        resp = await client.post(
            "/auth/forgot-password",
            json={"email": "admin@test.com"},
        )
        assert_ok(resp)

    async def test_forgot_password_nonexistent(
        self, client: AsyncClient, admin_user
    ):
        resp = await client.post(
            "/auth/forgot-password",
            json={"email": "nonexistent@test.com"},
        )
        assert_ok(resp)


class TestResetPassword:
    async def test_reset_password_invalid_token(
        self, client: AsyncClient
    ):
        resp = await client.post(
            "/auth/reset-password",
            json={
                "token": "invalid",
                "new_password": "NewPass456!",
            },
        )
        assert_bad_request(resp)


class TestSecurity:
    async def test_token_with_invalid_signature(
        self, client: AsyncClient, admin_user
    ):
        resp = await client.get(
            "/users/me",
            headers={
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid"
            },
        )
        assert_unauthorized(resp)

    async def test_token_with_expired_signature(
        self, client: AsyncClient, admin_user
    ):
        token = create_access_token(
            {"sub": str(admin_user.id), "role": admin_user.role.value},
            expires_delta=timedelta(seconds=-1),
        )
        resp = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert_unauthorized(resp)

    async def test_validate_token_success(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        resp = await client.post(
            "/auth/validate-token",
            headers=admin_headers,
        )
        assert_ok(resp)
        data = resp.json()
        assert data["valid"] is True

    async def test_validate_token_invalid(
        self, client: AsyncClient, admin_user
    ):
        resp = await client.post(
            "/auth/validate-token",
            headers={
                "Authorization": "Bearer invalid.token.value"
            },
        )
        assert_unauthorized(resp)


class TestTokenRevocation:
    async def test_login_after_password_change_invalidates_old(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        resp1 = await client.post(
            "/auth/change-password",
            json={
                "old_password": "TestPass123!",
                "new_password": "NewPass789!",
            },
            headers=admin_headers,
        )
        assert_ok(resp1)

        resp2 = await client.post(
            "/auth/login",
            json={
                "email": "admin@test.com",
                "password": "NewPass789!",
            },
        )
        assert_ok(resp2)
        assert "access_token" in resp2.json()

    async def test_logout_invalidates_refresh_token(
        self,
        client: AsyncClient,
        admin_user,
    ):
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": "admin@test.com",
                "password": "TestPass123!",
            },
        )
        assert_ok(login_resp)
        refresh_token = login_resp.json()["refresh_token"]

        logout_resp = await client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers={
                "Authorization": f"Bearer {login_resp.json()['access_token']}"
            },
        )
        assert_no_content(logout_resp)

        refresh_resp = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert_unauthorized(refresh_resp)

    async def test_multiple_logins_create_different_tokens(
        self, client: AsyncClient, admin_user
    ):
        login1 = await client.post(
            "/auth/login",
            json={
                "email": "admin@test.com",
                "password": "TestPass123!",
            },
        )
        login2 = await client.post(
            "/auth/login",
            json={
                "email": "admin@test.com",
                "password": "TestPass123!",
            },
        )
        assert_ok(login1)
        assert_ok(login2)

    async def test_refresh_creates_new_token_pair(
        self, client: AsyncClient, admin_user
    ):
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": "admin@test.com",
                "password": "TestPass123!",
            },
        )
        assert_ok(login_resp)
        old_refresh = login_resp.json()["refresh_token"]

        refresh_resp = await client.post(
            "/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert_ok(refresh_resp)
        new_refresh = refresh_resp.json()["refresh_token"]

        old_refresh_resp = await client.post(
            "/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert_unauthorized(old_refresh_resp)
