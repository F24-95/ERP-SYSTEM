import os
from datetime import date

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import NoticeAudience, NoticeType, UserRole
from src.core.exceptions import ResourceNotFoundException
from src.database.connection import get_db
from src.domain.notices.schemas import NoticeResponse
from src.domain.notices.service import UPLOAD_DIR, NoticeService
from src.domain.users.models import User

router = APIRouter(prefix="/notices", tags=["Notice Board"])


def _disk_path(stored_name: str):
    return UPLOAD_DIR / stored_name


@router.post("/", response_model=NoticeResponse)
async def create_notice(
    title: str = Form(...),
    description: str = Form(...),
    notice_type: NoticeType = Form(NoticeType.GENERAL),
    audience: NoticeAudience = Form(NoticeAudience.ALL),
    publish_date: date = Form(...),
    expiry_date: date | None = Form(None),
    is_pinned: bool = Form(False),
    academic_sessions_id: int = Form(...),
    classroom_id: int | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new notice, optionally with an uploaded attachment."""
    return await NoticeService.create_notice(
        db,
        title=title,
        description=description,
        notice_type=notice_type,
        audience=audience,
        publish_date=publish_date,
        expiry_date=expiry_date,
        is_pinned=is_pinned,
        academic_sessions_id=academic_sessions_id,
        classroom_id=classroom_id,
        file=file,
        current_user=current_user,
    )


@router.get("/", response_model=list[NoticeResponse])
async def get_notices(
    notice_type: NoticeType | None = None,
    audience: NoticeAudience | None = None,
    is_pinned: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notices with filters. Audience is restricted by role automatically."""
    return await NoticeService.get_notices(
        db,
        current_user,
        notice_type=notice_type,
        is_pinned=is_pinned,
    )


@router.get("/{notice_id}", response_model=NoticeResponse)
async def get_notice(
    notice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notice by ID."""
    return await NoticeService.get_notice(db, notice_id, current_user)


@router.put("/{notice_id}", response_model=NoticeResponse)
async def update_notice(
    notice_id: int,
    title: str | None = Form(None),
    description: str | None = Form(None),
    notice_type: NoticeType | None = Form(None),
    audience: NoticeAudience | None = Form(None),
    publish_date: date | None = Form(None),
    expiry_date: date | None = Form(None),
    is_pinned: bool | None = Form(None),
    classroom_id: int | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Update notice."""
    return await NoticeService.update_notice(
        db,
        notice_id,
        title=title,
        description=description,
        notice_type=notice_type,
        audience=audience,
        publish_date=publish_date,
        expiry_date=expiry_date,
        is_pinned=is_pinned,
        classroom_id=classroom_id,
        file=file,
        current_user=current_user,
    )


@router.delete("/{notice_id}")
async def delete_notice(
    notice_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete notice + remove attachment file from disk (best-effort)."""
    await NoticeService.delete_notice(db, notice_id, current_user)
    return {"success": True, "message": "Notice deleted successfully"}


@router.post("/{notice_id}/pin")
async def pin_notice(
    notice_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Pin a notice."""
    await NoticeService.pin_notice(db, notice_id)
    return {"success": True, "message": "Notice pinned successfully"}


@router.post("/{notice_id}/unpin")
async def unpin_notice(
    notice_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Unpin a notice."""
    await NoticeService.unpin_notice(db, notice_id)
    return {"success": True, "message": "Notice unpinned successfully"}


@router.get("/{notice_id}/view")
async def view_notice_file(
    notice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notice = await NoticeService.get_notice_file(db, notice_id, current_user)
    stored_name = os.path.basename(str(notice.attachment_path))
    disk_path = _disk_path(stored_name)
    if not disk_path.exists():
        raise ResourceNotFoundException("File missing on server")

    return FileResponse(
        disk_path,
        media_type=notice.mime_type,
        filename=notice.attachment_name or stored_name,
        headers={"Content-Disposition": f"inline; filename={notice.attachment_name or stored_name}"},
    )


@router.get("/{notice_id}/download")
async def download_notice_file(
    notice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notice = await NoticeService.get_notice_file(db, notice_id, current_user)
    stored_name = os.path.basename(str(notice.attachment_path))
    disk_path = _disk_path(stored_name)
    if not disk_path.exists():
        raise ResourceNotFoundException("File missing on server")

    filename = notice.attachment_name or stored_name
    return FileResponse(
        disk_path,
        media_type=notice.mime_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
