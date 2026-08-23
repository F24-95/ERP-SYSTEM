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
    get_auth_headers,
)

pytestmark = pytest.mark.asyncio

DEFAULT_PASSWORD = "TestPass123!"


async def _create_class_and_subject(client, admin_user):
    from src.core.security import create_access_token

    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

    from datetime import date

    s_resp = await client.post(
        "/academics/sessions",
        headers=headers,
        json={
            "session_code": "SES-ASSIGN-2026",
            "session_name": "2025-2026",
            "start_year": 2025,
            "end_year": 2026,
            "start_date": str(date(2025, 4, 1)),
            "end_date": str(date(2026, 3, 31)),
            "is_current": True,
        },
    )
    session_id = s_resp.json()["id"]

    c_resp = await client.post(
        "/academics/classrooms",
        headers=headers,
        json={
            "class_code": "CLS-8",
            "class_name": "Class 8",
            "section": "A",
            "display_name": "Class 8 - A",
            "academic_sessions_id": session_id,
        },
    )
    classroom_id = c_resp.json()["id"]

    sub_resp = await client.post(
        "/academics/subjects",
        headers=headers,
        json={
            "subject_code": "SCI",
            "subject_name": "Science",
            "display_order": 1,
        },
    )
    subject_id = sub_resp.json()["id"]

    cs_resp = await client.post(
        "/academics/class-subjects",
        headers=headers,
        json={
            "academic_sessions_id": session_id,
            "classroom_id": classroom_id,
            "subject_id": subject_id,
        },
    )
    class_subject_id = cs_resp.json()["id"]

    return {
        "session_id": session_id,
        "classroom_id": classroom_id,
        "subject_id": subject_id,
        "class_subject_id": class_subject_id,
    }


async def _create_teacher(client, admin_user):
    from src.core.security import create_access_token

    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

    resp = await client.post(
        "/admin/user",
        headers=headers,
        json={
            "email": f"teacher_assign_{id}@test.com",
            "phone": "9876543210",
            "role": "teacher",
            "password": DEFAULT_PASSWORD,
        },
    )
    return resp.json()["id"]


async def _create_student(client, admin_user):
    from src.core.security import create_access_token

    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

    resp = await client.post(
        "/admin/user",
        headers=headers,
        json={
            "email": f"student_assign_{id}@test.com",
            "phone": "9876543220",
            "role": "student",
            "password": DEFAULT_PASSWORD,
        },
    )
    return resp.json()["id"]


async def _assign_teacher(client, admin_user, teacher_id, class_subject_id, classroom_id, subject_id, session_id):
    from src.core.security import create_access_token

    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

    resp = await client.post(
        "/operations/assign-teacher",
        headers=headers,
        json={
            "teacher_id": teacher_id,
            "class_subject_id": class_subject_id,
            "classroom_id": classroom_id,
            "subject_id": subject_id,
            "academic_sessions_id": session_id,
            "is_class_teacher": False,
        },
    )
    return resp.json()


async def _enroll_student(client, admin_user, student_id, classroom_id, session_id):
    from src.core.security import create_access_token

    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

    resp = await client.post(
        "/operations/enroll-student",
        headers=headers,
        json={
            "student_id": student_id,
            "classroom_id": classroom_id,
            "academic_sessions_id": session_id,
            "roll_number": 1,
            "admission_date": "2026-04-01",
        },
    )
    return resp.json()


