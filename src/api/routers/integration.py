"""Academic reference endpoints the ns-exam (Exam Engine) platform pulls from.

These implement the ERP side of the Phase 16 inbound sync contract so the
Exam Engine's `SyncService` can populate its academic snapshot tables:

  GET /integration/academic/boards|schools|sessions|classes|subjects|students|teachers

Each returns a paginated payload of the shape the Exam Engine sync job
expects: `erp_id`, business fields, `updated_at`, `is_deleted`.
"""

import os
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.domain.academics.models import AcademicSession, ClassRoom, ClassSubject
from src.domain.curriculum.models import Subject
from src.domain.operations.models import StudentClass
from src.domain.users.models import StudentProfile, TeacherProfile, User

router = APIRouter(prefix="/integration/academic", tags=["Exam Engine Integration"])

PAGE_SIZE = 100


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


@router.get("/boards")
async def list_boards(
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """ERP is a single-board deployment; expose one default board."""
    name = os.getenv("INSTITUTE_NAME", "SCHOOL-ERP Institute")
    board = {
        "erp_id": "BOARD-1",
        "name": name,
        "code": "DEFAULT",
        "status": "ACTIVE",
        "updated_at": _iso(datetime.utcnow()),
        "is_deleted": False,
    }
    return {"items": [board], "page": page, "page_size": page_size, "total": 1}


@router.get("/schools")
async def list_schools(
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """ERP is a single-school deployment; expose one default school."""
    name = os.getenv("INSTITUTE_NAME", "SCHOOL-ERP Institute")
    school = {
        "erp_id": "SCHOOL-1",
        "board_erp_id": "BOARD-1",
        "name": name,
        "status": "ACTIVE",
        "updated_at": _iso(datetime.utcnow()),
        "is_deleted": False,
    }
    return {"items": [school], "page": page, "page_size": page_size, "total": 1}


@router.get("/sessions")
async def list_sessions(
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AcademicSession)
    if updated_since:
        stmt = stmt.filter(AcademicSession.updated_at >= updated_since)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = list((await db.execute(stmt)).scalars().all())
    total = len(rows)
    return {
        "items": [
            {
                "erp_id": str(s.id),
                "school_erp_id": "SCHOOL-1",
                "name": s.session_name,
                "start_date": s.start_date.isoformat() if s.start_date else None,
                "end_date": s.end_date.isoformat() if s.end_date else None,
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


@router.get("/classes")
async def list_classes(
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ClassRoom)
    if updated_since:
        stmt = stmt.filter(ClassRoom.updated_at >= updated_since)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = list((await db.execute(stmt)).scalars().all())
    total = len(rows)
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


@router.get("/subjects")
async def list_subjects(
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Subjects scoped per class (from class_subjects mapping).

    ERP has no chapter/unit/topic hierarchy of its own — those are Exam
    Engine concepts — so only the board→school→class→subject spine is
    exposed here; chapters/units/topics return empty lists.
    """
    stmt = (
        select(ClassSubject, Subject)
        .join(Subject, ClassSubject.subject_id == Subject.id)
        .order_by(ClassSubject.classroom_id, Subject.id)
    )
    if updated_since:
        stmt = stmt.filter(ClassSubject.updated_at >= updated_since)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = list((await db.execute(stmt)).all())
    total = len(rows)
    return {
        "items": [
            {
                "erp_id": f"{cs.id}",
                "board_erp_id": "BOARD-1",
                "class_erp_id": str(cs.classroom_id),
                "name": s.subject_name,
                "code": s.subject_code,
                "updated_at": _iso(s.updated_at or cs.updated_at),
                "is_deleted": not s.is_active or not cs.is_active,
            }
            for cs, s in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/chapters")
async def list_chapters(
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return {"items": [], "page": page, "page_size": page_size, "total": 0}


@router.get("/units")
async def list_units(
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return {"items": [], "page": page, "page_size": page_size, "total": 0}


@router.get("/topics")
async def list_topics(
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return {"items": [], "page": page, "page_size": page_size, "total": 0}


@router.get("/students")
async def list_students(
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(StudentProfile, User, StudentClass)
        .join(User, StudentProfile.user_id == User.id)
        .outerjoin(StudentClass, StudentClass.student_id == User.id)
    )
    if updated_since:
        stmt = stmt.filter(StudentProfile.updated_at >= updated_since)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = list((await db.execute(stmt)).all())
    total = len(rows)
    return {
        "items": [
            {
                "erp_id": str(prof.id),
                "user_erp_id": str(user.id),
                "school_erp_id": "SCHOOL-1",
                "name": prof.student_name,
                "roll_number": sc.roll_number if sc else None,
                "class_erp_id": str(sc.classroom_id) if sc else None,
                "email": user.email,
                "updated_at": _iso(prof.updated_at),
                "is_deleted": bool(user.is_deleted) or not prof.is_active,
            }
            for prof, user, sc in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/teachers")
async def list_teachers(
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(TeacherProfile, User)
        .join(User, TeacherProfile.user_id == User.id)
    )
    if updated_since:
        stmt = stmt.filter(TeacherProfile.updated_at >= updated_since)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = list((await db.execute(stmt)).all())
    total = len(rows)
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
                "is_deleted": bool(user.is_deleted) or not prof.is_active,
            }
            for prof, user in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
