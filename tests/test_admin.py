import pytest
from httpx import AsyncClient

from tests.helpers import (
    assert_bad_request,
    assert_created,
    assert_forbidden,
    assert_no_content,
    assert_not_found,
    assert_ok,
    assert_unauthorized,
)

pytestmark = pytest.mark.asyncio


class TestAdminUserCRUD:
    USER_CREATE_PAYLOAD = {
        "email": "newuser@test.com",
        "phone": "9998887776",
        "role": "student",
        "password": "StrongPass1!",
    }

    async def test_create_user(self, admin_client: AsyncClient):
        response = await admin_client.post("/admin/user", json=self.USER_CREATE_PAYLOAD)
        assert_created(response)
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "student"
        assert data["is_active"] is True
        assert "id" in data

    async def test_create_duplicate_email(self, admin_client: AsyncClient, admin_user):
        response = await admin_client.post("/admin/user", json=self.USER_CREATE_PAYLOAD)
        assert_created(response)
        response2 = await admin_client.post("/admin/user", json=self.USER_CREATE_PAYLOAD)
        assert_bad_request(response2)

    async def test_create_user_unauthorized(self, client: AsyncClient):
        response = await client.post("/admin/user", json=self.USER_CREATE_PAYLOAD)
        assert_unauthorized(response)

    async def test_create_user_forbidden_student(self, student_client: AsyncClient):
        response = await student_client.post("/admin/user", json=self.USER_CREATE_PAYLOAD)
        assert_forbidden(response)

    async def test_create_user_forbidden_teacher(self, teacher_client: AsyncClient):
        response = await teacher_client.post("/admin/user", json=self.USER_CREATE_PAYLOAD)
        assert_forbidden(response)

    async def test_list_users(self, admin_client: AsyncClient, admin_user, teacher_user, student_user):
        response = await admin_client.get("/admin/users")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 3

    async def test_list_users_filter_role(self, admin_client: AsyncClient, admin_user, teacher_user, student_user):
        response = await admin_client.get("/admin/users?role=teacher")
        assert_ok(response)
        data = response.json()
        assert all(u["role"] == "teacher" for u in data)

    async def test_list_users_filter_active(self, admin_client: AsyncClient, admin_user):
        response = await admin_client.get("/admin/users?is_active=true")
        assert_ok(response)
        data = response.json()
        assert all(u["is_active"] is True for u in data)

    async def test_get_user(self, admin_client: AsyncClient, teacher_user):
        response = await admin_client.get(f"/admin/users/{teacher_user.public_id}")
        assert_ok(response)
        data = response.json()
        assert data["email"] == teacher_user.email

    async def test_get_user_not_found(self, admin_client: AsyncClient):
        response = await admin_client.get("/admin/users/nonexistent-uuid")
        assert_not_found(response)

    async def test_update_user(self, admin_client: AsyncClient, student_user):
        response = await admin_client.patch(
            f"/admin/users/{student_user.public_id}",
            json={"phone": "1112223334"},
        )
        assert_ok(response)
        data = response.json()
        assert data["phone"] == "1112223334"

    async def test_update_user_deactivate(self, admin_client: AsyncClient, student_user):
        response = await admin_client.patch(
            f"/admin/users/{student_user.public_id}",
            json={"is_active": False},
        )
        assert_ok(response)
        data = response.json()
        assert data["is_active"] is False

    async def test_deactivate_user(self, admin_client: AsyncClient, teacher_user):
        response = await admin_client.delete(f"/admin/users/{teacher_user.public_id}")
        assert_no_content(response)

    async def test_deactivate_user_twice(self, admin_client: AsyncClient, teacher_user):
        response = await admin_client.delete(f"/admin/users/{teacher_user.public_id}")
        assert_no_content(response)
        response2 = await admin_client.delete(f"/admin/users/{teacher_user.public_id}")
        assert_no_content(response2)