class TestAssignmentCRUD:
    async def test_create_assignment(
        self, client, admin_user
    ):
        from src.core.security import create_access_token

        headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

        await client.post("/academics/sessions", headers=headers, json={"session_code": "SES-A1", "session_name": "25-26", "start_year": 2025, "end_year": 2026, "start_date": "2025-04-01", "end_date": "2026-03-31", "is_current": True})
        s = await client.get("/academics/sessions", headers=headers)
        sid = s.json()[0]["id"]

        c = await client.post("/academics/classrooms", headers=headers, json={"class_code": "C-A1", "class_name": "5", "section": "A", "display_name": "5-A", "academic_sessions_id": sid})
        cid = c.json()["id"]

        sub = await client.post("/academics/subjects", headers=headers, json={"subject_code": "S-A1", "subject_name": "Math", "display_order": 1})
        sub_id = sub.json()["id"]

        cs = await client.post("/academics/class-subjects", headers=headers, json={"academic_sessions_id": sid, "classroom_id": cid, "subject_id": sub_id})
        cs_id = cs.json()["id"]

        t = await client.post("/admin/user", headers=headers, json={"email": "t_a1@test.com", "phone": "9800000001", "role": "teacher", "password": DEFAULT_PASSWORD})
        tid = t.json()["id"]

        await client.post("/operations/assign-teacher", headers=headers, json={"teacher_id": tid, "class_subject_id": cs_id, "classroom_id": cid, "subject_id": sub_id, "academic_sessions_id": sid, "is_class_teacher": False})

        resp = await client.post(
            "/assignments/",
            headers=headers,
            json={
                "title": "Homework 1",
                "description": "Complete exercises 1-10",
                "subject_id": sub_id,
                "classroom_id": cid,
                "assigned_by": tid,
                "assigned_date": "2026-08-01",
                "due_date": "2026-08-05",
                "max_marks": 100,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Homework 1"
        assert data["max_marks"] == 100

    async def test_create_assignment_teacher(self, client, admin_user):
        from src.core.security import create_access_token

        headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

        await client.post("/academics/sessions", headers=headers, json={"session_code": "SES-A2", "session_name": "25-26", "start_year": 2025, "end_year": 2026, "start_date": "2025-04-01", "end_date": "2026-03-31", "is_current": True})
        s = await client.get("/academics/sessions", headers=headers)
        sid = s.json()[0]["id"]

        c = await client.post("/academics/classrooms", headers=headers, json={"class_code": "C-A2", "class_name": "5", "section": "B", "display_name": "5-B", "academic_sessions_id": sid})
        cid = c.json()["id"]

        sub = await client.post("/academics/subjects", headers=headers, json={"subject_code": "S-A2", "subject_name": "Math", "display_order": 1})
        sub_id = sub.json()["id"]

        cs = await client.post("/academics/class-subjects", headers=headers, json={"academic_sessions_id": sid, "classroom_id": cid, "subject_id": sub_id})
        cs_id = cs.json()["id"]

        t = await client.post("/admin/user", headers=headers, json={"email": "t_a2@test.com", "phone": "9800000002", "role": "teacher", "password": DEFAULT_PASSWORD})
        tid = t.json()["id"]

        await client.post("/operations/assign-teacher", headers=headers, json={"teacher_id": tid, "class_subject_id": cs_id, "classroom_id": cid, "subject_id": sub_id, "academic_sessions_id": sid, "is_class_teacher": False})

        teacher_headers = await get_auth_headers(client, "t_a2@test.com", DEFAULT_PASSWORD)

        resp = await client.post(
            "/assignments/",
            headers=teacher_headers,
            json={
                "title": "Assignment 1",
                "description": "Complete exercises 1-10",
                "subject_id": sub_id,
                "classroom_id": cid,
                "assigned_by": tid,
                "assigned_date": "2026-08-01",
                "due_date": "2026-08-05",
                "max_marks": 100,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Assignment 1"

    async def test_create_assignment_student_forbidden(self, client, admin_user):
        from src.core.security import create_access_token

        headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

        t = await client.post("/admin/user", headers=headers, json={"email": "t_a3@test.com", "phone": "9800000003", "role": "teacher", "password": DEFAULT_PASSWORD})
        tid = t.json()["id"]

        await client.post("/academics/sessions", headers=headers, json={"session_code": "SES-A3", "session_name": "25-26", "start_year": 2025, "end_year": 2026, "start_date": "2025-04-01", "end_date": "2026-03-31", "is_current": True})
        s = await client.get("/academics/sessions", headers=headers)
        sid = s.json()[0]["id"]

        c = await client.post("/academics/classrooms", headers=headers, json={"class_code": "C-A3", "class_name": "6", "section": "A", "display_name": "6-A", "academic_sessions_id": sid})
        cid = c.json()["id"]

        sub = await client.post("/academics/subjects", headers=headers, json={"subject_code": "S-A3", "subject_name": "English", "display_order": 2})
        sub_id = sub.json()["id"]

        student_h = await get_auth_headers(client, "student@test.com", DEFAULT_PASSWORD)
        student_id_resp = await client.get("/users/me", headers=student_h)
        student_id = student_id_resp.json()["id"]

        resp = await client.post(
            "/assignments/",
            headers=student_h,
            json={
                "title": "Assignment 2",
                "description": "Read chapter 1",
                "subject_id": sub_id,
                "classroom_id": cid,
                "assigned_by": tid,
                "assigned_date": "2026-08-01",
                "due_date": "2026-08-05",
                "max_marks": 50,
            },
        )
        assert resp.status_code == 403

    async def test_list_assignments(self, client, admin_user):
        from src.core.security import create_access_token

        headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

        await client.post("/academics/sessions", headers=headers, json={"session_code": "SES-A4", "session_name": "25-26", "start_year": 2025, "end_year": 2026, "start_date": "2025-04-01", "end_date": "2026-03-31", "is_current": True})
        s = await client.get("/academics/sessions", headers=headers)
        sid = s.json()[0]["id"]

        c = await client.post("/academics/classrooms", headers=headers, json={"class_code": "C-A4", "class_name": "7", "section": "A", "display_name": "7-A", "academic_sessions_id": sid})
        cid = c.json()["id"]

        sub = await client.post("/academics/subjects", headers=headers, json={"subject_code": "S-A4", "subject_name": "Science", "display_order": 3})
        sub_id = sub.json()["id"]

        cs = await client.post("/academics/class-subjects", headers=headers, json={"academic_sessions_id": sid, "classroom_id": cid, "subject_id": sub_id})
        cs_id = cs.json()["id"]

        t = await client.post("/admin/user", headers=headers, json={"email": "t_a4@test.com", "phone": "9800000004", "role": "teacher", "password": DEFAULT_PASSWORD})
        tid = t.json()["id"]

        await client.post("/operations/assign-teacher", headers=headers, json={"teacher_id": tid, "class_subject_id": cs_id, "classroom_id": cid, "subject_id": sub_id, "academic_sessions_id": sid, "is_class_teacher": False})

        await client.post(
            "/assignments/",
            headers=headers,
            json={
                "title": "Assignment 3",
                "description": "Science project",
                "subject_id": sub_id,
                "classroom_id": cid,
                "assigned_by": tid,
                "assigned_date": "2026-08-01",
                "due_date": "2026-08-10",
                "max_marks": 50,
            },
        )

        resp = await client.get("/assignments/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_assignment(self, client, admin_user):
        from src.core.security import create_access_token

        headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

        await client.post("/academics/sessions", headers=headers, json={"session_code": "SES-A5", "session_name": "25-26", "start_year": 2025, "end_year": 2026, "start_date": "2025-04-01", "end_date": "2026-03-31", "is_current": True})
        s = await client.get("/academics/sessions", headers=headers)
        sid = s.json()[0]["id"]

        c = await client.post("/academics/classrooms", headers=headers, json={"class_code": "C-A5", "class_name": "7", "section": "B", "display_name": "7-B", "academic_sessions_id": sid})
        cid = c.json()["id"]

        sub = await client.post("/academics/subjects", headers=headers, json={"subject_code": "S-A5", "subject_name": "English", "display_order": 4})
        sub_id = sub.json()["id"]

        cs = await client.post("/academics/class-subjects", headers=headers, json={"academic_sessions_id": sid, "classroom_id": cid, "subject_id": sub_id})
        cs_id = cs.json()["id"]

        t = await client.post("/admin/user", headers=headers, json={"email": "t_a5@test.com", "phone": "9800000005", "role": "teacher", "password": DEFAULT_PASSWORD})
        tid = t.json()["id"]

        await client.post("/operations/assign-teacher", headers=headers, json={"teacher_id": tid, "class_subject_id": cs_id, "classroom_id": cid, "subject_id": sub_id, "academic_sessions_id": sid, "is_class_teacher": False})

        create_resp = await client.post(
            "/assignments/",
            headers=headers,
            json={
                "title": "Assignment 4",
                "description": "English essay",
                "subject_id": sub_id,
                "classroom_id": cid,
                "assigned_by": tid,
                "assigned_date": "2026-08-01",
                "due_date": "2026-08-07",
                "max_marks": 100,
            },
        )
        assignment_id = create_resp.json()["id"]

        resp = await client.get(f"/assignments/{assignment_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Assignment 4"

    async def test_delete_assignment(self, client, admin_user):
        from src.core.security import create_access_token

        headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_user.id), 'role': admin_user.role.value})}"}

        await client.post("/academics/sessions", headers=headers, json={"session_code": "SES-A6", "session_name": "25-26", "start_year": 2025, "end_year": 2026, "start_date": "2025-04-01", "end_date": "2026-03-31", "is_current": True})
        s = await client.get("/academics/sessions", headers=headers)
        sid = s.json()[0]["id"]

        c = await client.post("/academics/classrooms", headers=headers, json={"class_code": "C-A6", "class_name": "8", "section": "A", "display_name": "8-A", "academic_sessions_id": sid})
        cid = c.json()["id"]

        sub = await client.post("/academics/subjects", headers=headers, json={"subject_code": "S-A6", "subject_name": "Math", "display_order": 5})
        sub_id = sub.json()["id"]

        cs = await client.post("/academics/class-subjects", headers=headers, json={"academic_sessions_id": sid, "classroom_id": cid, "subject_id": sub_id})
        cs_id = cs.json()["id"]

        t = await client.post("/admin/user", headers=headers, json={"email": "t_a6@test.com", "phone": "9800000006", "role": "teacher", "password": DEFAULT_PASSWORD})
        tid = t.json()["id"]

        await client.post("/operations/assign-teacher", headers=headers, json={"teacher_id": tid, "class_subject_id": cs_id, "classroom_id": cid, "subject_id": sub_id, "academic_sessions_id": sid, "is_class_teacher": False})

        create_resp = await client.post(
            "/assignments/",
            headers=headers,
            json={
                "title": "Assignment 5",
                "description": "Math problems",
                "subject_id": sub_id,
                "classroom_id": cid,
                "assigned_by": tid,
                "assigned_date": "2026-08-01",
                "due_date": "2026-08-03",
                "max_marks": 25,
            },
        )
        assignment_id = create_resp.json()["id"]

        resp = await client.delete(f"/assignments/{assignment_id}", headers=headers)
        assert resp.status_code == 204
