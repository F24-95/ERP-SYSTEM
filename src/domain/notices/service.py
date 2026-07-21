import os
import uuid
from datetime import date
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import NoticeAudience, NoticeType, UserRole
from src.core.exceptions import AuthorizationException, ResourceNotFoundException
from src.core.logger import get_logger
from src.domain.notices.crud import notice_crud
from src.domain.notices.models import Notice
from src.domain.users.models import User

logger = get_logger(__name__)

UPLOAD_DIR = Path("uploads") / "notices"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _notice_file_disk_path(stored_name: str) -> Path:
    return UPLOAD_DIR / stored_name


def _delete_if_exists(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except Exception:
        logger.warning(f"Failed to delete file: {path}")


async def _save_notice_file(file: UploadFile) -> dict:
    original_name = file.filename or "notice"
    ext = os.path.splitext(original_name)[1]
    stored_name = f"{uuid.uuid4().hex}{ext}" if ext else uuid.uuid4().hex
    disk_path = _notice_file_disk_path(stored_name)

    with disk_path.open("wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)

    return {
        "attachment_name": original_name,
        "attachment_path": f"/uploads/notices/{stored_name}",
        "attachment_size": disk_path.stat().st_size,
        "mime_type": file.content_type,
    }


def _check_notice_access(notice: Notice, current_user: User) -> None:
    """Ported verbatim from legacy `_notice_access_check`. NOTE: the
    expiry/publish-date checks apply to every role including admin — legacy
    never granted admins a bypass for these, only for the audience checks
    below. Preserved exactly, not "fixed".
    """
    if notice.expiry_date is not None and date.today() > notice.expiry_date:
        raise ResourceNotFoundException("Notice expired")

    if notice.publish_date > date.today():
        raise ResourceNotFoundException("Notice not yet published")

    if current_user.role == UserRole.STUDENT:
        if notice.audience not in (NoticeAudience.ALL, NoticeAudience.STUDENT):
            raise AuthorizationException("Access denied")
    elif current_user.role == UserRole.TEACHER:
        if notice.audience not in (NoticeAudience.ALL, NoticeAudience.TEACHER):
            raise AuthorizationException("Access denied")


class NoticeService:
    @staticmethod
    async def create_notice(
        db: AsyncSession,
        *,
        title: str,
        description: str,
        notice_type: NoticeType,
        audience: NoticeAudience,
        publish_date: date,
        expiry_date: date | None,
        is_pinned: bool,
        academic_sessions_id: int,
        classroom_id: int | None,
        file: UploadFile | None,
        current_user: User,
    ) -> Notice:
        attachment_fields = {
            "attachment_name": None,
            "attachment_path": None,
            "attachment_size": None,
            "mime_type": None,
        }

        # Only a real, named file upload counts as an attachment — some HTTP
        # clients still send an empty file part even when "no file" was intended.
        if file is not None and file.filename:
            attachment_fields = await _save_notice_file(file)

        notice = await notice_crud.create(
            db,
            {
                "academic_sessions_id": academic_sessions_id,
                "classroom_id": classroom_id,
                "title": title,
                "description": description,
                "notice_type": notice_type,
                "audience": audience,
                "publish_date": publish_date,
                "expiry_date": expiry_date,
                "is_pinned": is_pinned,
                "created_by": current_user.id,
                **attachment_fields,
            },
        )
        logger.info(f"Notice created: {notice.notice_id} by user={current_user.id}")
        return notice

    @staticmethod
    async def get_notices(
        db: AsyncSession,
        current_user: User,
        notice_type: NoticeType | None = None,
        is_pinned: bool | None = None,
    ) -> list[Notice]:
        query = select(Notice).filter(
            Notice.is_active,
            Notice.publish_date <= date.today(),
        )

        if notice_type:
            query = query.filter(Notice.notice_type == notice_type)
        if is_pinned is not None:
            query = query.filter(Notice.is_pinned == is_pinned)

        if current_user.role == UserRole.STUDENT:
            query = query.filter(
                Notice.audience.in_([NoticeAudience.ALL, NoticeAudience.STUDENT]),
            )
        elif current_user.role == UserRole.TEACHER:
            query = query.filter(
                Notice.audience.in_([NoticeAudience.ALL, NoticeAudience.TEACHER]),
            )
        # Admins see everything — no additional filter.

        query = query.order_by(Notice.is_pinned.desc(), Notice.publish_date.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_notice(
        db: AsyncSession,
        notice_id: int,
        current_user: User,
    ) -> Notice:
        notice = await notice_crud.get(db, notice_id)
        if not notice:
            raise ResourceNotFoundException("Notice not found")
        _check_notice_access(notice, current_user)
        return notice

    @staticmethod
    async def update_notice(
        db: AsyncSession,
        notice_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        notice_type: NoticeType | None = None,
        audience: NoticeAudience | None = None,
        publish_date: date | None = None,
        expiry_date: date | None = None,
        is_pinned: bool | None = None,
        classroom_id: int | None = None,
        file: UploadFile | None = None,
        current_user: User,
    ) -> Notice:
        notice = await notice_crud.get(db, notice_id)
        if not notice:
            raise ResourceNotFoundException("Notice not found")

        update_map = {
            "title": title,
            "description": description,
            "notice_type": notice_type,
            "audience": audience,
            "publish_date": publish_date,
            "expiry_date": expiry_date,
            "is_pinned": is_pinned,
            "classroom_id": classroom_id,
        }
        for key, value in update_map.items():
            if value is not None:
                setattr(notice, key, value)

        if file is not None:
            if notice.attachment_path:
                old_disk = Path(
                    str(notice.attachment_path).replace("/uploads/", "uploads/"),
                )
                _delete_if_exists(old_disk)

            attachment_fields = await _save_notice_file(file)
            notice.attachment_name = attachment_fields["attachment_name"]
            notice.attachment_path = attachment_fields["attachment_path"]
            notice.attachment_size = attachment_fields["attachment_size"]
            notice.mime_type = attachment_fields["mime_type"]

        notice.updated_by = current_user.id
        await db.flush()
        await db.refresh(notice)
        logger.info(f"Notice updated: {notice.notice_id} by user={current_user.id}")
        return notice

    @staticmethod
    async def delete_notice(
        db: AsyncSession,
        notice_id: int,
        current_user: User,
    ) -> None:
        notice = await notice_crud.get(db, notice_id)
        if not notice:
            raise ResourceNotFoundException("Notice not found")

        if notice.attachment_path:
            stored_name = os.path.basename(str(notice.attachment_path))
            _delete_if_exists(_notice_file_disk_path(stored_name))

        notice.is_active = False
        notice.deleted_by = current_user.id
        await db.flush()
        logger.info(f"Notice deleted: {notice.notice_id} by user={current_user.id}")

    @staticmethod
    async def pin_notice(db: AsyncSession, notice_id: int) -> None:
        notice = await notice_crud.get(db, notice_id)
        if not notice:
            raise ResourceNotFoundException("Notice not found")
        notice.is_pinned = True
        await db.flush()

    @staticmethod
    async def unpin_notice(db: AsyncSession, notice_id: int) -> None:
        notice = await notice_crud.get(db, notice_id)
        if not notice:
            raise ResourceNotFoundException("Notice not found")
        notice.is_pinned = False
        await db.flush()

    @staticmethod
    async def get_notice_file(
        db: AsyncSession,
        notice_id: int,
        current_user: User,
    ) -> Notice:
        """Used by both /view and /download — returns the notice only after
        confirming it has an attachment and passes the access check.
        """
        notice = await notice_crud.get(db, notice_id)
        if not notice or not notice.attachment_path:
            raise ResourceNotFoundException("Notice file not found")
        _check_notice_access(notice, current_user)
        return notice
