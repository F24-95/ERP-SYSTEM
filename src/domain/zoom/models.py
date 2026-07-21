"""Zoom integration domain.

Like khan_academy, none of these tables exist in the legacy `mmmmmm`
codebase -- they were drafted as new tables directly against this project's
schema (in the top-level `model/zoom.py` and `model/zoom_file.py` scratch
files) but never relocated into `src/domain/` or given schemas/crud/
service/router. This pass does that relocation, fixing the same class of
issues found in khan_academy/models.py: `app.*` imports rewritten to
`src.*`, and (for `ZoomFile.classroom`) wiring up to `ClassRoom.zoom_files`,
which was added to `src/domain/academics/models.py` as part of this same
pass since `ZoomFile` explicitly declared that back_populates target.

All FKs here were already correctly typed against this project's actual
column types in the drafts (Zoom's own UUID/ID strings, or `classroom.id`),
so -- unlike khan_academy's `student_profiles.student_id` issue -- no FK
retyping was needed here.
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.core.id_generators import generate_zoom_file_id
from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, TimestampMixin

# =============================================================================
# ZoomMeeting  (master meeting record from the Zoom API)
# =============================================================================


class ZoomMeeting(Base, TimestampMixin):
    __tablename__ = "zoom_meetings"

    uuid = Column(String(100), primary_key=True)

    meeting_id = Column(BigInteger, nullable=True, index=True)
    account_id = Column(String(100), nullable=True)
    host_id = Column(String(100), nullable=True)

    topic = Column(String(300), nullable=True)
    type = Column(Integer, nullable=True)  # 1=instant 2=scheduled 3=recurring
    start_time = Column(DateTime, nullable=True, index=True)
    timezone = Column(String(100), nullable=True)
    duration = Column(Integer, nullable=True)  # minutes

    total_size = Column(BigInteger, nullable=True)
    recording_count = Column(Integer, nullable=True, default=0)
    share_url = Column(String(500), nullable=True)
    recording_play_passcode = Column(String(100), nullable=True)

    recording_files = relationship(
        "ZoomRecordingFile",
        back_populates="zoom_meeting",
        cascade="all, delete-orphan",
    )
    participants = relationship(
        "ZoomParticipant",
        back_populates="zoom_meeting",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_zoom_meeting_id", "meeting_id"),
        Index("idx_zoom_meeting_start_time", "start_time"),
        Index("idx_zoom_meeting_host", "host_id"),
    )


# =============================================================================
# ZoomRecordingFile  (a recording file belonging to a ZoomMeeting)
# =============================================================================


class ZoomRecordingFile(Base, TimestampMixin):
    __tablename__ = "zoom_recording_files"

    id = Column(String(100), primary_key=True)  # Zoom file UUID
    meeting_uuid = Column(
        String(100),
        ForeignKey("zoom_meetings.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recording_start = Column(DateTime, nullable=True, index=True)
    recording_end = Column(DateTime, nullable=True)

    file_type = Column(String(50), nullable=True)  # MP4, M4A, TRANSCRIPT, CHAT...
    file_extension = Column(String(20), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    recording_type = Column(String(100), nullable=True)

    play_url = Column(String(1000), nullable=True)
    download_url = Column(String(1000), nullable=True)
    status = Column(String(50), nullable=True)

    zoom_meeting = relationship("ZoomMeeting", back_populates="recording_files")
    transcripts = relationship(
        "ZoomTranscript",
        back_populates="recording_file",
        cascade="all, delete-orphan",
    )
    student_interactions = relationship(
        "ZoomStudentInteraction",
        back_populates="recording_file",
        cascade="all, delete-orphan",
    )
    zoom_file_links = relationship("ZoomFile", back_populates="recording_file")

    __table_args__ = (
        Index("idx_zoom_rec_file_meeting", "meeting_uuid"),
        Index("idx_zoom_rec_file_type", "file_type"),
        Index("idx_zoom_rec_file_start", "recording_start"),
    )


# =============================================================================
# ZoomTranscript  (one speaker segment from a meeting transcript)
# =============================================================================


class ZoomTranscript(Base, TimestampMixin):
    __tablename__ = "zoom_transcripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recording_file_id = Column(
        String(100),
        ForeignKey("zoom_recording_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    segment_index = Column(Integer, nullable=False)
    start_time = Column(String(20), nullable=False)  # e.g. "00:01:23.456"
    end_time = Column(String(20), nullable=False)
    duration = Column(Float, nullable=False)  # seconds

    speaker = Column(String(200), nullable=False)
    text = Column(Text, nullable=False)

    class_name = Column(String(200), nullable=True)
    class_date = Column(DateTime, nullable=True, index=True)
    file_name = Column(String(255), nullable=True)

    recording_file = relationship("ZoomRecordingFile", back_populates="transcripts")

    __table_args__ = (
        UniqueConstraint(
            "recording_file_id",
            "segment_index",
            name="uq_zoom_transcript_segment",
        ),
        Index("idx_zoom_transcript_speaker", "speaker"),
        Index("idx_zoom_transcript_class_date", "class_date"),
    )


# =============================================================================
# ZoomStudentInteraction  (one speaking turn by a student)
# =============================================================================


class ZoomStudentInteraction(Base, TimestampMixin):
    __tablename__ = "zoom_student_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recording_file_id = Column(
        String(100),
        ForeignKey("zoom_recording_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    class_date = Column(DateTime, nullable=True, index=True)
    class_name = Column(String(200), nullable=True)

    interaction_time = Column(String(20), nullable=False)  # "00:05:42"
    interaction_duration = Column(Float, nullable=False)  # seconds
    speaker_name = Column(String(200), nullable=False, index=True)

    recording_file = relationship(
        "ZoomRecordingFile",
        back_populates="student_interactions",
    )

    __table_args__ = (
        Index("idx_zoom_interaction_speaker", "speaker_name"),
        Index("idx_zoom_interaction_class_date", "class_date"),
        Index("idx_zoom_interaction_file", "recording_file_id"),
    )


# =============================================================================
# ZoomParticipant  (join/leave data from the Zoom API)
# =============================================================================


class ZoomParticipant(Base, TimestampMixin):
    __tablename__ = "zoom_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_uuid = Column(
        String(100),
        ForeignKey("zoom_meetings.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    zoom_participant_id = Column(String(100), nullable=True)
    user_id = Column(String(100), nullable=True)
    participant_user_id = Column(String(100), nullable=True)

    name = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True, index=True)

    join_time = Column(DateTime, nullable=True)
    leave_time = Column(DateTime, nullable=True)
    meeting_date = Column(Date, nullable=True, index=True)

    duration_seconds = Column(Integer, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    attentiveness_score = Column(String(20), nullable=True)
    failover = Column(Boolean, nullable=True, default=False)
    status = Column(String(50), nullable=True)

    group_id = Column(String(100), nullable=True)
    customer_key = Column(String(100), nullable=True)
    bo_mtg_id = Column(String(100), nullable=True)

    zoom_meeting = relationship("ZoomMeeting", back_populates="participants")

    __table_args__ = (
        Index("idx_zoom_participant_meeting", "meeting_uuid"),
        Index("idx_zoom_participant_email", "user_email"),
        Index("idx_zoom_participant_meeting_date", "meeting_date"),
    )


# =============================================================================
# ProcessedMeeting / ProcessedParticipant  (legacy names: meetings/participants)
# =============================================================================


class ProcessedMeeting(Base, TimestampMixin):
    __tablename__ = "processed_meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    meeting_id = Column(String(100), nullable=True, index=True)
    uuid = Column(String(100), nullable=True, unique=True)

    topic = Column(String(300), nullable=True)
    start_time = Column(DateTime, nullable=True, index=True)
    end_time = Column(DateTime, nullable=True)
    meeting_date = Column(Date, nullable=True, index=True)

    duration_minutes = Column(Integer, nullable=True)
    participants_count = Column(Integer, nullable=True, default=0)

    # Comma-separated UUIDs of ZoomMeeting rows merged into this record
    merged_meeting_ids = Column(Text, nullable=True)

    processed_participants = relationship(
        "ProcessedParticipant",
        back_populates="processed_meeting",
        foreign_keys="ProcessedParticipant.meeting_id_fk",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_processed_meeting_date", "meeting_date"),
        Index("idx_processed_meeting_meeting", "meeting_id"),
    )


class ProcessedParticipant(Base, TimestampMixin):
    __tablename__ = "processed_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)

    meeting_id_fk = Column(
        Integer,
        ForeignKey("processed_meetings.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # Legacy second FK -- points to the same ProcessedMeeting row
    meeting_data_id = Column(
        Integer,
        ForeignKey("processed_meetings.id", ondelete="SET NULL"),
        nullable=True,
    )

    zoom_participant_id = Column(String(100), nullable=True)
    user_id = Column(String(100), nullable=True)
    participant_user_id = Column(String(100), nullable=True)

    name = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True, index=True)

    join_time = Column(DateTime, nullable=True)
    leave_time = Column(DateTime, nullable=True)
    meeting_date = Column(Date, nullable=True, index=True)

    duration_seconds = Column(Integer, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    attentiveness_score = Column(String(20), nullable=True)
    failover = Column(Boolean, nullable=True, default=False)
    status = Column(String(50), nullable=True)

    group_id = Column(String(100), nullable=True)
    customer_key = Column(String(100), nullable=True)
    bo_mtg_id = Column(String(100), nullable=True)

    processed_meeting = relationship(
        "ProcessedMeeting",
        foreign_keys=[meeting_id_fk],
        back_populates="processed_participants",
    )

    __table_args__ = (
        Index("idx_proc_participant_meeting", "meeting_id_fk"),
        Index("idx_proc_participant_email", "user_email"),
        Index("idx_proc_participant_meeting_date", "meeting_date"),
    )


# =============================================================================
# RawMeeting / RawParticipant  (staging/archive, unprocessed API responses)
# =============================================================================


class RawMeeting(Base, TimestampMixin):
    __tablename__ = "raw_meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    meeting_id = Column(String(100), nullable=True)
    uuid = Column(String(100), nullable=False, unique=True)
    topic = Column(String(300), nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    participants_count = Column(Integer, nullable=True)

    raw_participants = relationship(
        "RawParticipant",
        back_populates="raw_meeting",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_raw_meeting_uuid", "uuid"),
        Index("idx_raw_meeting_meeting_id", "meeting_id"),
        Index("idx_raw_meeting_start", "start_time"),
    )


class RawParticipant(Base, TimestampMixin):
    __tablename__ = "raw_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id_fk = Column(
        Integer,
        ForeignKey("raw_meetings.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    zoom_participant_id = Column(String(100), nullable=True)
    user_id = Column(String(100), nullable=True)
    participant_user_id = Column(String(100), nullable=True)

    name = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True, index=True)

    join_time = Column(DateTime, nullable=True)
    leave_time = Column(DateTime, nullable=True)

    duration_seconds = Column(Integer, nullable=True)
    attentiveness_score = Column(String(20), nullable=True)
    failover = Column(Boolean, nullable=True, default=False)
    status = Column(String(50), nullable=True)

    group_id = Column(String(100), nullable=True)
    customer_key = Column(String(100), nullable=True)
    bo_mtg_id = Column(String(100), nullable=True)

    raw_meeting = relationship("RawMeeting", back_populates="raw_participants")

    __table_args__ = (
        Index("idx_raw_participant_meeting", "meeting_id_fk"),
        Index("idx_raw_participant_email", "user_email"),
    )


# =============================================================================
# ZoomFile  (legacy-compat "session file bundle", not tied to the Zoom API)
# =============================================================================


class ZoomFile(Base, TimestampMixin, ActiveMixin):
    """One row = one class session's file bundle (transcript/audio/video),
    regardless of whether it came from the Zoom API, a manual upload, or a
    third-party recorder -- unlike ZoomRecordingFile, which assumes a Zoom
    API origin. `classroom_id` and `recording_file_id` are optional
    cross-references for when both exist for the same session.
    """

    __tablename__ = "zoom_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zoom_file_code = Column(
        String(30),
        unique=True,
        nullable=False,
        default=generate_zoom_file_id,
        index=True,
    )

    file_initial = Column(String(255), nullable=False, index=True)  # grouping key

    transcript_file = Column(String(500), nullable=True)
    audio_file = Column(String(500), nullable=True)
    audio_duration = Column(String(20), nullable=True)
    video_file = Column(String(500), nullable=True)
    video_duration = Column(String(20), nullable=True)

    raw_date = Column(String(50), nullable=False)
    raw_time = Column(String(50), nullable=False)
    date = Column(String(20), nullable=False, index=True)
    time = Column(String(20), nullable=False)

    classroom_id = Column(
        Integer,
        ForeignKey("classroom.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recording_file_id = Column(
        String(100),
        ForeignKey("zoom_recording_files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    classroom = relationship("ClassRoom", back_populates="zoom_files")
    recording_file = relationship("ZoomRecordingFile", back_populates="zoom_file_links")

    __table_args__ = (
        Index("idx_zoom_file_initial", "file_initial"),
        Index("idx_zoom_file_date", "date"),
        Index("idx_zoom_file_classroom", "classroom_id"),
        Index("idx_zoom_file_recording", "recording_file_id"),
    )
