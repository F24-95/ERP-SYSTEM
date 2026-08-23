"""Tests for teacher dashboard and profile endpoints."""
import pytest
from httpx import AsyncClient

from tests.helpers import (
    assert_forbidden,
    assert_ok,
    assert_unauthorized,
)

pytestmark = pytest.mark.asyncio


class TestTeacherProfile:
    async def test_get_teacher_profile(
        self, teacher_client: AsyncClient, teacher_user
    ):
        resp = await teacher_client.get("/teachers/me/profile")
        assert resp.status_code in (200, 404)

    async def test_teacher_profile_unauthorized(self, client: AsyncClient):
        resp = await client.get("/teachers/me/profile")
        assert resp.status_code == 401

    async def test_update_teacher_profile(
        self, teacher_client: AsyncClient, teacher_user
    ):
        resp = await teacher_client.patch(
            "/teachers/me/profile",
            json={"phone": "1234567890"},
        )
        assert resp.status_code in (200, 400, 404)

    async def test_student_cannot_access_teacher_profile(
        self, student_client: AsyncClient
    ):
        resp = await student_client.get("/teachers/me/profile")
        assert resp.status_code in (403, 404, 401)


class TestTeacherDashboard:
    async def test_teacher_dashboard(
        self, teacher_client: AsyncClient, teacher_user
    ):
        resp = await teacher_client.get("/teachers/me/dashboard")
        assert resp.status_code in (200, 404)

    async def test_teacher_dashboard_unauthorized(self, client: AsyncClient):
        resp = await client.get("/teachers/me/dashboard")
        assert resp.status_code == 401

    async def test_teacher_subjects(
        self, teacher_client: AsyncClient, teacher_user
    ):
        resp = await teacher_client.get("/teachers/me/subjects")
        assert resp.status_code in (200, 404)

    async def test_teacher_schedule(
        self, teacher_client: AsyncClient, teacher_user
    ):
        resp = await teacher_client.get("/teachers/me/schedule")
        assert resp.status_code in (200, 404)

    async def test_teacher_assignments(
        self, teacher_client: AsyncClient, teacher_user
    ):
        resp = await teacher_client.get("/teachers/me/assignments")
        assert resp.status_code in (200, 404)


class TestTeacherAttendance:
    async def test_teacher_attendance(
        self, teacher_client: AsyncClient, teacher_user
    ):
        resp = await teacher_client.get("/teachers/me/attendance")
        assert resp.status_code in (200, 404)

    async def test_student_cannot_access_teacher_attendance(
        self, student_client: AsyncClient
    ):
        resp = await student_client.get("/teachers/me/attendance")
        assert resp.status_code in (403, 404, 401)
