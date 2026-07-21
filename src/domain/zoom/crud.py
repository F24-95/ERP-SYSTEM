from src.database.base_crud import AsyncBaseCRUD
from src.domain.zoom.models import (
    ProcessedMeeting,
    ProcessedParticipant,
    RawMeeting,
    RawParticipant,
    ZoomFile,
    ZoomMeeting,
    ZoomParticipant,
    ZoomRecordingFile,
    ZoomStudentInteraction,
    ZoomTranscript,
)

zoom_meeting_crud = AsyncBaseCRUD[ZoomMeeting](ZoomMeeting)
zoom_recording_file_crud = AsyncBaseCRUD[ZoomRecordingFile](ZoomRecordingFile)
zoom_transcript_crud = AsyncBaseCRUD[ZoomTranscript](ZoomTranscript)
zoom_student_interaction_crud = AsyncBaseCRUD[ZoomStudentInteraction](
    ZoomStudentInteraction,
)
zoom_participant_crud = AsyncBaseCRUD[ZoomParticipant](ZoomParticipant)
processed_meeting_crud = AsyncBaseCRUD[ProcessedMeeting](ProcessedMeeting)
processed_participant_crud = AsyncBaseCRUD[ProcessedParticipant](ProcessedParticipant)
raw_meeting_crud = AsyncBaseCRUD[RawMeeting](RawMeeting)
raw_participant_crud = AsyncBaseCRUD[RawParticipant](RawParticipant)
zoom_file_crud = AsyncBaseCRUD[ZoomFile](ZoomFile)