class TestAdminStudentProfiles:
    async def test_list_students(self, admin_client: AsyncClient, student_user):
        response = await admin_client.get("/admin/students")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1
        assert any(s["student_name"] == "Test Student" for s in data)

    async def test_get_student_profile(self, admin_client: AsyncClient, student_user, db_session):
        from sqlalchemy import select
        from src.domain.users.models import StudentProfile
        result = await db_session.execute(
            select(StudentProfile).filter_by(user_id=student_user.id)
        )
        profile = result.scalars().first()
        response = await admin_client.get(f"/admin/students/{profile.id}")
        assert_ok(response)
        assert response.json()["student_name"] == "Test Student"

    async def test_update_student_profile(self, admin_client: AsyncClient, student_user, db_session):
        from sqlalchemy import select
        from src.domain.users.models import StudentProfile
        result = await db_session.execute(
            select(StudentProfile).filter_by(user_id=student_user.id)
        )
        profile = result.scalars().first()
        response = await admin_client.patch(
            f"/admin/students/{profile.id}",
            json={"student_name": "Updated Name", "city": "Mumbai"},
        )
        assert_ok(response)
        assert response.json()["student_name"] == "Updated Name"
        assert response.json()["city"] == "Mumbai"

    async def test_deactivate_student(self, admin_client: AsyncClient, student_user, db_session):
        from sqlalchemy import select
        from src.domain.users.models import StudentProfile
        result = await db_session.execute(
            select(StudentProfile).filter_by(user_id=student_user.id)
        )
        profile = result.scalars().first()
        response = await admin_client.delete(f"/admin/students/{profile.id}")
        assert_no_content(response)

    async def test_student_list_forbidden_parent(self, client: AsyncClient):
        response = await client.get("/admin/students")
        assert_unauthorized(response)


class TestAdminTeacherProfiles:
    async def test_list_teachers(self, admin_client: AsyncClient, teacher_user):
        response = await admin_client.get("/admin/teachers")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1

    async def test_get_teacher_profile(self, admin_client: AsyncClient, teacher_user, db_session):
        from sqlalchemy import select
        from src.domain.users.models import TeacherProfile
        result = await db_session.execute(
            select(TeacherProfile).filter_by(user_id=teacher_user.id)
        )
        profile = result.scalars().first()
        response = await admin_client.get(f"/admin/teachers/{profile.id}")
        assert_ok(response)
        assert response.json()["teacher_name"] == "Test Teacher"

    async def test_update_teacher_profile(self, admin_client: AsyncClient, teacher_user, db_session):
        from sqlalchemy import select
        from src.domain.users.models import TeacherProfile
        result = await db_session.execute(
            select(TeacherProfile).filter_by(user_id=teacher_user.id)
        )
        profile = result.scalars().first()
        response = await admin_client.patch(
            f"/admin/teachers/{profile.id}",
            json={"teacher_name": "Updated Teacher", "department": "Science"},
        )
        assert_ok(response)
        assert response.json()["teacher_name"] == "Updated Teacher"

    async def test_deactivate_teacher(self, admin_client: AsyncClient, teacher_user, db_session):
        from sqlalchemy import select
        from src.domain.users.models import TeacherProfile
        result = await db_session.execute(
            select(TeacherProfile).filter_by(user_id=teacher_user.id)
        )
        profile = result.scalars().first()
        response = await admin_client.delete(f"/admin/teachers/{profile.id}")
        assert_no_content(response)


