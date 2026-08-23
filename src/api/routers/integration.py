"""Academic reference endpoints the ns-exam (Exam Engine) platform pulls from.

These implement the ERP side of the Phase 16 inbound sync contract so the
Exam Engine's `SyncService` can populate its academic snapshot tables:

  GET /integration/academic/boards|schools|sessions|classes|subjects|students|teachers

Each returns a paginated payload of the shape the Exam Engine sync job
expects: `erp_id`, business fields, `updated_at`, `is_deleted`.

Security Hardening:
- Constant-time API key validation via `secrets.compare_digest`.
- Rate limiting per API key.
- Clear separation of router layer and service layer (`IntegrationService`).
"""

import os
import secrets
import time
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import get_logger
from src.database.connection import get_db
from src.domain.exam_engine.integration_service import IntegrationService

logger = get_logger(__name__)

router = APIRouter(prefix="/integration/academic", tags=["Exam Engine Integration"])

PAGE_SIZE = 100

# Rate limiting: 100 requests per minute per API key
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0
RATE_LIMIT_MAX_REQUESTS = 100


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Validate API key from X-API-Key header using constant-time comparison."""
    expected_key = os.getenv("INTEGRATION_API_KEY", "")
    if not expected_key:
        logger.error("integration.api_key_not_configured")
        raise HTTPException(
            status_code=500,
            detail="Integration API key not configured on server",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
        logger.warning(
            "integration.invalid_api_key",
            ip=request.client.host if request.client else "unknown",
        )
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
        logger.warning(
            "integration.rate_limit_exceeded",
            client_id=client_id[:8] + "...",
        )
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
    _: str = Depends(check_rate_limit),
):
    """ERP is a single-board deployment; expose one default board."""
    logger.info("integration.boards.requested", page=page, page_size=page_size)
    return await IntegrationService.get_boards(page=page, page_size=page_size)


@router.get("/schools")
async def list_schools(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    _: str = Depends(check_rate_limit),
):
    """ERP is a single-school deployment; expose one default school."""
    logger.info("integration.schools.requested", page=page, page_size=page_size)
    return await IntegrationService.get_schools(page=page, page_size=page_size)


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
    return await IntegrationService.get_sessions(
        db,
        updated_since=updated_since,
        page=page,
        page_size=page_size,
    )


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
    return await IntegrationService.get_classes(
        db,
        updated_since=updated_since,
        page=page,
        page_size=page_size,
    )


@router.get("/subjects")
async def list_subjects(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(check_rate_limit),
):
    """Subjects scoped per class (from class_subjects mapping)."""
    logger.info("integration.subjects.requested", page=page, page_size=page_size)
    return await IntegrationService.get_subjects(
        db,
        updated_since=updated_since,
        page=page,
        page_size=page_size,
    )


@router.get("/chapters")
async def list_chapters(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    _: str = Depends(check_rate_limit),
):
    """Chapters endpoint - ERP does not have chapter data yet."""
    logger.info("integration.chapters.requested", page=page, page_size=page_size)
    return {"items": [], "page": page, "page_size": page_size, "total": 0}


@router.get("/units")
async def list_units(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    _: str = Depends(check_rate_limit),
):
    """Units endpoint - ERP does not have unit data yet."""
    logger.info("integration.units.requested", page=page, page_size=page_size)
    return {"items": [], "page": page, "page_size": page_size, "total": 0}


@router.get("/topics")
async def list_topics(
    request: Request,
    updated_since: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=PAGE_SIZE, ge=1, le=500),
    _: str = Depends(check_rate_limit),
):
    """Topics endpoint - ERP does not have topic data yet."""
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
    return await IntegrationService.get_students(
        db,
        updated_since=updated_since,
        page=page,
        page_size=page_size,
    )


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
    return await IntegrationService.get_teachers(
        db,
        updated_since=updated_since,
        page=page,
        page_size=page_size,
    )
