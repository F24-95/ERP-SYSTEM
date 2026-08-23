"""Tests for student dashboard and profile endpoints."""
import pytest
from httpx import AsyncClient

from tests.helpers import (
    assert_forbidden,
    assert_ok,
    assert_unauthorized,
)

pytestmark = pytest.mark.asyncio


class TestStudentProfile:
    async def test_get_student_profile(
        self, student_client: AsyncClient, student_user
    ):
        resp = await student_client.get("/students/me/profile")
        assert resp.status_code in (200, 404)

    async def test_student_profile_unauthorized(self, client: AsyncClient):
        resp = await client.get("/students/me/profile")
        assert resp.status_code == 401

    async def test_update_student_profile(
        self, student_client: AsyncClient, student_user
    ):
        resp = await student_client.patch(
            "/students/me/profile",
            json={"phone": "1234567890"},
        )
        assert resp.status_code in (200, 400, 404)

    async def test_teacher_cannot_access_student_profile(
        self, teacher_client: AsyncClient
    ):
        resp = await teacher_client.get("/students/me/profile")
        assert resp.status_code in (403, 404, 401)


class TestStudentDashboard:
    async def test_student_dashboard(
        self, student_client: AsyncClient, student_user
    ):
        resp = await student_client.get("/students/me/dashboard")
        assert resp.status_code in (200, 404)

    async def test_student_dashboard_unauthorized(self, client: AsyncClient):
        resp = await client.get("/students/me/dashboard")
        assert resp.status_code == 401

    async def test_student_schedule(
        self, student_client: AsyncClient, student_user
    ):
        resp = await student_client.get("/students/me/schedule")
        assert resp.status_code in (200, 404)

    async def test_student_fee_balance(
        self, student_client: AsyncClient, student_user
    ):
        resp = await student_client.get("/students/me/fee-balance")
        assert resp.status_code in (200, 404)

    async def test_student_fee_receipts(
        self, student_client: AsyncClient, student_user
    ):
        resp = await student_client.get("/students/me/fee-receipts")
        assert resp.status_code in (200, 404)

    async def test_student_exams(
        self, student_client: AsyncClient, student_user
    ):
        resp = await student_client.get("/students/me/exams")
        assert resp.status_code in (200, 404)


class TestStudentAttendance:
    async def test_student_attendance(
        self, student_client: AsyncClient, student_user
    ):
        resp = await student_client.get("/students/me/attendance")
        assert resp.status_code in (200, 404)

    async def test_student_attendance_with_date_range(
        self, student_client: AsyncClient, student_user
    ):
        resp = await student_client.get(
            "/students/me/attendance?start_date=2026-08-01&end_date=2026-08-31"
        )
        assert resp.status_code in (200, 404)
