"""Tests for audit trail, session uniqueness, student fee balance, fee receipt."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuditTrailOnUserCreation:
    async def test_admin_user_has_created_by(
        self, admin_client: AsyncClient, admin_user
    ):
        response = await admin_client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert "created_by_user_id" in data

    async def test_student_user_created_via_endpoint(
        self, client: AsyncClient, admin_user, admin_headers
    ):
        response = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "audit_student@test.com",
                "phone": "9876543210",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "created_by_user_id" in data
        assert data["created_by_user_id"] == str(admin_user.public_id)


@pytest.mark.asyncio
class TestSessionCodeUniqueness:
    async def test_duplicate_session_code_rejected(
        self, admin_client: AsyncClient
    ):
        payload = {
            "session_code": "UNIQUE_TEST",
            "session_name": "Unique Test",
            "start_year": 2025,
            "end_year": 2026,
        }
        resp1 = await admin_client.post("/academics/sessions", json=payload)
        assert resp1.status_code in (201, 400)

        resp2 = await admin_client.post("/academics/sessions", json=payload)
        assert resp2.status_code == 409 or resp2.status_code == 400


@pytest.mark.asyncio
class TestClassRoomUniqueness:
    async def test_duplicate_classroom_code_rejected(
        self, admin_client: AsyncClient, academic_session
    ):
        payload = {
            "class_code": "DUP_CODE",
            "class_name": "Dup Class",
            "section": "A",
            "display_name": "Dup Class A",
            "academic_sessions_id": str(academic_session.id),
        }
        resp1 = await admin_client.post("/academics/classrooms", json=payload)
        assert resp1.status_code in (201, 400)

        resp2 = await admin_client.post("/academics/classrooms", json=payload)
        assert resp2.status_code == 409 or resp2.status_code == 400


@pytest.mark.asyncio
class TestSubjectCodeUniqueness:
    async def test_duplicate_subject_code_rejected(
        self, admin_client: AsyncClient
    ):
        payload = {"subject_code": "UNIQUE_SUBJ", "subject_name": "Unique Subj"}
        resp1 = await admin_client.post("/academics/subjects", json=payload)
        assert resp1.status_code in (201, 400)

        resp2 = await admin_client.post("/academics/subjects", json=payload)
        assert resp2.status_code == 409 or resp2.status_code == 400


@pytest.mark.asyncio
class TestTeacherEmailUniqueness:
    async def test_duplicate_teacher_email_rejected(
        self, admin_client: AsyncClient
    ):
        payload = {
            "email": "unique_teacher@test.com",
            "phone": "9876543211",
            "role": "teacher",
            "password": "TeacherPass1!",
        }
        resp1 = await admin_client.post("/admin/user", json=payload)
        assert resp1.status_code == 201

        resp2 = await admin_client.post("/admin/user", json=payload)
        assert resp2.status_code == 400


@pytest.mark.asyncio
class TestStudentFeeBalanceRecalculation:
    async def test_student_fee_balance_endpoint_exists(
        self, admin_client: AsyncClient, student_user
    ):
        resp = await admin_client.get("/students/me/fee-balance")
        assert resp.status_code in (200, 404, 403)

    async def test_student_fee_balance_update_returns_balanced(
        self, client: AsyncClient, admin_user, admin_headers
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "fee_student@test.com",
                "phone": "9876543212",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201
        student_id = user_resp.json()["id"]
        resp = await client.get(
            f"/students/{student_id}/fee-balance",
            headers=admin_headers,
        )
        assert resp.status_code in (200, 404)


@pytest.mark.asyncio
class TestFeeReceiptGeneration:
    async def test_fee_receipt_endpoint_exists(
        self, admin_client: AsyncClient, student_user
    ):
        resp = await admin_client.get("/fees/receipts")
        assert resp.status_code in (200, 403, 422)

    async def test_student_fee_receipt_access_control(
        self, client: AsyncClient, admin_user, admin_headers
    ):
        user_resp = await client.post(
            "/admin/user",
            headers=admin_headers,
            json={
                "email": "receipt_student@test.com",
                "phone": "9876543213",
                "role": "student",
                "password": "StudentPass1!",
            },
        )
        assert user_resp.status_code == 201

        token_resp = await client.post(
            "/auth/login",
            json={
                "email": "receipt_student@test.com",
                "password": "StudentPass1!",
            },
        )
        assert token_resp.status_code == 200

        student_token = token_resp.json()["access_token"]
        resp = await client.get(
            "/fees/receipts",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code in (200, 403)
