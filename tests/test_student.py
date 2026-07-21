import pytest
from httpx import AsyncClient

from .helpers import (
    assert_success_response,
    assert_error_response,
    INVALID_TOKENS,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.student]


class TestStudentProfile:
    async def test_get_profile(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/student/profile", headers=student_headers)
        assert_success_response(response)
        data = response.json()
        assert "student_name" in data or "user_id" in data

    async def test_get_profile_no_auth(self, client: AsyncClient):
        response = await client.get("/student/profile")
        assert_error_response(response, 401)

    async def test_get_profile_wrong_role(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get("/student/profile", headers=teacher_headers)
        assert_error_response(response, 403)

    async def test_update_profile(self, client: AsyncClient, student_headers: dict):
        response = await client.put(
            "/student/profile",
            json={"student_name": "Updated Student Name", "phone": "9444444444"},
            headers=student_headers,
        )
        assert_success_response(response)

    async def test_update_profile_invalid_data(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.put(
            "/student/profile",
            json={"date_of_birth": "invalid-date"},
            headers=student_headers,
        )
        assert response.status_code in (200, 422)


class TestStudentClasses:
    async def test_get_classes(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/student/classes", headers=student_headers)
        assert_success_response(response)

    async def test_get_classes_no_auth(self, client: AsyncClient):
        response = await client.get("/student/classes")
        assert_error_response(response, 401)

    async def test_get_classes_wrong_role(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get("/student/classes", headers=teacher_headers)
        assert_error_response(response, 403)


class TestStudentAttendance:
    async def test_get_attendance_summary(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get(
            "/student/attendance/summary?academic_sessions_id=1",
            headers=student_headers,
        )
        assert response.status_code in (200, 404)

    async def test_get_attendance_summary_no_auth(self, client: AsyncClient):
        response = await client.get(
            "/student/attendance/summary?academic_sessions_id=1"
        )
        assert_error_response(response, 401)

    async def test_get_attendance_summary_missing_param(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get(
            "/student/attendance/summary", headers=student_headers
        )
        assert_error_response(response, 422)

    async def test_get_daily_attendance(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get(
            "/student/attendance/daily?academic_sessions_id=1",
            headers=student_headers,
        )
        assert_success_response(response)

    async def test_get_daily_attendance_with_dates(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get(
            "/student/attendance/daily?academic_sessions_id=1&start_date=2025-01-01&end_date=2025-12-31",
            headers=student_headers,
        )
        assert_success_response(response)


class TestStudentAssignments:
    async def test_get_assignments(self, client: AsyncClient, student_headers: dict):
        response = await client.get(
            "/student/assignments?academic_sessions_id=1",
            headers=student_headers,
        )
        assert_success_response(response)

    async def test_get_assignments_no_auth(self, client: AsyncClient):
        response = await client.get("/student/assignments?academic_sessions_id=1")
        assert_error_response(response, 401)

    async def test_get_assignments_wrong_role(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get(
            "/student/assignments?academic_sessions_id=1", headers=teacher_headers
        )
        assert_error_response(response, 403)

    async def test_get_assignments_with_subject(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get(
            "/student/assignments?academic_sessions_id=1&subject_id=1",
            headers=student_headers,
        )
        assert_success_response(response)


class TestStudentExams:
    async def test_get_exam_results(self, client: AsyncClient, student_headers: dict):
        response = await client.get(
            "/student/exams?academic_sessions_id=1",
            headers=student_headers,
        )
        assert_success_response(response)

    async def test_get_exam_results_no_auth(self, client: AsyncClient):
        response = await client.get("/student/exams?academic_sessions_id=1")
        assert_error_response(response, 401)

    async def test_get_exam_results_wrong_role(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get(
            "/student/exams?academic_sessions_id=1", headers=teacher_headers
        )
        assert_error_response(response, 403)

    async def test_get_exam_results_with_subject(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get(
            "/student/exams?academic_sessions_id=1&subject_id=1",
            headers=student_headers,
        )
        assert_success_response(response)


class TestStudentFees:
    async def test_get_fees(self, client: AsyncClient, student_headers: dict):
        response = await client.get(
            "/student/fees?academic_sessions_id=1",
            headers=student_headers,
        )
        assert_success_response(response)

    async def test_get_fees_no_auth(self, client: AsyncClient):
        response = await client.get("/student/fees?academic_sessions_id=1")
        assert_error_response(response, 401)

    async def test_get_fees_with_status(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get(
            "/student/fees?academic_sessions_id=1&status=PENDING",
            headers=student_headers,
        )
        assert_success_response(response)

    async def test_get_fee_summary(self, client: AsyncClient, student_headers: dict):
        response = await client.get(
            "/student/fees/summary?academic_sessions_id=1",
            headers=student_headers,
        )
        assert_success_response(response)


class TestStudentDashboard:
    async def test_get_dashboard(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/dashboard/student", headers=student_headers)
        assert_success_response(response)

    async def test_get_dashboard_no_auth(self, client: AsyncClient):
        response = await client.get("/dashboard/student")
        assert_error_response(response, 401)

    async def test_get_dashboard_wrong_role(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get("/dashboard/student", headers=teacher_headers)
        assert_error_response(response, 403)


class TestStudentTimetable:
    async def test_get_timetable(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/student/timetable", headers=student_headers)
        assert_success_response(response)

    async def test_get_timetable_no_auth(self, client: AsyncClient):
        response = await client.get("/student/timetable")
        assert_error_response(response, 401)

    async def test_get_timetable_wrong_role(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get("/student/timetable", headers=teacher_headers)
        assert_error_response(response, 403)


class TestStudentOwnFeeView:
    async def test_get_my_fees(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/fees/my", headers=student_headers)
        assert_success_response(response)

    async def test_get_my_fees_no_auth(self, client: AsyncClient):
        response = await client.get("/fees/my")
        assert_error_response(response, 401)

    async def test_get_my_fees_wrong_role(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get("/fees/my", headers=teacher_headers)
        assert_error_response(response, 403)


class TestStudentIDCard:
    async def test_view_id_card(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/student/id-card/1", headers=student_headers)
        assert response.status_code in (200, 404)

    async def test_download_id_card(self, client: AsyncClient, student_headers: dict):
        response = await client.get(
            "/student/id-card/1/download", headers=student_headers
        )
        assert response.status_code in (200, 404)


class TestStudentReports:
    async def test_generate_report(self, client: AsyncClient, student_headers: dict):
        response = await client.post(
            "/reports/generate",
            json={
                "student_profile_id": 1,
                "data_start_date": "2025-01-01",
                "data_end_date": "2025-12-31",
            },
            headers=student_headers,
        )
        assert response.status_code in (200, 201, 404, 403)

    async def test_list_own_reports(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/reports/student/1", headers=student_headers)
        assert response.status_code in (200, 404)

    async def test_download_report(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/reports/1/download", headers=student_headers)
        assert response.status_code in (200, 404)


class TestStudentKhanAcademy:
    async def test_get_student_progress(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get(
            "/khan-academy/progress/student/1", headers=student_headers
        )
        assert response.status_code in (200, 404)

    async def test_get_student_activity(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get(
            "/khan-academy/activity/student/1", headers=student_headers
        )
        assert response.status_code in (200, 404)


class TestStudentChat:
    async def test_get_chat_rooms(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/chat/rooms", headers=student_headers)
        assert_success_response(response)

    async def test_get_unread_counts(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/chat/unread", headers=student_headers)
        assert_success_response(response)


class TestStudentNotices:
    async def test_get_notices(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/notices/", headers=student_headers)
        assert_success_response(response)

    async def test_get_notice_by_id(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/notices/1", headers=student_headers)
        assert response.status_code in (200, 404)


class TestStudentUsersMe:
    async def test_get_users_me(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/users/me", headers=student_headers)
        assert_success_response(response)

    async def test_get_users_me_no_auth(self, client: AsyncClient):
        response = await client.get("/users/me")
        assert_error_response(response, 401)

    async def test_update_users_me(self, client: AsyncClient, student_headers: dict):
        response = await client.patch(
            "/users/me",
            json={"phone": "9555555555"},
            headers=student_headers,
        )
        assert_success_response(response)


class TestStudentAuthorizationNegative:
    @pytest.mark.parametrize("token", INVALID_TOKENS)
    async def test_invalid_tokens(self, client: AsyncClient, token: str):
        response = await client.get(
            "/student/profile", headers={"Authorization": token}
        )
        assert response.status_code in (401, 403)

    async def test_admin_accessing_student_endpoint(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.get("/student/profile", headers=admin_headers)
        assert_error_response(response, 403)

    async def test_teacher_accessing_student_endpoint(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get("/student/profile", headers=teacher_headers)
        assert_error_response(response, 403)
