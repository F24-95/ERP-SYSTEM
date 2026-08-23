"""Edge-case tests: missing IDs, empty strings, invalid tokens, etc."""
import pytest
from httpx import AsyncClient

from tests.helpers import (
    assert_bad_request,
    assert_created,
    assert_forbidden,
    assert_not_found,
    assert_ok,
    assert_unauthorized,
)

pytestmark = pytest.mark.asyncio


class TestMissingFields:
    async def test_create_user_missing_email(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "phone": "9998887776",
                "role": "student",
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_create_user_missing_phone(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "nophone@test.com",
                "role": "student",
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_create_user_missing_role(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "norole@test.com",
                "phone": "9998887776",
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_create_user_missing_password(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "nopass@test.com",
                "phone": "9998887776",
                "role": "student",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_create_user_empty_email(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "",
                "phone": "9998887776",
                "role": "student",
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_create_user_empty_phone(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "emptyphone@test.com",
                "phone": "",
                "role": "student",
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_create_user_empty_password(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "emptypass@test.com",
                "phone": "9998887776",
                "role": "student",
                "password": "",
            },
        )
        assert resp.status_code in (400, 422)


class TestInvalidIDs:
    async def test_get_user_invalid_id(self, admin_client):
        resp = await admin_client.get("/admin/users/not-a-uuid")
        assert resp.status_code in (404, 400, 422)

    async def test_get_user_random_uuid(self, admin_client):
        resp = await admin_client.get(
            "/admin/users/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (404, 400)

    async def test_update_user_invalid_id(self, admin_client):
        resp = await admin_client.patch(
            "/admin/users/not-a-uuid", json={"phone": "1111111111"}
        )
        assert resp.status_code in (404, 400, 422)

    async def test_delete_user_invalid_id(self, admin_client):
        resp = await admin_client.delete("/admin/users/not-a-uuid")
        assert resp.status_code in (404, 400, 422)

    async def test_get_student_profile_invalid_id(self, admin_client):
        resp = await admin_client.get("/admin/students/not-a-uuid")
        assert resp.status_code in (404, 400, 422)

    async def test_get_teacher_profile_invalid_id(self, admin_client):
        resp = await admin_client.get("/admin/teachers/not-a-uuid")
        assert resp.status_code in (404, 400, 422)


class TestWeakPasswords:
    async def test_weak_password_too_short(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "weak@test.com",
                "phone": "9998887776",
                "role": "student",
                "password": "123",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_weak_password_no_uppercase(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "noupper@test.com",
                "phone": "9998887776",
                "role": "student",
                "password": "weakpassword1!",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_weak_password_no_number(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "nonum@test.com",
                "phone": "9998887776",
                "role": "student",
                "password": "WeakPassword!",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_weak_password_no_special_char(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "nospecial@test.com",
                "phone": "9998887776",
                "role": "student",
                "password": "WeakPassword1",
            },
        )
        assert resp.status_code in (400, 422)


class TestDuplicateEmails:
    async def test_duplicate_email_rejected(
        self, admin_client, admin_user
    ):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "admin@test.com",
                "phone": "9998887776",
                "role": "student",
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code in (400, 409)


class TestInvalidRoles:
    async def test_invalid_role_string(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "invalidrole@test.com",
                "phone": "9998887776",
                "role": "superadmin",
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_empty_role(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "emptyrole@test.com",
                "phone": "9998887776",
                "role": "",
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_numeric_role(self, admin_client):
        resp = await admin_client.post(
            "/admin/user",
            json={
                "email": "numrole@test.com",
                "phone": "9998887776",
                "role": 123,
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code in (400, 422)


class TestEdgeCasesUserUpdate:
    async def test_update_user_empty_body(
        self, admin_client, student_user
    ):
        resp = await admin_client.patch(
            f"/admin/users/{student_user.public_id}", json={}
        )
        assert resp.status_code in (200, 400)

    async def test_update_user_invalid_field(
        self, admin_client, student_user
    ):
        resp = await admin_client.patch(
            f"/admin/users/{student_user.public_id}",
            json={"nonexistent_field": "value"},
        )
        assert resp.status_code in (200, 400, 422)

    async def test_update_user_huge_string(
        self, admin_client, student_user
    ):
        resp = await admin_client.patch(
            f"/admin/users/{student_user.public_id}",
            json={"phone": "x" * 10000},
        )
        assert resp.status_code in (400, 422)


class TestEmptyHeaders:
    async def test_empty_auth_header(self, client):
        resp = await client.get(
            "/users/me", headers={"Authorization": ""}
        )
        assert_unauthorized(resp)

    async def test_malformed_auth_header(self, client):
        resp = await client.get(
            "/users/me", headers={"Authorization": "Bearer"}
        )
        assert_unauthorized(resp)

    async def test_bearer_with_no_token(self, client):
        resp = await client.get(
            "/users/me", headers={"Authorization": "Bearer "}
        )
        assert_unauthorized(resp)


class TestHTTPMethods:
    async def test_login_with_get(self, client):
        resp = await client.get("/auth/login")
        assert resp.status_code in (405, 404)

    async def test_refresh_with_get(self, client):
        resp = await client.get("/auth/refresh")
        assert resp.status_code in (405, 404)

    async def test_logout_with_get(self, client):
        resp = await client.get("/auth/logout")
        assert resp.status_code in (405, 404)

    async def test_users_me_with_post(self, client):
        resp = await client.post("/users/me", json={})
        assert resp.status_code in (405, 401, 422)


class TestAssignmentEdgeCases:
    async def test_create_assignment_missing_fields(self, admin_client):
        resp = await admin_client.post("/assignments/", json={})
        assert resp.status_code in (400, 422)

    async def test_create_assignment_invalid_date_format(self, admin_client):
        resp = await admin_client.post(
            "/assignments/",
            json={
                "title": "Test",
                "subject_id": "invalid",
                "classroom_id": "invalid",
                "assigned_by": "invalid",
                "assigned_date": "not-a-date",
                "due_date": "not-a-date",
                "max_marks": "not-a-number",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_get_assignment_invalid_id(self, admin_client):
        resp = await admin_client.get("/assignments/not-a-uuid")
        assert resp.status_code in (404, 400, 422)

    async def test_list_assignments_unauthorized(self, client):
        resp = await client.get("/assignments/")
        assert_unauthorized(resp)