class TestAdminAdminProfiles:
    async def test_list_admin_profiles(self, admin_client: AsyncClient, admin_user):
        response = await admin_client.get("/admin/admins")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1

    async def test_get_admin_profile(self, admin_client: AsyncClient, admin_user, db_session):
        from sqlalchemy import select
        from src.domain.users.models import AdminProfile
        result = await db_session.execute(
            select(AdminProfile).filter_by(user_id=admin_user.id)
        )
        profile = result.scalars().first()
        response = await admin_client.get(f"/admin/admins/{profile.id}")
        assert_ok(response)
        assert response.json()["admin_name"] == "Test Admin"

    async def test_update_admin_profile(self, admin_client: AsyncClient, admin_user, db_session):
        from sqlalchemy import select
        from src.domain.users.models import AdminProfile
        result = await db_session.execute(
            select(AdminProfile).filter_by(user_id=admin_user.id)
        )
        profile = result.scalars().first()
        response = await admin_client.patch(
            f"/admin/admins/{profile.id}",
            json={"admin_name": "Super Admin", "department": "IT"},
        )
        assert_ok(response)
        assert response.json()["admin_name"] == "Super Admin"

    async def test_deactivate_admin_profile(self, admin_client: AsyncClient, admin_user, db_session):
        from sqlalchemy import select
        from src.domain.users.models import AdminProfile
        result = await db_session.execute(
            select(AdminProfile).filter_by(user_id=admin_user.id)
        )
        profile = result.scalars().first()
        response = await admin_client.delete(f"/admin/admins/{profile.id}")
        assert_no_content(response)


class TestAdminAcademicsSessions:
    SESSION_PAYLOAD = {
        "session_code": "SES-2027",
        "session_name": "2026-2027",
        "start_year": 2026,
        "end_year": 2027,
        "start_date": "2026-04-01",
        "end_date": "2027-03-31",
        "is_current": False,
    }

    async def test_create_session(self, admin_client: AsyncClient):
        response = await admin_client.post("/academics/sessions", json=self.SESSION_PAYLOAD)
        assert_created(response)
        data = response.json()
        assert data["session_code"] == "SES-2027"

    async def test_list_sessions(self, admin_client: AsyncClient, academic_session):
        response = await admin_client.get("/academics/sessions")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1

    async def test_get_session(self, admin_client: AsyncClient, academic_session):
        response = await admin_client.get(f"/academics/sessions/{academic_session.id}")
        assert_ok(response)
        data = response.json()
        assert data["session_code"] == academic_session.session_code

    async def test_update_session(self, admin_client: AsyncClient, academic_session):
        response = await admin_client.put(
            f"/academics/sessions/{academic_session.id}",
            json={"description": "Updated desc"},
        )
        assert_ok(response)
        assert response.json()["description"] == "Updated desc"

    async def test_deactivate_session(self, admin_client: AsyncClient, academic_session):
        response = await admin_client.delete(f"/academics/sessions/{academic_session.id}")
        assert_no_content(response)


class TestAdminAcademicsClassrooms:
    async def test_create_classroom(self, admin_client: AsyncClient, academic_session):
        response = await admin_client.post(
            "/academics/classrooms",
            json={
                "class_code": "CLS-11",
                "class_name": "Class 11",
                "section": "A",
                "display_name": "Class 11 - A",
                "academic_sessions_id": academic_session.id,
            },
        )
        assert_created(response)
        data = response.json()
        assert data["class_code"] == "CLS-11"

    async def test_list_classrooms(self, admin_client: AsyncClient, classroom):
        response = await admin_client.get("/academics/classrooms")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1

    async def test_get_classroom(self, admin_client: AsyncClient, classroom):
        response = await admin_client.get(f"/academics/classrooms/{classroom.id}")
        assert_ok(response)
        assert response.json()["class_name"] == classroom.class_name

    async def test_update_classroom(self, admin_client: AsyncClient, classroom):
        response = await admin_client.put(
            f"/academics/classrooms/{classroom.id}",
            json={"section": "B"},
        )
        assert_ok(response)
        assert response.json()["section"] == "B"

    async def test_deactivate_classroom(self, admin_client: AsyncClient, classroom):
        response = await admin_client.delete(f"/academics/classrooms/{classroom.id}")
        assert_no_content(response)


