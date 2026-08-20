"""Academic reference endpoints the ns-exam (Exam Engine) platform pulls from.

These implement the ERP side of the Phase 16 inbound sync contract so the
Exam Engine's `SyncService` can populate its academic snapshot tables:

  GET /integration/academic/boards|schools|sessions|classes|subjects|students|teachers

Each returns a paginated payload of the shape the Exam Engine sync job
expects: `erp_id`, business fields, `updated_at`, `is_deleted`.

Phase 1 Security Hardening: All endpoints now require API key authentication
via X-API-Key header to prevent unauthorized access to sensitive student/teacher data.
"""

import os
import time
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import get_logger
from src.database.connection import get_db
from src.domain.academics.models import AcademicSession, ClassRoom, ClassSubject
from src.domain.curriculum.models import Subject
from src.domain.operations.models import StudentClass
from src.domain.users.models import StudentProfile, TeacherProfile, User

logger = get_logger(__name__)

router = APIRouter(prefix="/integration/academic", tags=["Exam Engine Integration"])

PAGE_SIZE = 100

# Rate limiting: 100 requests per minute per API key
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0
RATE_LIMIT_MAX_REQUESTS = 100


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Validate API key from X-API-Key header.

    Phase 1 Security: Integration endpoints MUST have authentication.
    The API key must match the INTEGRATION_API_KEY env var.
    """
    expected_key = os.getenv("INTEGRATION_API_KEY", "")
    if not expected_key:
        logger.error("integration.api_key_not_configured")
        raise HTTPException(
            status_code=500,
            detail="Integration API key not configured on server",
        )
    if not x_api_key or x_api_key != expected_key:
        logger.warning("integration.invalid_api_key", ip=request.client.host if request.client else "unknown")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )
    return x_api_key


async def check_rate_limit(
    request: Request,
    x_api_key: str = Depends(require_api_key),
) -> str:
    """Rate limiting: max 100 requests per minute per API key."""
    client_id = x_api_key
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old entries
    _rate_limit_store[client_id] = [
        t for t in _rate_limit_store[client_id] if t > window_start
    ]

    if len(_rate_limit_store[client_id]) >= RATE_LIMIT_MAX_REQUESTS:
        logger.warning("integration.rate_limit_exceeded", client_id=client_id[:8] + "...")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 100 requests per minute.",
        )

    _rate_limit_store[client_id].append(now)
    return x_api_key


@router.get("/boards")
async def list_boards(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    """ERP is a single-board deployment; expose one default board."""
    logger.info("integration.boards.requested", page=page, page_size=page_size)
    name = os.getenv("INSTITUTE_NAME", "SCHOOL-ERP Institute")
    board = {
        "erp_id": "BOARD-1",
        "name": name,
        "code": "DEFAULT",
        "status": "ACTIVE",
        "updated_at": _iso(datetime.now(timezone.utc)),
        "is_deleted": False,
    }
    return {"items": [board], "page": page, "page_size": page_size, "total": 1}


@router.get("/schools")
async def list_schools(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    """ERP is a single-school deployment; expose one default school."""
    logger.info("integration.schools.requested", page=page, page_size=page_size)
    name = os.getenv("INSTITUTE_NAME", "SCHOOL-ERP Institute")
    school = {
        "erp_id": "SCHOOL-1",
        "board_erp_id": "BOARD-1",
        "name": name,
        "status": "ACTIVE",
        "updated_at": _iso(datetime.now(timezone.utc)),
        "is_deleted": False,
    }
    return {"items": [school], "page": page, "page_size": page_size, "total": 1}


@router.get("/sessions")
async def list_sessions(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    logger.info("integration.sessions.requested", page=page, page_size=page_size)
    stmt = select(AcademicSession)
    count_stmt = select(func.count()).select_from(AcademicSession)
    if updated_since:
        stmt = stmt.filter(AcademicSession.updated_at >= updated_since)
        count_stmt = count_stmt.filter(AcademicSession.updated_at >= updated_since)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = list((await db.execute(stmt)).scalars().all())
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
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    logger.info("integration.classes.requested", page=page, page_size=page_size)
    stmt = select(ClassRoom)
    count_stmt = select(func.count()).select_from(ClassRoom)
    if updated_since:
        stmt = stmt.filter(ClassRoom.updated_at >= updated_since)
        count_stmt = count_stmt.filter(ClassRoom.updated_at >= updated_since)
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


@router.get("/subjects")
async def list_subjects(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    """Subjects scoped per class (from class_subjects mapping).

    ERP has no chapter/unit/topic hierarchy of its own — those are Exam
    Engine concepts — so only the board→school→class→subject spine is
    exposed here; chapters/units/topics return empty lists.
    """
    logger.info("integration.subjects.requested", page=page, page_size=page_size)
    stmt = (
        select(ClassSubject, Subject)
        .join(Subject, ClassSubject.subject_id == Subject.id)
        .order_by(ClassSubject.classroom_id, Subject.id)
    )
    count_stmt = select(func.count()).select_from(ClassSubject).join(
        Subject, ClassSubject.subject_id == Subject.id
    )
    if updated_since:
        stmt = stmt.filter(ClassSubject.updated_at >= updated_since)
        count_stmt = count_stmt.filter(ClassSubject.updated_at >= updated_since)
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
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    """Chapters endpoint - ERP does not have chapter data yet.

    Phase 2 will implement proper chapter queries if curriculum data is added.
    """
    logger.info("integration.chapters.requested", page=page, page_size=page_size)
    return {"items": [], "page": page, "page_size": page_size, "total": 0}


@router.get("/units")
async def list_units(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    """Units endpoint - ERP does not have unit data yet.

    Phase 2 will implement proper unit queries if curriculum data is added.
    """
    logger.info("integration.units.requested", page=page, page_size=page_size)
    return {"items": [], "page": page, "page_size": page_size, "total": 0}


@router.get("/topics")
async def list_topics(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    """Topics endpoint - ERP does not have topic data yet.

    Phase 2 will implement proper topic queries if curriculum data is added.
    """
    logger.info("integration.topics.requested", page=page, page_size=page_size)
    return {"items": [], "page": page, "page_size": page_size, "total": 0}


@router.get("/students")
async def list_students(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    logger.info("integration.students.requested", page=page, page_size=page_size)
    stmt = (
        select(StudentProfile, User, StudentClass)
        .join(User, StudentProfile.user_id == User.id)
        .outerjoin(StudentClass, StudentClass.student_id == User.id)
    )
    count_stmt = (
        select(func.count())
        .select_from(StudentProfile)
        .join(User, StudentProfile.user_id == User.id)
    )
    if updated_since:
        stmt = stmt.filter(StudentProfile.updated_at >= updated_since)
        count_stmt = count_stmt.filter(StudentProfile.updated_at >= updated_since)
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
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    logger.info("integration.teachers.requested", page=page, page_size=page_size)
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
        stmt = stmt.filter(TeacherProfile.updated_at >= updated_since)
        count_stmt = count_stmt.filter(TeacherProfile.updated_at >= updated_since)
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
                "is_deleted": bool(user.is_deleted) or not prof.is_active,
            }
            for prof, user in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
