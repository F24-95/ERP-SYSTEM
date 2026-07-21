import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from .helpers import (
    assert_success_response,
    assert_error_response,
    INVALID_TOKENS,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.teacher]


class TestTeacherProfile:
    async def test_get_profile(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/teacher/profile", headers=teacher_headers)
        assert_success_response(response)
        data = response.json()
        assert "teacher_name" in data or "user_id" in data

    async def test_get_profile_no_auth(self, client: AsyncClient):
        response = await client.get("/teacher/profile")
        assert_error_response(response, 401)

    async def test_get_profile_wrong_role(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get("/teacher/profile", headers=student_headers)
        assert_error_response(response, 403)

    async def test_update_profile(self, client: AsyncClient, teacher_headers: dict):
        response = await client.put(
            "/teacher/profile",
            json={"teacher_name": "Updated Teacher Name", "phone": "9333333333"},
            headers=teacher_headers,
        )
        assert_success_response(response)

    async def test_update_profile_empty_name(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.put(
            "/teacher/profile",
            json={"teacher_name": ""},
            headers=teacher_headers,
        )
        assert response.status_code in (200, 422)


class TestTeacherClasses:
    async def test_get_classes(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/teacher/classes", headers=teacher_headers)
        assert_success_response(response)

    async def test_get_classes_no_auth(self, client: AsyncClient):
        response = await client.get("/teacher/classes")
        assert_error_response(response, 401)

    async def test_get_classes_wrong_role(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get("/teacher/classes", headers=student_headers)
        assert_error_response(response, 403)


class TestTeacherStudents:
    async def test_get_class_students(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get(
            "/teacher/students?classroom_id=1&academic_sessions_id=1",
            headers=teacher_headers,
        )
        assert response.status_code in (200, 404)

    async def test_get_class_students_missing_params(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get("/teacher/students", headers=teacher_headers)
        assert_error_response(response, 422)

    async def test_get_my_students(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get(
            "/teacher/my-students?academic_sessions_id=1", headers=teacher_headers
        )
        assert response.status_code in (200, 404)


class TestTeacherSubjects:
    async def test_get_subjects(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/teacher/subjects", headers=teacher_headers)
        assert_success_response(response)

    async def test_get_subjects_no_auth(self, client: AsyncClient):
        response = await client.get("/teacher/subjects")
        assert_error_response(response, 401)


class TestTeacherAssignments:
    async def test_get_assignments(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/teacher/assignments", headers=teacher_headers)
        assert_success_response(response)

    async def test_get_assignments_no_auth(self, client: AsyncClient):
        response = await client.get("/teacher/assignments")
        assert_error_response(response, 401)

    async def test_get_assignments_wrong_role(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get("/teacher/assignments", headers=student_headers)
        assert_error_response(response, 403)


class TestTeacherDashboard:
    async def test_get_dashboard(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/teacher/dashboard", headers=teacher_headers)
        assert_success_response(response)

    async def test_get_dashboard_no_auth(self, client: AsyncClient):
        response = await client.get("/teacher/dashboard")
        assert_error_response(response, 401)

    async def test_get_dashboard_wrong_role(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get("/teacher/dashboard", headers=student_headers)
        assert_error_response(response, 403)

    async def test_dashboard_from_dashboard_router(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get("/dashboard/teacher", headers=teacher_headers)
        assert_success_response(response)


class TestTeacherTimetable:
    async def test_get_teacher_timetable(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get("/teacher/timetable", headers=teacher_headers)
        assert_success_response(response)

    async def test_get_teacher_timetable_no_auth(self, client: AsyncClient):
        response = await client.get("/teacher/timetable")
        assert_error_response(response, 401)

    async def test_get_teacher_timetable_wrong_role(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get("/teacher/timetable", headers=student_headers)
        assert_error_response(response, 403)


class TestTeacherAvailability:
    async def test_get_availability(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get(
            "/availability/teacher/1?session_id=1",
            headers=teacher_headers,
        )
        assert response.status_code in (200, 404)

    async def test_create_availability(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.post(
            "/availability",
            json={
                "teacher_subject_id": 1,
                "week_day_id": 1,
                "time_slot_id": 1,
                "academic_sessions_id": 1,
                "is_active": True,
            },
            headers=teacher_headers,
        )
        assert response.status_code in (200, 201, 400, 404)

    async def test_update_availability(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.put(
            "/availability/1",
            json={"is_active": False},
            headers=teacher_headers,
        )
        assert response.status_code in (200, 404)

    async def test_delete_availability(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.delete("/availability/1", headers=teacher_headers)
        assert response.status_code in (204, 404)


class TestTeacherExams:
    async def test_create_exam(
        self, client: AsyncClient, teacher_headers: dict, db: AsyncSession
    ):
        from src.domain.academics.models import ClassSubject
        from sqlalchemy import select

        cs = (await db.execute(select(ClassSubject).limit(1))).scalars().first()
        if cs:
            response = await client.post(
                "/exams/",
                json={
                    "title": "Mid Term",
                    "class_subject_id": cs.id,
                    "exam_date": "2025-07-15",
                    "max_marks": 100,
                },
                headers=teacher_headers,
            )
            assert response.status_code in (200, 201, 400, 404)

    async def test_list_exams(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/exams/", headers=teacher_headers)
        assert_success_response(response)

    async def test_get_exam(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/exams/1", headers=teacher_headers)
        assert response.status_code in (200, 404)

    async def test_update_exam(self, client: AsyncClient, teacher_headers: dict):
        response = await client.put(
            "/exams/1",
            json={"title": "Updated Mid Term", "max_marks": 50},
            headers=teacher_headers,
        )
        assert response.status_code in (200, 404)

    async def test_delete_exam(self, client: AsyncClient, teacher_headers: dict):
        response = await client.delete("/exams/1", headers=teacher_headers)
        assert response.status_code in (200, 404)

    async def test_create_exam_no_auth(self, client: AsyncClient):
        response = await client.post(
            "/exams/",
            json={
                "title": "Test",
                "class_subject_id": 1,
                "exam_date": "2025-07-15",
                "max_marks": 100,
            },
        )
        assert_error_response(response, 401)

    async def test_create_exam_wrong_role(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.post(
            "/exams/",
            json={
                "title": "Test",
                "class_subject_id": 1,
                "exam_date": "2025-07-15",
                "max_marks": 100,
            },
            headers=student_headers,
        )
        assert_error_response(response, 403)


class TestTeacherAssignmentsCRUD:
    async def test_create_assignment(
        self, client: AsyncClient, teacher_headers: dict, db: AsyncSession
    ):
        from src.domain.academics.models import ClassSubject
        from sqlalchemy import select

        cs = (await db.execute(select(ClassSubject).limit(1))).scalars().first()
        if cs:
            response = await client.post(
                "/assignments/",
                json={
                    "title": "Homework 1",
                    "description": "Complete chapter 1",
                    "class_subject_id": cs.id,
                    "due_date": "2025-07-20",
                },
                headers=teacher_headers,
            )
            assert response.status_code in (200, 201, 400, 404)

    async def test_list_assignments(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/assignments/", headers=teacher_headers)
        assert_success_response(response)

    async def test_get_assignment(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/assignments/1", headers=teacher_headers)
        assert response.status_code in (200, 404)

    async def test_update_assignment(self, client: AsyncClient, teacher_headers: dict):
        response = await client.put(
            "/assignments/1",
            json={"title": "Updated Homework", "description": "Updated desc"},
            headers=teacher_headers,
        )
        assert response.status_code in (200, 404)

    async def test_delete_assignment(self, client: AsyncClient, teacher_headers: dict):
        response = await client.delete("/assignments/1", headers=teacher_headers)
        assert response.status_code in (200, 404)

    async def test_grade_assignment(self, client: AsyncClient, teacher_headers: dict):
        response = await client.post(
            "/assignments/1/results",
            json=[{"student_profile_id": 1, "marks_obtained": 85, "remarks": "Good"}],
            headers=teacher_headers,
        )
        assert response.status_code in (200, 201, 404)


class TestTeacherDailyClass:
    async def test_create_daily_class(
        self, client: AsyncClient, teacher_headers: dict, db: AsyncSession
    ):
        from src.domain.academics.models import ClassSubject
        from sqlalchemy import select

        cs = (await db.execute(select(ClassSubject).limit(1))).scalars().first()
        if cs:
            response = await client.post(
                "/daily-class/",
                json={
                    "teacher_subject_id": 1,
                    "class_subject_id": cs.id,
                    "class_date": "2025-07-10",
                    "topic": "Introduction to Algebra",
                },
                headers=teacher_headers,
            )
            assert response.status_code in (200, 201, 400, 404)

    async def test_list_daily_classes(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/daily-class/", headers=teacher_headers)
        assert_success_response(response)

    async def test_mark_attendance(self, client: AsyncClient, teacher_headers: dict):
        response = await client.post(
            "/daily-class/1/students",
            json=[{"student_profile_id": 1, "attendance_status": "Present"}],
            headers=teacher_headers,
        )
        assert response.status_code in (200, 201, 404)

    async def test_get_attendance(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/daily-class/1/students", headers=teacher_headers)
        assert response.status_code in (200, 404)

    async def test_recalculate_attendance_summary(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.post(
            "/daily-class/attendance/recalculate/1",
            headers=teacher_headers,
        )
        assert response.status_code in (200, 404)


class TestTeacherNotices:
    async def test_create_notice(
        self, client: AsyncClient, teacher_headers: dict, academic_session
    ):
        response = await client.post(
            "/notices/",
            data={
                "title": "Class Test Notice",
                "description": "Test next week",
                "notice_type": "ACADEMIC",
                "audience": "CLASS",
                "publish_date": "2025-06-10",
                "academic_sessions_id": str(academic_session.id),
                "classroom_id": "1",
                "is_pinned": "false",
            },
            headers=teacher_headers,
        )
        assert response.status_code in (200, 201, 422)

    async def test_pin_notice(
        self, client: AsyncClient, teacher_headers: dict, db: AsyncSession
    ):
        from src.domain.notices.models import Notice
        from sqlalchemy import select

        notice = (await db.execute(select(Notice).limit(1))).scalars().first()
        if notice:
            response = await client.post(
                f"/notices/{notice.id}/pin", headers=teacher_headers
            )
            assert_success_response(response)

    async def test_unpin_notice(
        self, client: AsyncClient, teacher_headers: dict, db: AsyncSession
    ):
        from src.domain.notices.models import Notice
        from sqlalchemy import select

        notice = (await db.execute(select(Notice).limit(1))).scalars().first()
        if notice:
            response = await client.post(
                f"/notices/{notice.id}/unpin", headers=teacher_headers
            )
            assert_success_response(response)


class TestTeacherChat:
    async def test_get_chat_rooms(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/chat/rooms", headers=teacher_headers)
        assert_success_response(response)

    async def test_create_chat_room(self, client: AsyncClient, teacher_headers: dict):
        response = await client.post(
            "/chat/rooms",
            json={"student_profile_id": 1, "subject": "Doubt session"},
            headers=teacher_headers,
        )
        assert response.status_code in (200, 201, 400, 404)

    async def test_get_unread_count(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/chat/unread", headers=teacher_headers)
        assert_success_response(response)


class TestTeacherAuthorizationNegative:
    @pytest.mark.parametrize("token", INVALID_TOKENS)
    async def test_invalid_tokens(self, client: AsyncClient, token: str):
        response = await client.get(
            "/teacher/profile", headers={"Authorization": token}
        )
        assert response.status_code in (401, 403)

    async def test_admin_accessing_teacher_endpoint(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.get("/teacher/profile", headers=admin_headers)
        assert_error_response(response, 403)

    async def test_student_accessing_teacher_endpoint(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get("/teacher/profile", headers=student_headers)
        assert_error_response(response, 403)


class TestTeacherTimetableBase:
    async def test_list_weekdays(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/weekdays", headers=teacher_headers)
        assert_success_response(response)

    async def test_list_timeslots(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/timeslots", headers=teacher_headers)
        assert_success_response(response)

    async def test_get_class_timetable(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get(
            "/timetable/class/1?session_id=1", headers=teacher_headers
        )
        assert response.status_code in (200, 404)

    async def test_create_timetable_entry(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.post(
            "/timetable",
            json={
                "classroom_id": 1,
                "teacher_subject_id": 1,
                "week_day_id": 1,
                "time_slot_id": 1,
                "academic_sessions_id": 1,
                "is_active": True,
            },
            headers=teacher_headers,
        )
        assert response.status_code in (200, 201, 400, 404)
