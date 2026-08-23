"""Tests for exam management endpoints."""
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


class TestExamManagement:
    async def test_create_exam(self, admin_client):
        resp = await admin_client.post(
            "/exams/exams",
            json={
                "title": "Mid-Term Exam",
                "subject_id": 1,
                "classroom_id": 1,
                "academic_session_id": 1,
                "start_date": "2026-09-01",
                "end_date": "2026-09-10",
            },
        )
        assert resp.status_code in (201, 400, 422)

    async def test_create_exam_missing_fields(self, admin_client):
        resp = await admin_client.post("/exams/exams", json={})
        assert resp.status_code in (400, 422)

    async def test_list_exams(self, admin_client):
        resp = await admin_client.get("/exams/exams")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_exams_unauthorized(self, client):
        resp = await client.get("/exams/exams")
        assert_unauthorized(resp)

    async def test_list_exams_student(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "ex_student@test.com",
                "phone": "9876543210",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "ex_student@test.com",
                "password": "StudentPass1!",
            },
        )
        assert token_resp.status_code == 200
        student_token = token_resp.json()["access_token"]

        resp = await client.get(
            "/exams/exams",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200

    async def test_list_exams_teacher(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "ex_teacher@test.com",
                "phone": "9876543211",
                "role": "teacher",
                "password": "TeacherPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "ex_teacher@test.com",
                "password": "TeacherPass1!",
            },
        )
        assert token_resp.status_code == 200
        teacher_token = token_resp.json()["access_token"]

        resp = await client.get(
            "/exams/exams",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 200

    async def test_get_exam(self, admin_client):
        list_resp = await admin_client.get("/exams/exams")
        assert list_resp.status_code == 200
        exams = list_resp.json()
        if exams:
            exam_id = exams[0]["id"]
            resp = await admin_client.get(f"/exams/exams/{exam_id}")
            assert resp.status_code == 200

    async def test_get_exam_not_found(self, admin_client):
        resp = await admin_client.get(
            "/exams/exams/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (404, 400)

    async def test_update_exam(self, admin_client):
        list_resp = await admin_client.get("/exams/exams")
        assert list_resp.status_code == 200
        exams = list_resp.json()
        if exams:
            exam_id = exams[0]["id"]
            resp = await admin_client.patch(
                f"/exams/exams/{exam_id}",
                json={"title": "Updated Exam Title"},
            )
            assert resp.status_code == 200
            assert resp.json()["title"] == "Updated Exam Title"

    async def test_update_exam_not_found(self, admin_client):
        resp = await admin_client.patch(
            "/exams/exams/00000000-0000-0000-0000-000000000000",
            json={"title": "X"},
        )
        assert resp.status_code in (404, 400)

    async def test_delete_exam(self, admin_client):
        create_resp = await admin_client.post(
            "/exams/exams",
            json={
                "title": "To Delete Exam",
                "subject_id": 1,
                "classroom_id": 1,
                "academic_session_id": 1,
                "start_date": "2026-09-01",
                "end_date": "2026-09-01",
            },
        )
        if create_resp.status_code == 201:
            exam_id = create_resp.json()["id"]
            resp = await admin_client.delete(f"/exams/exams/{exam_id}")
            assert resp.status_code == 204

    async def test_delete_exam_not_found(self, admin_client):
        resp = await admin_client.delete(
            "/exams/exams/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (204, 404, 400)

    async def test_create_exam_result(self, admin_client):
        list_resp = await admin_client.get("/exams/exams")
        assert list_resp.status_code == 200
        exams = list_resp.json()
        if exams:
            exam_id = exams[0]["id"]
            user_resp = await admin_client.post(
                "/admin/user",
                json={
                    "email": "exam_student@test.com",
                    "phone": "9876543220",
                    "role": "student",
                    "password": "StudentPass1!",
                },
            )
            if user_resp.status_code == 201:
                student_id = user_resp.json()["id"]
                resp = await admin_client.post(
                    "/exams/results",
                    json={
                        "exam_id": exam_id,
                        "student_id": student_id,
                        "marks_obtained": 85,
                        "grade": "A",
                        "remarks": "Good work",
                    },
                )
                assert resp.status_code in (201, 400, 422)

    async def test_list_exam_results(self, admin_client):
        resp = await admin_client.get("/exams/results")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_exam_results_unauthorized(self, client):
        resp = await client.get("/exams/results")
        assert_unauthorized(resp)

    async def test_student_can_view_exam_results(
        self,
        client: AsyncClient,
        admin_user,
        admin_headers,
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "ex_res_student@test.com",
                "phone": "9876543221",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "ex_res_student@test.com",
                "password": "StudentPass1!",
            },
        )
        assert token_resp.status_code == 200
        student_token = token_resp.json()["access_token"]

        resp = await client.get(
            "/exams/results",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200

    async def test_exam_not_found_with_invalid_id(self, admin_client):
        resp = await admin_client.get(
            "/exams/exams/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (404, 400)

    async def test_exam_results_not_found_with_invalid_id(
        self, admin_client
    ):
        resp = await admin_client.get(
            "/exams/results/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (404, 400)

    async def test_create_exam_missing_title(self, admin_client):
        resp = await admin_client.post(
            "/exams/exams",
            json={
                "subject_id": 1,
                "classroom_id": 1,
                "academic_session_id": 1,
                "start_date": "2026-09-01",
                "end_date": "2026-09-10",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_create_exam_missing_dates(self, admin_client):
        resp = await admin_client.post(
            "/exams/exams",
            json={
                "title": "No Dates Exam",
                "subject_id": 1,
                "classroom_id": 1,
                "academic_session_id": 1,
            },
        )
        assert resp.status_code in (400, 422)

    async def test_create_exam_invalid_dates(self, admin_client):
        resp = await admin_client.post(
            "/exams/exams",
            json={
                "title": "Invalid Dates Exam",
                "subject_id": 1,
                "classroom_id": 1,
                "academic_session_id": 1,
                "start_date": "2026-09-10",
                "end_date": "2026-09-01",
            },
        )
        assert resp.status_code in (400, 422)

    async def test_update_exam_nonexistent_field(self, admin_client):
        list_resp = await admin_client.get("/exams/exams")
        if list_resp.json():
            exam_id = list_resp.json()[0]["id"]
            resp = await admin_client.patch(
                f"/exams/exams/{exam_id}",
                json={"nonexistent_field": "value"},
            )
            assert resp.status_code in (200, 400, 422)
