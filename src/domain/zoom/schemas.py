from datetime import datetime

from pydantic import BaseModel


# ===========================
# ZoomFile (session file bundle -- the one user-facing entity in this domain)
# ===========================
class ZoomFileBase(BaseModel):
    file_initial: str
    transcript_file: str | None = None
    audio_file: str | None = None
    audio_duration: str | None = None
    video_file: str | None = None
    video_duration: str | None = None
    raw_date: str
    raw_time: str
    date: str
    time: str
    classroom_id: int | None = None
    recording_file_id: str | None = None


class ZoomFileCreate(ZoomFileBase):
    pass


class ZoomFileUpdate(BaseModel):
    transcript_file: str | None = None
    audio_file: str | None = None
    audio_duration: str | None = None
    video_file: str | None = None
    video_duration: str | None = None
    classroom_id: int | None = None
    is_active: bool | None = None


class ZoomFileResponse(ZoomFileBase):
    id: int
    zoom_file_code: str
    is_active: bool | None = None

    class Config:
        from_attributes = True


# ===========================
# ZoomMeeting (read-mostly; landing point for a future Zoom API sync job)
# ===========================
class ZoomMeetingIngest(BaseModel):
    uuid: str
    meeting_id: int | None = None
    account_id: str | None = None
    host_id: str | None = None
    topic: str | None = None
    type: int | None = None
    start_time: datetime | None = None
    timezone: str | None = None
    duration: int | None = None
    total_size: int | None = None
    recording_count: int | None = 0
    share_url: str | None = None
    recording_play_passcode: str | None = None


class ZoomMeetingResponse(BaseModel):
    uuid: str
    meeting_id: int | None = None
    host_id: str | None = None
    topic: str | None = None
    start_time: datetime | None = None
    duration: int | None = None
    recording_count: int | None = None
    share_url: str | None = None

    class Config:
        from_attributes = True
