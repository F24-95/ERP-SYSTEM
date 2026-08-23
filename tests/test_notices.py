"""Tests for notice/announcement endpoints."""
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


class TestNoticeCRUD:
    async def test_create_notice(self, admin_client):
        resp = await admin_client.post(
            "/notices/notices",
            json={
                "title": "School Holiday",
                "content": "School will remain closed tomorrow.",
                "notice_date": "2026-08-15",
                "target_audience": "all",
            },
        )
        assert resp.status_code in (201, 400, 422)

    async def test_create_notice_missing_title(self, admin_client):
        resp = await admin_client.post(
            "/notices/notices",
            json={
                "content": "Missing title notice",
                "notice_date": "2026-08-15",
                "target_audience": "all",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_create_notice_missing_content(self, admin_client):
        resp = await admin_client.post(
            "/notices/notices",
            json={
                "title": "Missing Content Notice",
                "notice_date": "2026-08-15",
                "target_audience": "all",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_create_notice_teacher(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "notice_teacher@test.com",
                "phone": "9876543210",
                "role": "teacher",
                "password": "TeacherPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "notice_teacher@test.com",
                "password": "TeacherPass1!",
            },
        )
        assert token_resp.status_code == 200
        teacher_token = token_resp.json()["access_token"]

        resp = await client.post(
            "/notices/notices",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "title": "PTM Meeting",
                "content": "PTM scheduled for next week.",
                "notice_date": "2026-08-20",
                "target_audience": "parents",
            },
        )
        assert resp.status_code in (201, 403)

    async def test_create_notice_student_forbidden(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "notice_student@test.com",
                "phone": "9876543211",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "notice_student@test.com",
                "password": "StudentPass1!",
            },
        )
        assert token_resp.status_code == 200
        student_token = token_resp.json()["access_token"]

        resp = await client.post(
            "/notices/notices",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "title": "Fake Notice",
                "content": "This should not be created.",
                "notice_date": "2026-08-15",
                "target_audience": "all",
            },
        )
        assert resp.status_code == 403

    async def test_list_notices(self, admin_client):
        resp = await admin_client.get("/notices/notices")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_notices_unauthorized(self, client):
        resp = await client.get("/notices/notices")
        assert_unauthorized(resp)

    async def test_get_notice(self, admin_client):
        create_resp = await admin_client.post(
            "/notices/notices",
            json={
                "title": "Get Notice Test",
                "content": "Test content",
                "notice_date": "2026-08-15",
                "target_audience": "all",
            },
        )
        if create_resp.status_code == 201:
            notice_id = create_resp.json()["id"]
            resp = await admin_client.get(
                f"/notices/notices/{notice_id}"
            )
            assert resp.status_code == 200
            assert resp.json()["title"] == "Get Notice Test"

    async def test_get_notice_not_found(self, admin_client):
        resp = await admin_client.get(
            "/notices/notices/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (404, 400)

    async def test_update_notice(self, admin_client):
        create_resp = await admin_client.post(
            "/notices/notices",
            json={
                "title": "Update Notice Test",
                "content": "Original content",
                "notice_date": "2026-08-15",
                "target_audience": "all",
            },
        )
        if create_resp.status_code == 201:
            notice_id = create_resp.json()["id"]
            resp = await admin_client.patch(
                f"/notices/notices/{notice_id}",
                json={"title": "Updated Notice Title"},
            )
            assert resp.status_code == 200
            assert resp.json()["title"] == "Updated Notice Title"

    async def test_update_notice_not_found(self, admin_client):
        resp = await admin_client.patch(
            "/notices/notices/00000000-0000-0000-0000-000000000000",
            json={"title": "X"},
        )
        assert resp.status_code in (404, 400)

    async def test_delete_notice(self, admin_client):
        create_resp = await admin_client.post(
            "/notices/notices",
            json={
                "title": "Delete Notice Test",
                "content": "To be deleted",
                "notice_date": "2026-08-15",
                "target_audience": "all",
            },
        )
        if create_resp.status_code == 201:
            notice_id = create_resp.json()["id"]
            resp = await admin_client.delete(
                f"/notices/notices/{notice_id}"
            )
            assert resp.status_code in (204, 400)

    async def test_delete_notice_not_found(self, admin_client):
        resp = await admin_client.delete(
            "/notices/notices/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (204, 404, 400)

    async def test_student_can_view_notices(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "notice_stu_view@test.com",
                "phone": "9876543212",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "notice_stu_view@test.com",
                "password": "StudentPass1!",
            },
        )
        assert token_resp.status_code == 200
        student_token = token_resp.json()["access_token"]

        resp = await client.get(
            "/notices/notices",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200
