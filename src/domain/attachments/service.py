"""AttachmentService

Generic polymorphic file upload/download/list/delete, ported from legacy
`app/routers/attachment_router.py`. Kept as a service (not just a thin
router) so any other domain can reuse `AttachmentService.upload(...)`
programmatically later without going through HTTP.
"""

import base64
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import (
    AuthorizationException,
    ResourceNotFoundException,
    ValidationException,
)
from src.core.logger import get_logger
from src.domain.attachments.crud import attachment_crud
from src.domain.attachments.models import Attachment
from src.domain.users.models import User

logger = get_logger(__name__)

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "image/jpeg",
    "image/png",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _normalize_mime_type(mime_type: str) -> str:
    mime_type_norm = mime_type.strip().lower()
    if mime_type_norm in ("application/jpg", "image/jpg"):
        mime_type_norm = "image/jpeg"
    if mime_type_norm == "application/txt":
        mime_type_norm = "text/plain"
    return mime_type_norm


def _decode_base64_to_bytes(data: str) -> bytes:
    try:
        # Accept raw base64 or data URL format: data:<mime>;base64,<...>
        if data.strip().startswith("data:") and "," in data:
            data = data.split(",", 1)[1]
        return base64.b64decode(data, validate=True)
    except Exception as exc:
        raise ValidationException("Invalid base64 file data") from exc


def _generate_attachment_code() -> str:
    return f"ATT-{secrets.token_hex(8).upper()}"[:30]


class AttachmentService:
    @staticmethod
    async def upload(
        db: AsyncSession,
        entity_type: str,
        entity_id: int,
        file_name: str,
        mime_type: str,
        file_data_b64: str,
        current_user: User,
    ) -> Attachment:
        mime_type_norm = _normalize_mime_type(mime_type)
        if mime_type_norm not in ALLOWED_MIME_TYPES:
            raise ValidationException("Unsupported file type")

        raw = _decode_base64_to_bytes(file_data_b64)
        if len(raw) == 0:
            raise ValidationException("File is empty")
        if len(raw) > MAX_FILE_SIZE_BYTES:
            raise ValidationException("File exceeds maximum allowed size (10 MB)")

        attachment = await attachment_crud.create(
            db,
            {
                "attachment_code": _generate_attachment_code(),
                "entity_type": entity_type.lower(),
                "entity_id": int(entity_id),
                "file_name": file_name,
                "mime_type": mime_type_norm,
                "file_size": len(raw),
                "file_data": raw,
                "created_by": current_user.id,
            },
        )
        logger.info(
            f"Attachment uploaded: {attachment.attachment_code} by user={current_user.id}",
        )
        return attachment

    @staticmethod
    async def get_for_download(db: AsyncSession, attachment_id: int) -> Attachment:
        attachment = await attachment_crud.get_by(db, id=attachment_id, is_active=True)
        if not attachment:
            raise ResourceNotFoundException("Attachment not found")
        return attachment

    @staticmethod
    async def list_for_entity(
        db: AsyncSession,
        entity_type: str,
        entity_id: int,
    ) -> list[Attachment]:
        query = (
            select(Attachment)
            .filter(
                Attachment.entity_type == entity_type.lower(),
                Attachment.entity_id == entity_id,
                Attachment.is_active,
            )
            .order_by(Attachment.created_at.desc())
        )
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, attachment_id: int, current_user: User) -> None:
        attachment = await attachment_crud.get(db, attachment_id)
        if not attachment:
            raise ResourceNotFoundException("Attachment not found")

        is_owner = attachment.created_by == current_user.id
        is_admin = current_user.role == UserRole.ADMIN
        if not (is_owner or is_admin):
            raise AuthorizationException(
                "You do not have permission to delete this attachment",
            )

        await attachment_crud.update(db, attachment_id, {"is_active": False})