class TestAdminAcademicsSubjects:
    SUBJECT_PAYLOAD = {
        "subject_code": "PHY",
        "subject_name": "Physics",
        "display_order": 2,
    }

    async def test_create_subject(self, admin_client: AsyncClient):
        response = await admin_client.post("/academics/subjects", json=self.SUBJECT_PAYLOAD)
        assert_created(response)
        assert response.json()["subject_code"] == "PHY"

    async def test_list_subjects(self, admin_client: AsyncClient, subject):
        response = await admin_client.get("/academics/subjects")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1

    async def test_get_subject(self, admin_client: AsyncClient, subject):
        response = await admin_client.get(f"/academics/subjects/{subject.id}")
        assert_ok(response)
        assert response.json()["subject_code"] == subject.subject_code

    async def test_update_subject(self, admin_client: AsyncClient, subject):
        response = await admin_client.put(
            f"/academics/subjects/{subject.id}",
            json={"subject_name": "Advanced Physics"},
        )
        assert_ok(response)
        assert response.json()["subject_name"] == "Advanced Physics"

    async def test_deactivate_subject(self, admin_client: AsyncClient, subject):
        response = await admin_client.delete(f"/academics/subjects/{subject.id}")
        assert_no_content(response)

    async def test_create_duplicate_subject_code(self, admin_client: AsyncClient, subject):
        response = await admin_client.post(
            "/academics/subjects",
            json={"subject_code": "MATH", "subject_name": "Math Again", "display_order": 3},
        )
        assert_bad_request(response)


class TestAdminAcademicsClassSubjects:
    async def test_create_class_subject(
        self, admin_client: AsyncClient, academic_session, classroom, subject
    ):
        response = await admin_client.post(
            "/academics/class-subjects",
            json={
                "academic_sessions_id": academic_session.id,
                "classroom_id": classroom.id,
                "subject_id": subject.id,
            },
        )
        assert_created(response)
        data = response.json()
        assert data["classroom_id"] == classroom.id
        assert data["subject_id"] == subject.id

    async def test_list_class_subjects(
        self, admin_client: AsyncClient, db_session, academic_session, classroom, subject
    ):
        from src.domain.academics.models import ClassSubject
        db_session.add(ClassSubject(
            academic_sessions_id=academic_session.id,
            classroom_id=classroom.id,
            subject_id=subject.id,
        ))
        await db_session.flush()

        response = await admin_client.get("/academics/class-subjects")
        assert_ok(response)
        data = response.json()
        assert len(data) >= 1

    async def test_get_class_subject(
        self, admin_client: AsyncClient, db_session, academic_session, classroom, subject
    ):
        from src.domain.academics.models import ClassSubject
        cs = ClassSubject(
            academic_sessions_id=academic_session.id,
            classroom_id=classroom.id,
            subject_id=subject.id,
        )
        db_session.add(cs)
        await db_session.flush()

        response = await admin_client.get(f"/academics/class-subjects/{cs.id}")
        assert_ok(response)
        assert response.json()["subject_id"] == subject.id


