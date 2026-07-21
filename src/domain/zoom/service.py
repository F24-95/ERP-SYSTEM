from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ResourceNotFoundException
from src.core.logger import get_logger
from src.domain.zoom.crud import zoom_file_crud, zoom_meeting_crud
from src.domain.zoom.models import ZoomFile, ZoomMeeting

logger = get_logger(__name__)


class ZoomFileService:
    """Full CRUD for ZoomFile -- the one entity in this domain meant to be
    written directly (by a teacher/admin uploading or linking session
    files), as opposed to ZoomMeeting/ZoomParticipant/etc., which are meant
    to be synced from the Zoom API by a background job (see module
    docstring in models.py).
    """

    @staticmethod
    async def create(db: AsyncSession, data: dict) -> ZoomFile:
        return await zoom_file_crud.create(db, data)

    @staticmethod
    async def list_files(
        db: AsyncSession,
        classroom_id: int | None = None,
        date: str | None = None,
    ) -> list[ZoomFile]:
        query = select(ZoomFile).filter(ZoomFile.is_active == True)  # noqa: E712
        if classroom_id is not None:
            query = query.filter(ZoomFile.classroom_id == classroom_id)
        if date is not None:
            query = query.filter(ZoomFile.date == date)
        query = query.order_by(ZoomFile.date.desc())
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get(db: AsyncSession, zoom_file_id: int) -> ZoomFile:
        item = await zoom_file_crud.get(db, zoom_file_id)
        if not item:
            raise ResourceNotFoundException("Zoom file bundle not found")
        return item

    @staticmethod
    async def update(db: AsyncSession, zoom_file_id: int, data: dict) -> ZoomFile:
        await ZoomFileService.get(db, zoom_file_id)
        return await zoom_file_crud.update(db, zoom_file_id, data)

    @staticmethod
    async def delete(db: AsyncSession, zoom_file_id: int) -> None:
        await ZoomFileService.get(db, zoom_file_id)
        await zoom_file_crud.update(db, zoom_file_id, {"is_active": False})


class ZoomMeetingService:
    """Read + ingest for ZoomMeeting. `ingest` is the landing point for a
    future Zoom API sync job -- actual Zoom webhook/API polling is out of
    scope here (no legacy job exists to port; this is new integration
    surface), this is only the data-landing contract for it.
    """

    @staticmethod
    async def ingest(db: AsyncSession, data: dict) -> ZoomMeeting:
        existing = await db.get(ZoomMeeting, data["uuid"])
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            await db.flush()
            return existing
        return await zoom_meeting_crud.create(db, data)

    @staticmethod
    async def list_meetings(
        db: AsyncSession,
        host_id: str | None = None,
    ) -> list[ZoomMeeting]:
        query = select(ZoomMeeting)
        if host_id is not None:
            query = query.filter(ZoomMeeting.host_id == host_id)
        query = query.order_by(ZoomMeeting.start_time.desc())
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get(db: AsyncSession, uuid: str) -> ZoomMeeting:
        meeting = await db.get(ZoomMeeting, uuid)
        if not meeting:
            raise ResourceNotFoundException("Zoom meeting not found")
        return meeting
