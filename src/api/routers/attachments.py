from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.database.connection import get_db
from src.domain.attachments.schemas import (
    AttachmentListResponse,
    AttachmentUploadRequest,
    AttachmentUploadResponse,
)
from src.domain.attachments.service import AttachmentService
from src.domain.users.models import User

router = APIRouter(prefix="/attachments", tags=["Attachments"])


@router.post("/upload", response_model=AttachmentUploadResponse)
async def upload_attachment(
    payload: AttachmentUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = await AttachmentService.upload(
        db,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        file_name=payload.file_name,
        mime_type=payload.mime_type,
        file_data_b64=payload.file_data,
        current_user=current_user,
    )
    return {
        "success": True,
        "attachment_id": attachment.id,
        "attachment_code": attachment.attachment_code,
        "file_name": attachment.file_name,
        "file_size": attachment.file_size,
    }


@router.get("/{attachment_id}")
async def download_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = await AttachmentService.get_for_download(db, attachment_id)
    headers = {"Content-Disposition": f'inline; filename="{attachment.file_name}"'}
    return Response(
        content=attachment.file_data,
        media_type=attachment.mime_type,
        headers=headers,
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=AttachmentListResponse)
async def list_entity_attachments(
    entity_type: str,
    entity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachments = await AttachmentService.list_for_entity(db, entity_type, entity_id)
    return {"success": True, "data": attachments}


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await AttachmentService.delete(db, attachment_id, current_user)
    return {"success": True, "message": "Attachment deleted"}