class TestAdminOperationsTeacherAssignments:
    async def test_assign_teacher_to_subject(
        self, admin_client: AsyncClient, teacher_user, academic_session, classroom, subject, db_session
    ):
        from src.domain.academics.models import ClassSubject
        cs = ClassSubject(
            academic_sessions_id=academic_session.id,
            classroom_id=classroom.id,
            subject_id=subject.id,
        )
        db_session.add(cs)
        await db_session.flush()

        response = await admin_client.post(
            "/operations/assign-teacher",
            json={
                "teacher_id": teacher_user.id,
                "class_subject_id": cs.id,
                "classroom_id": classroom.id,
                "subject_id": subject.id,
                "academic_sessions_id": academic_session.id,
                "is_class_teacher": False,
            },
        )
        assert_created(response)
        data = response.json()
        assert data["teacher_id"] == teacher_user.id

    async def test_list_teacher_assignments(self, admin_client: AsyncClient):
        response = await admin_client.get("/operations/teacher-assignments")
        assert_ok(response)

    async def test_unassign_teacher(
        self, admin_client: AsyncClient, teacher_user, academic_session, classroom, subject, db_session
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

        response = await admin_client.delete(f"/operations/teacher-assignments/{ts.id}")
        assert_no_content(response)


class TestAdminOperationsStudentEnrollments:
    async def test_enroll_student(
        self, admin_client: AsyncClient, student_user, academic_session, classroom
    ):
        response = await admin_client.post(
            "/operations/enroll-student",
            json={
                "student_id": student_user.id,
                "classroom_id": classroom.id,
                "academic_sessions_id": academic_session.id,
                "roll_number": 1,
                "admission_date": "2026-04-01",
            },
        )
        assert_created(response)
        data = response.json()
        assert data["student_id"] == student_user.id
        assert data["roll_number"] == 1

    async def test_enroll_duplicate_student(
        self, admin_client: AsyncClient, student_user, academic_session, classroom, db_session
    ):
        from src.domain.operations.models import StudentClass
        db_session.add(StudentClass(
            student_id=student_user.id,
            classroom_id=classroom.id,
            academic_sessions_id=academic_session.id,
            roll_number=1,
            admission_date=__import__("datetime").datetime.utcnow().date(),
        ))
        await db_session.flush()

        response = await admin_client.post(
            "/operations/enroll-student",
            json={
                "student_id": student_user.id,
                "classroom_id": classroom.id,
                "academic_sessions_id": academic_session.id,
                "roll_number": 2,
                "admission_date": "2026-04-01",
            },
        )
        assert_bad_request(response)

    async def test_list_enrollments(self, admin_client: AsyncClient):
        response = await admin_client.get("/operations/student-enrollments")
        assert_ok(response)

    async def test_unenroll_student(
        self, admin_client: AsyncClient, student_user, academic_session, classroom, db_session
    ):
        from src.domain.operations.models import StudentClass
        sc = StudentClass(
            student_id=student_user.id,
            classroom_id=classroom.id,
            academic_sessions_id=academic_session.id,
            roll_number=1,
            admission_date=__import__("datetime").datetime.utcnow().date(),
        )
        db_session.add(sc)
        await db_session.flush()

        response = await admin_client.delete(f"/operations/student-enrollments/{sc.id}")
        assert_no_content(response)


class TestAdminUsersMe:
    async def test_get_me(self, admin_client: AsyncClient, admin_user):
        response = await admin_client.get("/users/me")
        assert_ok(response)
        assert response.json()["email"] == admin_user.email

    async def test_update_me(self, admin_client: AsyncClient, admin_user):
        response = await admin_client.patch("/users/me", json={"phone": "5556667778"})
        assert_ok(response)
        assert response.json()["phone"] == "5556667778"

    async def test_get_user_by_public_id(self, admin_client: AsyncClient, teacher_user):
        response = await admin_client.get(f"/users/{teacher_user.public_id}")
        assert_ok(response)
        assert response.json()["email"] == teacher_user.email


class TestAdminRoleIsolation:
    async def test_student_cannot_create_user(self, student_client: AsyncClient):
        response = await student_client.post(
            "/admin/user",
            json={"email": "x@x.com", "phone": "1111111111", "role": "student", "password": "Pass1234!"},
        )
        assert_forbidden(response)

    async def test_teacher_cannot_deactivate_user(self, teacher_client: AsyncClient, student_user):
        response = await teacher_client.delete(f"/admin/users/{student_user.public_id}")
        assert_forbidden(response)

    async def test_unauthenticated_cannot_access_admin(self, client: AsyncClient):
        response = await client.get("/admin/users")
        assert_unauthorized(response)

    async def test_student_cannot_delete_admin_profile(self, student_client: AsyncClient, admin_user, db_session):
        from sqlalchemy import select
        from src.domain.users.models import AdminProfile
        result = await db_session.execute(
            select(AdminProfile).filter_by(user_id=admin_user.id)
        )
        profile = result.scalars().first()
        response = await student_client.delete(f"/admin/admins/{profile.id}")
        assert_forbidden(response)

    async def test_teacher_can_list_students(self, teacher_client: AsyncClient, student_user):
        response = await teacher_client.get("/admin/students")
        assert_ok(response)
