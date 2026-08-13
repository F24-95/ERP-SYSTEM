import pytest
from httpx import AsyncClient

from tests.helpers import assert_forbidden, assert_ok

pytestmark = pytest.mark.asyncio


class TestStudentUsersMe:
    async def test_get_me(self, student_client: AsyncClient, student_user):
        response = await student_client.get("/users/me")
        assert_ok(response)
        assert response.json()["email"] == student_user.email

    async def test_update_me(self, student_client: AsyncClient, student_user):
        response = await student_client.patch("/users/me", json={"phone": "7778889990"})
        assert_ok(response)
        assert response.json()["phone"] == "7778889990"


class TestStudentAuthValidate:
    async def test_validate_token(self, student_client: AsyncClient, student_user):
        response = await student_client.get("/auth/validate-token")
        assert_ok(response)
        data = response.json()
        assert data["valid"] is True
        assert data["role"] == "student"


class TestStudentProfileList:
    async def test_list_student_profiles(
        self, student_client: AsyncClient, student_user
    ):
        response = await student_client.get("/admin/students")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1

    async def test_list_teacher_profiles(
        self, student_client: AsyncClient, teacher_user
    ):
        response = await student_client.get("/admin/teachers")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1

    async def test_list_admin_profiles(self, student_client: AsyncClient, admin_user):
        response = await student_client.get("/admin/admins")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1


class TestStudentForbidden:
    async def test_cannot_create_user(self, student_client: AsyncClient):
        response = await student_client.post(
            "/admin/user",
            json={
                "email": "x@x.com",
                "phone": "1111111111",
                "role": "student",
                "password": "Pass1234!",
            },
        )
        assert_forbidden(response)

    async def test_cannot_list_users(self, student_client: AsyncClient):
        response = await student_client.get("/admin/users")
        assert_forbidden(response)

    async def test_cannot_deactivate_user(
        self, student_client: AsyncClient, student_user
    ):
        response = await student_client.delete(f"/admin/users/{student_user.public_id}")
        assert_forbidden(response)

    async def test_cannot_update_teacher_profile(
        self, student_client: AsyncClient, teacher_user, db_session
    ):
        from sqlalchemy import select
        from src.domain.users.models import TeacherProfile

        result = await db_session.execute(
            select(TeacherProfile).filter_by(user_id=teacher_user.id)
        )
        profile = result.scalars().first()
        response = await student_client.patch(
            f"/admin/teachers/{profile.id}",
            json={"teacher_name": "Hacked"},
        )
        assert_forbidden(response)

    async def test_cannot_access_teacher_endpoints(self, student_client: AsyncClient):
        response = await student_client.get("/teacher/profile")
        assert_forbidden(response)

    async def test_cannot_deactivate_session(
        self, student_client: AsyncClient, academic_session
    ):
        response = await student_client.delete(
            f"/academics/sessions/{academic_session.id}"
        )
        assert_forbidden(response)

    async def test_cannot_delete_classroom(
        self, student_client: AsyncClient, classroom
    ):
        response = await student_client.delete(f"/academics/classrooms/{classroom.id}")
        assert_forbidden(response)

    async def test_cannot_delete_subject(self, student_client: AsyncClient, subject):
        response = await student_client.delete(f"/academics/subjects/{subject.id}")
        assert_forbidden(response)


class TestStudentParentRole:
    async def test_parent_get_me(self, client: AsyncClient, parent_user):
        from tests.conftest import DEFAULT_PASSWORD
        from tests.helpers import get_auth_headers

        headers = await get_auth_headers(client, "parent@test.com", DEFAULT_PASSWORD)
        response = await client.get("/users/me", headers=headers)
        assert_ok(response)
        assert response.json()["email"] == "parent@test.com"

    async def test_parent_cannot_access_admin(self, client: AsyncClient, parent_user):
        from tests.conftest import DEFAULT_PASSWORD
        from tests.helpers import get_auth_headers

        headers = await get_auth_headers(client, "parent@test.com", DEFAULT_PASSWORD)
        response = await client.get("/admin/users", headers=headers)
        assert_forbidden(response)
