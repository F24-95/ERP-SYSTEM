import pytest
from httpx import AsyncClient

from tests.helpers import assert_forbidden, assert_ok, assert_unauthorized

pytestmark = pytest.mark.asyncio


class TestTeacherProfile:
    async def test_get_profile(self, teacher_client: AsyncClient):
        response = await teacher_client.get("/teacher/profile")
        assert_ok(response)
        data = response.json()
        assert data["teacher_name"] == "Test Teacher"

    async def test_get_profile_unauthorized(self, client: AsyncClient):
        response = await client.get("/teacher/profile")
        assert_unauthorized(response)

    async def test_get_profile_forbidden_student(self, student_client: AsyncClient):
        response = await student_client.get("/teacher/profile")
        assert_forbidden(response)

    async def test_update_profile(self, teacher_client: AsyncClient):
        response = await teacher_client.put(
            "/teacher/profile",
            json={"teacher_name": "Updated Teacher Name", "department": "Science"},
        )
        assert_ok(response)
        data = response.json()
        assert data["teacher_name"] == "Updated Teacher Name"

    async def test_update_profile_invalid(self, teacher_client: AsyncClient):
        response = await teacher_client.put(
            "/teacher/profile",
            json={"experience_years": "not-a-number"},
        )
        assert response.status_code == 422


class TestTeacherClasses:
    async def test_get_classes_empty(self, teacher_client: AsyncClient):
        response = await teacher_client.get("/teacher/classes")
        assert_ok(response)
        assert response.json() == []

    async def test_get_classes_with_assignment(
        self,
        teacher_client: AsyncClient,
        teacher_user,
        academic_session,
        classroom,
        subject,
        db_session,
    ):
        from src.domain.academics.models import ClassSubject
        from src.domain.operations.models import TeacherSubject

        cs = ClassSubject(
            academic_sessions_id=academic_session.id,
            classroom_id=classroom.id,
            subject_id=subject.id,
        )
        db_session.add(cs)
        await db_session.flush()

        ts = TeacherSubject(
            teacher_id=teacher_user.id,
            class_subject_id=cs.id,
            classroom_id=classroom.id,
            subject_id=subject.id,
            academic_sessions_id=academic_session.id,
        )
        db_session.add(ts)
        await db_session.flush()

        response = await teacher_client.get("/teacher/classes")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1


class TestTeacherSubjects:
    async def test_get_subjects_empty(self, teacher_client: AsyncClient):
        response = await teacher_client.get("/teacher/subjects")
        assert_ok(response)
        assert response.json() == []

    async def test_get_subjects_with_assignment(
        self,
        teacher_client: AsyncClient,
        teacher_user,
        academic_session,
        classroom,
        subject,
        db_session,
    ):
        from src.domain.academics.models import ClassSubject
        from src.domain.operations.models import TeacherSubject

        cs = ClassSubject(
            academic_sessions_id=academic_session.id,
            classroom_id=classroom.id,
            subject_id=subject.id,
        )
        db_session.add(cs)
        await db_session.flush()

        ts = TeacherSubject(
            teacher_id=teacher_user.id,
            class_subject_id=cs.id,
            classroom_id=classroom.id,
            subject_id=subject.id,
            academic_sessions_id=academic_session.id,
        )
        db_session.add(ts)
        await db_session.flush()

        response = await teacher_client.get("/teacher/subjects")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1


class TestTeacherDashboard:
    async def test_get_dashboard(self, teacher_client: AsyncClient):
        response = await teacher_client.get("/teacher/dashboard")
        assert_ok(response)
        data = response.json()
        assert "total_classes" in data
        assert "total_students" in data
        assert "total_assignments" in data


class TestTeacherAssignments:
    async def test_get_assignments_empty(self, teacher_client: AsyncClient):
        response = await teacher_client.get("/teacher/assignments")
        assert_ok(response)
        assert response.json() == []


class TestTeacherStudents:
    async def test_get_class_students_no_assignment(
        self, teacher_client: AsyncClient, academic_session, classroom
    ):
        response = await teacher_client.get(
            "/teacher/students",
            params={
                "classroom_id": classroom.id,
                "academic_sessions_id": academic_session.id,
            },
        )
        assert response.status_code == 403


class TestTeacherOperations:
    async def test_teacher_can_list_students(
        self, teacher_client: AsyncClient, student_user
    ):
        response = await teacher_client.get("/admin/students")
        assert_ok(response)

    async def test_teacher_can_list_teachers(
        self, teacher_client: AsyncClient, teacher_user
    ):
        response = await teacher_client.get("/admin/teachers")
        assert_ok(response)

    async def test_teacher_cannot_delete_user(
        self, teacher_client: AsyncClient, student_user
    ):
        response = await teacher_client.delete(f"/admin/users/{student_user.public_id}")
        assert_forbidden(response)

    async def test_teacher_cannot_update_student_profile(
        self, teacher_client: AsyncClient, student_user, db_session
    ):
        from sqlalchemy import select
        from src.domain.users.models import StudentProfile

        result = await db_session.execute(
            select(StudentProfile).filter_by(user_id=student_user.id)
        )
        profile = result.scalars().first()
        response = await teacher_client.patch(
            f"/admin/students/{profile.id}",
            json={"student_name": "Hacked"},
        )
        assert_forbidden(response)
