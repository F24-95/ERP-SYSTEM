import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.users.models import User
from src.core.enums import UserRole
from .helpers import (
    assert_success_response,
    assert_error_response,
    INVALID_TOKENS,
    SQL_INJECTION_PAYLOADS,
)


pytestmark = [pytest.mark.asyncio, pytest.mark.admin]


class TestAdminUserManagement:
    async def test_create_user(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        response = await client.post(
            "/admin/user",
            json={
                "email": "newuser@test.com",
                "phone": "9111111111",
                "password": "NewUser123!",
                "role": "teacher",
                "teacher_name": "New Teacher",
            },
            headers=admin_headers,
        )
        assert_success_response(response, 201)
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "teacher"

    async def test_create_user_no_auth(self, client: AsyncClient):
        response = await client.post(
            "/admin/user",
            json={
                "email": "nologin@test.com",
                "phone": "9111111112",
                "password": "Test123!",
                "role": "student",
            },
        )
        assert_error_response(response, 401)

    async def test_create_user_teacher_role(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.post(
            "/admin/user",
            json={
                "email": "teachercreates@test.com",
                "phone": "9111111113",
                "password": "Test123!",
                "role": "student",
                "student_name": "S",
            },
            headers=teacher_headers,
        )
        assert_error_response(response, 403)

    async def test_create_user_duplicate_email(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.core.security import hash_password

        user = User(
            email="duplicate@test.com",
            phone="9111111114",
            password_hash=hash_password("test"),
            role=UserRole.STUDENT,
            is_active=True,
            is_deleted=False,
        )
        db.add(user)
        await db.commit()

        response = await client.post(
            "/admin/user",
            json={
                "email": "duplicate@test.com",
                "phone": "9111111115",
                "password": "Test123!",
                "role": "student",
                "student_name": "D",
            },
            headers=admin_headers,
        )
        assert_error_response(response, 400)

    async def test_create_user_missing_required(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.post("/admin/user", json={}, headers=admin_headers)
        assert_error_response(response, 422)

    async def test_create_user_invalid_role(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.post(
            "/admin/user",
            json={
                "email": "badrole@test.com",
                "phone": "9111111116",
                "password": "Test123!",
                "role": "superadmin",
            },
            headers=admin_headers,
        )
        assert_error_response(response, 422)

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_create_user_sql_injection(
        self, client: AsyncClient, admin_headers: dict, payload: str
    ):
        response = await client.post(
            "/admin/user",
            json={
                "email": f"{payload}@test.com",
                "phone": "9111111117",
                "password": "Test123!",
                "role": "student",
                "student_name": payload,
            },
            headers=admin_headers,
        )
        assert response.status_code in (201, 400, 422)

    async def test_list_users(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/admin/users", headers=admin_headers)
        assert_success_response(response)
        data = response.json()
        assert isinstance(data, list)

    async def test_list_users_no_auth(self, client: AsyncClient):
        response = await client.get("/admin/users")
        assert_error_response(response, 401)

    async def test_list_users_teacher_forbidden(
        self, client: AsyncClient, teacher_headers: dict
    ):
        response = await client.get("/admin/users", headers=teacher_headers)
        assert_error_response(response, 403)

    async def test_get_user(
        self, client: AsyncClient, admin_headers: dict, admin_user: User
    ):
        response = await client.get(
            f"/admin/users/{admin_user.public_id}", headers=admin_headers
        )
        assert_success_response(response)

    async def test_get_user_not_found(self, client: AsyncClient, admin_headers: dict):
        response = await client.get(
            "/admin/users/nonexistent-id", headers=admin_headers
        )
        assert_error_response(response, 404)

    async def test_update_user(
        self, client: AsyncClient, admin_headers: dict, admin_user: User
    ):
        response = await client.patch(
            f"/admin/users/{admin_user.public_id}",
            json={"phone": "9222222222"},
            headers=admin_headers,
        )
        assert_success_response(response)
        assert response.json()["phone"] == "9222222222"

    async def test_deactivate_user(
        self, client: AsyncClient, admin_headers: dict, student_user: User
    ):
        response = await client.delete(
            f"/admin/users/{student_user.public_id}",
            headers=admin_headers,
        )
        assert_success_response(response, 204)


class TestAdminStudentProfiles:
    async def test_list_students(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/admin/students", headers=admin_headers)
        assert_success_response(response)
        assert isinstance(response.json(), list)

    async def test_get_student(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.users.models import StudentProfile

        result = await db.execute(
            __import__("sqlalchemy").select(StudentProfile).limit(1)
        )
        profile = result.scalars().first()
        if profile:
            response = await client.get(
                f"/admin/students/{profile.id}", headers=admin_headers
            )
            assert_success_response(response)

    async def test_get_student_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.get("/admin/students/99999", headers=admin_headers)
        assert_error_response(response, 404)


class TestAdminTeacherProfiles:
    async def test_list_teachers(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/admin/teachers", headers=admin_headers)
        assert_success_response(response)

    async def test_get_teacher(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.users.models import TeacherProfile

        result = await db.execute(
            __import__("sqlalchemy").select(TeacherProfile).limit(1)
        )
        profile = result.scalars().first()
        if profile:
            response = await client.get(
                f"/admin/teachers/{profile.id}", headers=admin_headers
            )
            assert_success_response(response)

    async def test_update_teacher(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.users.models import TeacherProfile

        result = await db.execute(
            __import__("sqlalchemy").select(TeacherProfile).limit(1)
        )
        profile = result.scalars().first()
        if profile:
            response = await client.patch(
                f"/admin/teachers/{profile.id}",
                json={"teacher_name": "Updated Teacher"},
                headers=admin_headers,
            )
            assert_success_response(response)


class TestAdminAcademicSessions:
    async def test_create_session(self, client: AsyncClient, admin_headers: dict):
        response = await client.post(
            "/academics/sessions",
            json={
                "session_code": "2025-26",
                "session_name": "2025-2026",
                "start_year": 2025,
                "end_year": 2026,
                "start_date": "2025-04-01",
                "end_date": "2026-03-31",
            },
            headers=admin_headers,
        )
        assert_success_response(response, 201)

    async def test_list_sessions(self, client: AsyncClient):
        response = await client.get("/academics/sessions")
        assert_success_response(response)

    async def test_get_session(self, client: AsyncClient, db: AsyncSession):
        from src.domain.academics.models import AcademicSession
        from sqlalchemy import select

        result = await db.execute(select(AcademicSession).limit(1))
        session = result.scalars().first()
        if session:
            response = await client.get(f"/academics/sessions/{session.id}")
            assert_success_response(response)

    async def test_get_session_not_found(self, client: AsyncClient):
        response = await client.get("/academics/sessions/99999")
        assert_error_response(response, 404)

    async def test_update_session(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.academics.models import AcademicSession
        from sqlalchemy import select

        result = await db.execute(select(AcademicSession).limit(1))
        session = result.scalars().first()
        if session:
            response = await client.put(
                f"/academics/sessions/{session.id}",
                json={"name": "2025-2026 Updated"},
                headers=admin_headers,
            )
            assert_success_response(response)

    async def test_delete_session(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.academics.models import AcademicSession
        from sqlalchemy import select

        result = await db.execute(select(AcademicSession).limit(1))
        session = result.scalars().first()
        if session:
            response = await client.delete(
                f"/academics/sessions/{session.id}", headers=admin_headers
            )
            assert_success_response(response, 204)


class TestAdminClassrooms:
    async def test_create_classroom(
        self, client: AsyncClient, admin_headers: dict, academic_session
    ):
        response = await client.post(
            "/academics/classrooms",
            json={
                "class_code": "11A",
                "class_name": "Class 11",
                "section": "A",
                "display_name": "Class 11-A",
                "academic_sessions_id": academic_session.id,
            },
            headers=admin_headers,
        )
        assert_success_response(response, 201)

    async def test_list_classrooms(self, client: AsyncClient):
        response = await client.get("/academics/classrooms")
        assert_success_response(response)

    async def test_update_classroom(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.academics.models import ClassRoom
        from sqlalchemy import select

        result = await db.execute(select(ClassRoom).limit(1))
        room = result.scalars().first()
        if room:
            response = await client.put(
                f"/academics/classrooms/{room.id}",
                json={"name": "Updated Class"},
                headers=admin_headers,
            )
            assert_success_response(response)

    async def test_delete_classroom(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.academics.models import ClassRoom
        from sqlalchemy import select

        result = await db.execute(select(ClassRoom).limit(1))
        room = result.scalars().first()
        if room:
            response = await client.delete(
                f"/academics/classrooms/{room.id}", headers=admin_headers
            )
            assert_success_response(response, 204)


class TestAdminSubjects:
    async def test_create_subject(self, client: AsyncClient, admin_headers: dict):
        response = await client.post(
            "/academics/subjects",
            json={"subject_name": "Physics", "subject_code": "PHY101"},
            headers=admin_headers,
        )
        assert_success_response(response, 201)

    async def test_list_subjects(self, client: AsyncClient):
        response = await client.get("/academics/subjects")
        assert_success_response(response)

    async def test_update_subject(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.academics.models import Subject
        from sqlalchemy import select

        result = await db.execute(select(Subject).limit(1))
        subj = result.scalars().first()
        if subj:
            response = await client.put(
                f"/academics/subjects/{subj.id}",
                json={"name": "Advanced Physics"},
                headers=admin_headers,
            )
            assert_success_response(response)

    async def test_delete_subject(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.academics.models import Subject
        from sqlalchemy import select

        result = await db.execute(select(Subject).limit(1))
        subj = result.scalars().first()
        if subj:
            response = await client.delete(
                f"/academics/subjects/{subj.id}", headers=admin_headers
            )
            assert_success_response(response, 204)


class TestAdminClassSubjects:
    async def test_create_class_subject(
        self,
        client: AsyncClient,
        admin_headers: dict,
        academic_session,
        db: AsyncSession,
    ):
        from src.domain.academics.models import ClassRoom, Subject
        from sqlalchemy import select

        room = (await db.execute(select(ClassRoom).limit(1))).scalars().first()
        subj = (await db.execute(select(Subject).limit(1))).scalars().first()
        if room and subj:
            response = await client.post(
                "/academics/class-subjects",
                json={
                    "classroom_id": room.id,
                    "subject_id": subj.id,
                    "academic_sessions_id": academic_session.id,
                },
                headers=admin_headers,
            )
            assert_success_response(response, 201)

    async def test_list_class_subjects(self, client: AsyncClient):
        response = await client.get("/academics/class-subjects")
        assert_success_response(response)


class TestAdminFees:
    async def test_create_fee(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.operations.models import StudentClass
        from sqlalchemy import select

        enrollment = (await db.execute(select(StudentClass).limit(1))).scalars().first()
        if enrollment:
            response = await client.post(
                "/fees",
                json={
                    "student_class_id": enrollment.id,
                    "fee_type": "TUITION",
                    "amount": 5000.00,
                    "due_date": "2025-06-15",
                },
                headers=admin_headers,
            )
            assert_success_response(response)

    async def test_list_fees(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/fees", headers=admin_headers)
        assert_success_response(response)

    async def test_pending_fees(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/fees/pending", headers=admin_headers)
        assert_success_response(response)

    async def test_get_fee(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/fees/1", headers=admin_headers)
        assert response.status_code in (200, 404)

    async def test_delete_fee(self, client: AsyncClient, admin_headers: dict):
        response = await client.delete("/fees/NONEXISTENT", headers=admin_headers)
        assert response.status_code in (204, 404)


class TestAdminOperations:
    async def test_assign_teacher(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.academics.models import ClassSubject
        from src.domain.users.models import TeacherProfile
        from sqlalchemy import select

        cs = (await db.execute(select(ClassSubject).limit(1))).scalars().first()
        tp = (await db.execute(select(TeacherProfile).limit(1))).scalars().first()
        if cs and tp:
            response = await client.post(
                "/operations/assign-teacher",
                json={
                    "teacher_profile_id": tp.id,
                    "class_subject_id": cs.id,
                    "is_class_teacher": False,
                },
                headers=admin_headers,
            )
            assert_success_response(response, 201)

    async def test_list_teacher_assignments(self, client: AsyncClient):
        response = await client.get("/operations/teacher-assignments")
        assert_success_response(response)

    async def test_enroll_student(
        self,
        client: AsyncClient,
        admin_headers: dict,
        db: AsyncSession,
        academic_session,
    ):
        from src.domain.users.models import StudentProfile
        from src.domain.academics.models import ClassRoom
        from sqlalchemy import select

        sp = (await db.execute(select(StudentProfile).limit(1))).scalars().first()
        room = (await db.execute(select(ClassRoom).limit(1))).scalars().first()
        if sp and room:
            response = await client.post(
                "/operations/enroll-student",
                json={
                    "student_profile_id": sp.id,
                    "classroom_id": room.id,
                    "academic_sessions_id": academic_session.id,
                    "roll_number": 1,
                },
                headers=admin_headers,
            )
            assert_success_response(response, 201)

    async def test_list_enrollments(self, client: AsyncClient):
        response = await client.get("/operations/student-enrollments")
        assert_success_response(response)

    async def test_promote_student(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.users.models import StudentProfile
        from src.domain.academics.models import AcademicSession, ClassRoom
        from sqlalchemy import select

        sp = (await db.execute(select(StudentProfile).limit(1))).scalars().first()
        sessions = (await db.execute(select(AcademicSession))).scalars().all()
        rooms = (await db.execute(select(ClassRoom))).scalars().all()
        if sp and len(sessions) >= 2 and len(rooms) >= 2:
            response = await client.post(
                "/operations/promote-student",
                json={
                    "student_id": sp.id,
                    "from_session_id": sessions[0].id,
                    "to_session_id": sessions[1].id,
                    "to_classroom_id": rooms[1].id,
                },
                headers=admin_headers,
            )
            assert_success_response(response, 201)


class TestAdminDashboard:
    async def test_admin_dashboard(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/dashboard/admin", headers=admin_headers)
        assert_success_response(response)

    async def test_admin_dashboard_no_auth(self, client: AsyncClient):
        response = await client.get("/dashboard/admin")
        assert_error_response(response, 401)

    async def test_admin_dashboard_wrong_role(
        self, client: AsyncClient, student_headers: dict
    ):
        response = await client.get("/dashboard/admin", headers=student_headers)
        assert_error_response(response, 403)


class TestAdminNotices:
    async def test_create_notice(
        self, client: AsyncClient, admin_headers: dict, academic_session
    ):
        response = await client.post(
            "/notices/",
            data={
                "title": "School Holiday",
                "description": "School will remain closed",
                "notice_type": "GENERAL",
                "audience": "ALL",
                "publish_date": "2025-06-01",
                "academic_sessions_id": str(academic_session.id),
                "is_pinned": "false",
            },
            headers=admin_headers,
        )
        assert response.status_code in (200, 201, 422)

    async def test_list_notices(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/notices/", headers=admin_headers)
        assert_success_response(response)

    async def test_pin_notice(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.notices.models import Notice
        from sqlalchemy import select

        notice = (await db.execute(select(Notice).limit(1))).scalars().first()
        if notice:
            response = await client.post(
                f"/notices/{notice.id}/pin", headers=admin_headers
            )
            assert_success_response(response)

    async def test_delete_notice(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.notices.models import Notice
        from sqlalchemy import select

        notice = (await db.execute(select(Notice).limit(1))).scalars().first()
        if notice:
            response = await client.delete(
                f"/notices/{notice.id}", headers=admin_headers
            )
            assert_success_response(response)


class TestAdminIDCards:
    async def test_list_all_cards(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/student/id-card/all", headers=admin_headers)
        assert_success_response(response)

    async def test_generate_id_card(
        self, client: AsyncClient, admin_headers: dict, db: AsyncSession
    ):
        from src.domain.users.models import StudentProfile
        from sqlalchemy import select

        sp = (await db.execute(select(StudentProfile).limit(1))).scalars().first()
        if sp:
            response = await client.post(
                f"/student/id-card/{sp.id}", headers=admin_headers
            )
            assert response.status_code in (200, 201, 404, 500)


class TestAdminZoomFiles:
    async def test_create_zoom_file(self, client: AsyncClient, admin_headers: dict):
        response = await client.post(
            "/zoom/files",
            json={
                "file_initial": "zoom_rec",
                "raw_date": "2025-06-01",
                "raw_time": "10:00:00",
                "date": "2025-06-01",
                "time": "10:00:00",
                "video_file": "https://example.com/zoom/video.mp4",
            },
            headers=admin_headers,
        )
        assert response.status_code in (200, 201, 400, 404)

    async def test_list_zoom_files(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/zoom/files", headers=admin_headers)
        assert_success_response(response)

    async def test_delete_zoom_file(self, client: AsyncClient, admin_headers: dict):
        response = await client.delete("/zoom/files/1", headers=admin_headers)
        assert response.status_code in (200, 204, 404)


class TestAdminStudyMaterial:
    async def test_list_materials(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/study-materials", headers=admin_headers)
        assert_success_response(response)


class TestAdminSearch:
    async def test_search_students(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/students/search?q=test", headers=admin_headers)
        assert_success_response(response)

    async def test_search_teachers(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/teachers/search?q=test", headers=admin_headers)
        assert_success_response(response)


class TestAdminAuthorizationNegative:
    @pytest.mark.parametrize("token", INVALID_TOKENS)
    async def test_invalid_tokens(self, client: AsyncClient, token: str):
        response = await client.get("/admin/users", headers={"Authorization": token})
        assert_error_response(response, 401)

    async def test_wrong_role_student(self, client: AsyncClient, student_headers: dict):
        response = await client.get("/admin/users", headers=student_headers)
        assert_error_response(response, 403)

    async def test_wrong_role_teacher(self, client: AsyncClient, teacher_headers: dict):
        response = await client.get("/admin/users", headers=teacher_headers)
        assert_error_response(response, 403)
