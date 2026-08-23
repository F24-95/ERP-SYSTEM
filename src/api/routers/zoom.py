from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.zoom.schemas import (
    ZoomFileCreate,
    ZoomFileResponse,
    ZoomFileUpdate,
    ZoomMeetingIngest,
    ZoomMeetingResponse,
)
from src.domain.zoom.service import ZoomFileService, ZoomMeetingService, ZoomReportService

router = APIRouter(prefix="/zoom", tags=["Zoom"])


# ==================== ZOOM FILES (session bundles) ====================


@router.post("/files", response_model=ZoomFileResponse)
async def create_zoom_file(
    data: ZoomFileCreate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Register a class session's file bundle (video/audio/transcript)."""
    return await ZoomFileService.create(db, data.model_dump())


@router.get("/files", response_model=list[ZoomFileResponse])
async def list_zoom_files(
    classroom_id: int | None = None,
    date: str | None = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List session file bundles, optionally filtered by classroom/date."""
    return await ZoomFileService.list_files(db, classroom_id=classroom_id, date=date)


@router.get("/files/{zoom_file_id}", response_model=ZoomFileResponse)
async def get_zoom_file(
    zoom_file_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a session file bundle by ID."""
    return await ZoomFileService.get(db, zoom_file_id)


@router.put("/files/{zoom_file_id}", response_model=ZoomFileResponse)
async def update_zoom_file(
    zoom_file_id: int,
    data: ZoomFileUpdate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Update a session file bundle."""
    return await ZoomFileService.update(
        db,
        zoom_file_id,
        data.model_dump(exclude_unset=True),
    )


@router.delete("/files/{zoom_file_id}")
async def delete_zoom_file(
    zoom_file_id: int,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a session file bundle."""
    await ZoomFileService.delete(db, zoom_file_id)
    return {"success": True, "message": "Zoom file bundle deactivated"}


# ==================== ZOOM MEETINGS (read + sync landing point) ====================


@router.post("/meetings", response_model=ZoomMeetingResponse)
async def ingest_zoom_meeting(
    data: ZoomMeetingIngest,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Upsert a Zoom meeting record."""
    return await ZoomMeetingService.ingest(db, data.model_dump())


@router.get("/meetings", response_model=list[ZoomMeetingResponse])
async def list_zoom_meetings(
    host_id: str | None = None,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """List Zoom meetings, optionally filtered by host."""
    return await ZoomMeetingService.list_meetings(db, host_id=host_id)


@router.get("/meetings/{uuid}", response_model=ZoomMeetingResponse)
async def get_zoom_meeting(
    uuid: str,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Get a Zoom meeting by its Zoom UUID."""
    return await ZoomMeetingService.get(db, uuid)


# ==================== ZOOM REPORTS ====================


@router.get("/reports/class/{classroom_id}")
async def get_class_zoom_report(
    classroom_id: int,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Class-wise Zoom report: all sessions, participants, interactions."""
    return await ZoomReportService.get_class_zoom_report(
        db, classroom_id, start_date, end_date,
    )


@router.get("/reports/meeting/{meeting_uuid}")
async def get_meeting_detail_report(
    meeting_uuid: str,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Detailed single meeting report with participants and interactions."""
    return await ZoomReportService.get_meeting_detail_report(db, meeting_uuid)


@router.get("/reports/meetings")
async def list_all_meetings(
    classroom_id: int | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """List all meetings with basic stats."""
    return await ZoomReportService.list_all_meetings(
        db, classroom_id, start_date, end_date,
    )
