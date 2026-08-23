"""IntegrationService — Academic entity sync queries for external consumers (e.g. ns-exam).

Encapsulates all database querying, formatting, and pagination for integration endpoints.
"""

import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.academics.models import AcademicSession, ClassRoom, ClassSubject
from src.domain.curriculum.models import Subject
from src.domain.operations.models import StudentClass
from src.domain.users.models import StudentProfile, TeacherProfile, User


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class IntegrationService:

    @staticmethod
    async def get_boards(
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """ERP is a single-board deployment; expose default board."""
        name = os.getenv("INSTITUTE_NAME", "SCHOOL-ERP Institute")
        board = {
            "erp_id": "BOARD-1",
            "name": name,
            "code": "DEFAULT",
            "status": "ACTIVE",
            "updated_at": _iso(datetime.now(timezone.utc)),
            "is_deleted": False,
        }
        return {
            "items": [board],
            "page": page,
            "page_size": page_size,
            "total": 1,
        }

    @staticmethod
    async def get_schools(
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """ERP is a single-school deployment; expose default school."""
        name = os.getenv("INSTITUTE_NAME", "SCHOOL-ERP Institute")
        school = {
            "erp_id": "SCHOOL-1",
            "board_erp_id": "BOARD-1",
            "name": name,
            "status": "ACTIVE",
            "updated_at": _iso(datetime.now(timezone.utc)),
            "is_deleted": False,
        }
        return {
            "items": [school],
            "page": page,
            "page_size": page_size,
            "total": 1,
        }

    @staticmethod
    async def get_sessions(
        db: AsyncSession,
        updated_since: datetime | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        stmt = select(AcademicSession)
        count_stmt = select(func.count()).select_from(AcademicSession)
        if updated_since:
            stmt = stmt.filter(
                AcademicSession.updated_at >= updated_since,
            )
            count_stmt = count_stmt.filter(
                AcademicSession.updated_at >= updated_since,
            )
        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = list((await db.execute(stmt)).scalars().all())
        return {
            "items": [
                {
                    "erp_id": str(s.id),
                    "school_erp_id": "SCHOOL-1",
                    "name": s.session_name,
                    "start_date": (
                        s.start_date.isoformat()
                        if s.start_date
                        else None
                    ),
                    "end_date": (
                        s.end_date.isoformat()
                        if s.end_date
                        else None
                    ),
                    "is_current": s.is_current,
                    "updated_at": _iso(s.updated_at),
                    "is_deleted": not s.is_active,
                }
                for s in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    @staticmethod
    async def get_classes(
        db: AsyncSession,
        updated_since: datetime | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        stmt = select(ClassRoom)
        count_stmt = select(func.count()).select_from(ClassRoom)
        if updated_since:
            stmt = stmt.filter(
                ClassRoom.updated_at >= updated_since,
            )
            count_stmt = count_stmt.filter(
                ClassRoom.updated_at >= updated_since,
            )
        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = list((await db.execute(stmt)).scalars().all())
        return {
            "items": [
                {
                    "erp_id": str(c.id),
                    "school_erp_id": "SCHOOL-1",
                    "name": c.display_name,
                    "code": c.class_code,
                    "section": c.section,
                    "updated_at": _iso(c.updated_at),
                    "is_deleted": not c.is_active,
                }
                for c in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    @staticmethod
    async def get_subjects(
        db: AsyncSession,
        updated_since: datetime | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        stmt = (
            select(ClassSubject, Subject)
            .join(Subject, ClassSubject.subject_id == Subject.id)
            .order_by(ClassSubject.classroom_id, Subject.id)
        )
        count_stmt = (
            select(func.count())
            .select_from(ClassSubject)
            .join(Subject, ClassSubject.subject_id == Subject.id)
        )
        if updated_since:
            stmt = stmt.filter(
                ClassSubject.updated_at >= updated_since,
            )
            count_stmt = count_stmt.filter(
                ClassSubject.updated_at >= updated_since,
            )
        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = list((await db.execute(stmt)).all())
        return {
            "items": [
                {
                    "erp_id": f"{cs.id}",
                    "board_erp_id": "BOARD-1",
                    "class_erp_id": str(cs.classroom_id),
                    "name": s.subject_name,
                    "code": s.subject_code,
                    "updated_at": _iso(s.updated_at or cs.updated_at),
                    "is_deleted": (
                        not s.is_active or not cs.is_active
                    ),
                }
                for cs, s in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    @staticmethod
    async def get_students(
        db: AsyncSession,
        updated_since: datetime | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        stmt = (
            select(StudentProfile, User, StudentClass)
            .join(User, StudentProfile.user_id == User.id)
            .outerjoin(
                StudentClass,
                StudentClass.student_id == User.id,
            )
        )
        count_stmt = (
            select(func.count())
            .select_from(StudentProfile)
            .join(User, StudentProfile.user_id == User.id)
        )
        if updated_since:
            stmt = stmt.filter(
                StudentProfile.updated_at >= updated_since,
            )
            count_stmt = count_stmt.filter(
                StudentProfile.updated_at >= updated_since,
            )
        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = list((await db.execute(stmt)).all())
        return {
            "items": [
                {
                    "erp_id": str(prof.id),
                    "user_erp_id": str(user.id),
                    "school_erp_id": "SCHOOL-1",
                    "name": prof.student_name,
                    "roll_number": (
                        sc.roll_number if sc else None
                    ),
                    "class_erp_id": (
                        str(sc.classroom_id) if sc else None
                    ),
                    "email": user.email,
                    "updated_at": _iso(prof.updated_at),
                    "is_deleted": (
                        bool(user.is_deleted)
                        or not prof.is_active
                    ),
                }
                for prof, user, sc in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    @staticmethod
    async def get_teachers(
        db: AsyncSession,
        updated_since: datetime | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        stmt = (
            select(TeacherProfile, User)
            .join(User, TeacherProfile.user_id == User.id)
        )
        count_stmt = (
            select(func.count())
            .select_from(TeacherProfile)
            .join(User, TeacherProfile.user_id == User.id)
        )
        if updated_since:
            stmt = stmt.filter(
                TeacherProfile.updated_at >= updated_since,
            )
            count_stmt = count_stmt.filter(
                TeacherProfile.updated_at >= updated_since,
            )
        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = list((await db.execute(stmt)).all())
        return {
            "items": [
                {
                    "erp_id": str(prof.id),
                    "user_erp_id": str(user.id),
                    "school_erp_id": "SCHOOL-1",
                    "name": prof.teacher_name,
                    "employee_code": prof.employee_code,
                    "email": user.email,
                    "updated_at": _iso(prof.updated_at),
                    "is_deleted": (
                        bool(user.is_deleted)
                        or not prof.is_active
                    ),
                }
                for prof, user in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
