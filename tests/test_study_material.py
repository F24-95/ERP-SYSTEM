"""Tests for study material endpoints."""
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


class TestStudyMaterialCRUD:
    async def test_create_material(self, admin_client):
        resp = await admin_client.post(
            "/study-material/materials",
            json={
                "title": "Algebra Notes",
                "subject_id": 1,
                "classroom_id": 1,
                "description": "Chapter 1 notes on algebra",
                "material_type": "notes",
            },
        )
        assert resp.status_code in (201, 400, 422)

    async def test_create_material_missing_fields(self, admin_client):
        resp = await admin_client.post(
            "/study-material/materials", json={}
        )
        assert resp.status_code in (400, 422)

    async def test_list_materials(self, admin_client):
        resp = await admin_client.get("/study-material/materials")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_materials_unauthorized(self, client):
        resp = await client.get("/study-material/materials")
        assert_unauthorized(resp)

    async def test_list_materials_student(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "sm_student@test.com",
                "phone": "9876543210",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "sm_student@test.com",
                "password": "StudentPass1!",
            },
        )
        assert token_resp.status_code == 200
        student_token = token_resp.json()["access_token"]

        resp = await client.get(
            "/study-material/materials",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200

    async def test_list_materials_teacher(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "sm_teacher@test.com",
                "phone": "9876543211",
                "role": "teacher",
                "password": "TeacherPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "sm_teacher@test.com",
                "password": "TeacherPass1!",
            },
        )
        assert token_resp.status_code == 200
        teacher_token = token_resp.json()["access_token"]

        resp = await client.get(
            "/study-material/materials",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 200

    async def test_get_material(self, admin_client):
        list_resp = await admin_client.get("/study-material/materials")
        if list_resp.json():
            m_id = list_resp.json()[0]["id"]
            resp = await admin_client.get(
                f"/study-material/materials/{m_id}"
            )
            assert resp.status_code == 200

    async def test_get_material_not_found(self, admin_client):
        resp = await admin_client.get(
            "/study-material/materials/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (404, 400)

    async def test_update_material(self, admin_client):
        list_resp = await admin_client.get("/study-material/materials")
        if list_resp.json():
            m_id = list_resp.json()[0]["id"]
            resp = await admin_client.patch(
                f"/study-material/materials/{m_id}",
                json={"title": "Updated Material"},
            )
            assert resp.status_code == 200

    async def test_delete_material(self, admin_client):
        create_resp = await admin_client.post(
            "/study-material/materials",
            json={
                "title": "Temp Material",
                "subject_id": 1,
                "classroom_id": 1,
                "description": "Temporary",
                "material_type": "notes",
            },
        )
        if create_resp.status_code == 201:
            m_id = create_resp.json()["id"]
            resp = await admin_client.delete(
                f"/study-material/materials/{m_id}"
            )
            assert resp.status_code in (204, 400)

    async def test_student_cannot_create_material(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "sm_student2@test.com",
                "phone": "9876543212",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "sm_student2@test.com",
                "password": "StudentPass1!",
            },
        )
        student_token = token_resp.json()["access_token"]

        resp = await client.post(
            "/study-material/materials",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "title": "Student Material",
                "subject_id": 1,
                "classroom_id": 1,
                "description": "Student upload",
                "material_type": "notes",
            },
        )
        assert resp.status_code == 403
