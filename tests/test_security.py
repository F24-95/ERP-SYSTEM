"""Security tests: RBAC enforcement, boundary conditions."""
import pytest
from httpx import AsyncClient

from src.core.security import create_access_token
from tests.helpers import (
    assert_created,
    assert_forbidden,
    assert_ok,
    assert_unauthorized,
)

pytestmark = pytest.mark.asyncio


class TestRBACStudentCannotAccessAdmin:
    async def test_student_cannot_create_user(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "rbac_student@test.com",
                "phone": "9876543210",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "rbac_student@test.com",
                "password": "StudentPass1!",
            },
        )
        assert token_resp.status_code == 200
        student_token = token_resp.json()["access_token"]
        student_headers = {
            "Authorization": f"Bearer {student_token}"
        }

        resp = await client.post(
            "/admin/user",
            headers=student_headers,
            json={
                "email": "new@test.com",
                "phone": "1111111111",
                "role": "student",
                "password": "Pass1234!",
            },
        )
        assert resp.status_code == 403

    async def test_student_cannot_list_users(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "rbac_student2@test.com",
                "phone": "9876543211",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "rbac_student2@test.com",
                "password": "StudentPass1!",
            },
        )
        student_token = token_resp.json()["access_token"]

        resp = await client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 403

    async def test_student_cannot_update_user(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "rbac_student3@test.com",
                "phone": "9876543212",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "rbac_student3@test.com",
                "password": "StudentPass1!",
            },
        )
        student_token = token_resp.json()["access_token"]

        resp = await client.patch(
            "/admin/users/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"phone": "9999999999"},
        )
        assert resp.status_code == 403

    async def test_student_cannot_delete_user(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "rbac_student4@test.com",
                "phone": "9876543213",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "rbac_student4@test.com",
                "password": "StudentPass1!",
            },
        )
        student_token = token_resp.json()["access_token"]

        resp = await client.delete(
            "/admin/users/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 403

    async def test_student_cannot_manage_academics(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "rbac_student5@test.com",
                "phone": "9876543214",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "rbac_student5@test.com",
                "password": "StudentPass1!",
            },
        )
        student_token = token_resp.json()["access_token"]
        student_headers = {
            "Authorization": f"Bearer {student_token}"
        }

        resp = await client.post(
            "/academics/sessions",
            headers=student_headers,
            json={
                "session_code": "SES-RBAC",
                "session_name": "2025-2026",
                "start_year": 2025,
                "end_year": 2026,
            },
        )
        assert resp.status_code == 403

        resp = await client.post(
            "/academics/classrooms",
            headers=student_headers,
            json={
                "class_code": "CLS-RBAC",
                "class_name": "10",
                "section": "A",
                "display_name": "10-A",
            },
        )
        assert resp.status_code == 403

    async def test_student_can_access_profile(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "rbac_student6@test.com",
                "phone": "9876543215",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "rbac_student6@test.com",
                "password": "StudentPass1!",
            },
        )
        student_token = token_resp.json()["access_token"]

        resp = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200

    async def test_student_can_view_fee_structure(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "rbac_student7@test.com",
                "phone": "9876543216",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "rbac_student7@test.com",
                "password": "StudentPass1!",
            },
        )
        student_token = token_resp.json()["access_token"]

        resp = await client.get(
            "/fees/structures",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200


class TestRBACTeacherCannotAccessAdmin:
    async def test_teacher_cannot_manage_users(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "rbac_teacher@test.com",
                "phone": "9876543220",
                "role": "teacher",
                "password": "TeacherPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "rbac_teacher@test.com",
                "password": "TeacherPass1!",
            },
        )
        teacher_token = token_resp.json()["access_token"]
        teacher_headers = {
            "Authorization": f"Bearer {teacher_token}"
        }

        resp = await client.post(
            "/admin/user",
            headers=teacher_headers,
            json={
                "email": "new@test.com",
                "phone": "1111111111",
                "role": "student",
                "password": "Pass1234!",
            },
        )
        assert resp.status_code == 403

        resp = await client.get(
            "/admin/users",
            headers=teacher_headers,
        )
        assert resp.status_code == 403

    async def test_teacher_cannot_manage_academics(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "rbac_teacher2@test.com",
                "phone": "9876543221",
                "role": "teacher",
                "password": "TeacherPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "rbac_teacher2@test.com",
                "password": "TeacherPass1!",
            },
        )
        teacher_token = token_resp.json()["access_token"]
        teacher_headers = {
            "Authorization": f"Bearer {teacher_token}"
        }

        resp = await client.post(
            "/academics/sessions",
            headers=teacher_headers,
            json={
                "session_code": "SES-TCH",
                "session_name": "2025-2026",
                "start_year": 2025,
                "end_year": 2026,
            },
        )
        assert resp.status_code == 403

    async def test_teacher_can_list_subjects(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "rbac_teacher3@test.com",
                "phone": "9876543222",
                "role": "teacher",
                "password": "TeacherPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "rbac_teacher3@test.com",
                "password": "TeacherPass1!",
            },
        )
        teacher_token = token_resp.json()["access_token"]

        resp = await client.get(
            "/academics/subjects",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 200


class TestTokenSecurity:
    async def test_access_token_only_requires_auth(
        self,
        client: AsyncClient,
        admin_user,
    ):
        token = create_access_token(
            {"sub": str(admin_user.id), "role": admin_user.role.value}
        )
        resp = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_refresh_token_cannot_access_api(
        self,
        client: AsyncClient,
        admin_user,
    ):
        from src.core.security import create_refresh_token

        token = create_refresh_token(
            {"sub": str(admin_user.id), "role": admin_user.role.value}
        )
        resp = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (401, 403)


class TestBoundaryPermissions:
    async def test_admin_has_full_access(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        resp = await client.get(
            "/admin/users",
            headers=admin_headers,
        )
        assert resp.status_code == 200

        resp = await client.post(
            "/academics/sessions",
            headers=admin_headers,
            json={
                "session_code": "SES-BND",
                "session_name": "2025-2026",
                "start_year": 2025,
                "end_year": 2026,
            },
        )
        assert resp.status_code in (201, 400, 409)

        resp = await client.post(
            "/academics/subjects",
            headers=admin_headers,
            json={
                "subject_code": "BND",
                "subject_name": "Boundary Test",
            },
        )
        assert resp.status_code in (201, 400, 409)

    async def test_unauthenticated_cannot_access_protected(
        self,
        client: AsyncClient,
    ):
        resp = await client.get("/admin/users")
        assert resp.status_code == 401

        resp = await client.get("/academics/sessions")
        assert resp.status_code == 401

        resp = await client.get("/users/me")
        assert resp.status_code == 401

        resp = await client.post(
            "/auth/logout",
            json={"refresh_token": "dummy"},
        )
        assert resp.status_code == 401

        resp = await client.post(
            "/auth/change-password",
            json={
                "old_password": "old",
                "new_password": "new",
            },
        )
        assert resp.status_code == 401
