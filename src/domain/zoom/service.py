from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ResourceNotFoundException
from src.core.logger import get_logger
from src.domain.zoom.crud import zoom_file_crud, zoom_meeting_crud
from src.domain.zoom.models import (
    ZoomFile,
    ZoomMeeting,
    ZoomParticipant,
    ZoomRecordingFile,
    ZoomStudentInteraction,
    ZoomTranscript,
)

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


class ZoomReportService:
    """Zoom meeting report service — class-wise and meeting-wise reports
    showing duration, participant attendance, interactions (questions/answers).
    Queries ZoomFile, ProcessedMeeting, and RawMeeting tables to find data.
    """

    @staticmethod
    async def _build_meeting_entry(
        db: AsyncSession,
        topic: str,
        start_time: datetime | None,
        duration_min: int,
        meeting_date: str,
        meeting_time: str,
        classroom_name: str,
        participants: list,
        interactions: list,
        speaker_stats: dict,
        transcript_count: int,
        has_recording: bool,
        has_transcript: bool,
        meeting_uuid: str | None = None,
    ) -> dict:
        """Build a single meeting entry dict for the report."""
        return {
            "meeting_uuid": meeting_uuid,
            "topic": topic,
            "start_time": start_time.isoformat() if start_time else None,
            "duration_minutes": duration_min,
            "date": meeting_date,
            "time": meeting_time,
            "class_name": classroom_name,
            "participants_count": len(participants),
            "participants": participants,
            "interactions": interactions,
            "speaker_stats": list(speaker_stats.values()),
            "transcript_segments": transcript_count,
            "recording_available": has_recording,
            "transcript_available": has_transcript,
        }

    @staticmethod
    async def get_class_zoom_report(
        db: AsyncSession,
        classroom_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """Class-wise Zoom report: list all meetings for a classroom with
        per-student detail (join/leave/duration/interactions/speaking time)."""
        from src.domain.academics.models import ClassRoom
        from src.domain.zoom.models import ProcessedMeeting, ProcessedParticipant, RawMeeting, RawParticipant

        classroom = await db.get(ClassRoom, classroom_id)
        if not classroom:
            raise ResourceNotFoundException("Classroom not found")

        meetings_data = []
        total_duration = 0
        total_participants = 0
        total_interactions = 0

        # ── Source 1: ZoomFile + ZoomMeeting (primary) ──
        query = select(ZoomFile).filter(
            ZoomFile.classroom_id == classroom_id,
            ZoomFile.is_active == True,  # noqa: E712
        )
        zoom_files = list((await db.execute(query)).scalars().all())

        for zf in zoom_files:
            recording_file = None
            if zf.recording_file_id:
                try:
                    recording_file = await db.get(ZoomRecordingFile, zf.recording_file_id)
                except Exception:
                    recording_file = None

            meeting = None
            if recording_file:
                try:
                    meeting = await db.get(ZoomMeeting, recording_file.meeting_uuid)
                except Exception:
                    meeting = None

            # Get participants
            participants_raw = []
            if meeting:
                participants_raw = list(
                    (await db.execute(
                        select(ZoomParticipant).filter_by(meeting_uuid=meeting.uuid)
                    )).scalars().all()
                )

            # Get interactions for this recording
            interactions_raw = []
            if recording_file:
                interactions_raw = list(
                    (await db.execute(
                        select(ZoomStudentInteraction).filter_by(recording_file_id=recording_file.id)
                    )).scalars().all()
                )
            total_interactions += len(interactions_raw)

            # Build per-student detail: link participant ↔ interactions by speaker_name
            interaction_by_speaker = {}
            for i in interactions_raw:
                name = i.speaker_name
                if name not in interaction_by_speaker:
                    interaction_by_speaker[name] = {
                        "count": 0,
                        "total_seconds": 0,
                        "times": [],
                    }
                interaction_by_speaker[name]["count"] += 1
                interaction_by_speaker[name]["total_seconds"] += i.interaction_duration or 0
                interaction_by_speaker[name]["times"].append(i.interaction_time)

            # Build per-student list with joined interaction data
            per_student = []
            for p in participants_raw:
                name = p.name
                stats = interaction_by_speaker.get(name, {"count": 0, "total_seconds": 0, "times": []})
                per_student.append({
                    "name": name,
                    "email": p.user_email,
                    "join_time": p.join_time.isoformat() if p.join_time else None,
                    "leave_time": p.leave_time.isoformat() if p.leave_time else None,
                    "duration_minutes": p.duration_minutes or 0,
                    "duration_seconds": p.duration_seconds or 0,
                    "status": p.status,
                    "attentiveness_score": p.attentiveness_score,
                    "interaction_count": stats["count"],
                    "total_speaking_seconds": stats["total_seconds"],
                    "interaction_times": stats["times"],
                })
            total_participants += len(participants_raw)

            # Transcript count
            transcript_count = 0
            if recording_file:
                try:
                    trans = list(
                        (await db.execute(
                            select(ZoomTranscript).filter_by(recording_file_id=recording_file.id)
                        )).scalars().all()
                    )
                    transcript_count = len(trans)
                except Exception:
                    transcript_count = 0

            duration_min = (meeting.duration if meeting and meeting.duration else 0) or 0
            total_duration += duration_min

            # Compute summary stats for this meeting
            speakers_with_interactions = sum(1 for s in per_student if s["interaction_count"] > 0)
            avg_attentiveness = 0
            att_scores = [int(p.get("attentiveness_score") or 0) for p in per_student if p.get("attentiveness_score")]
            if att_scores:
                avg_attentiveness = round(sum(att_scores) / len(att_scores), 1)

            entry = {
                "meeting_uuid": meeting.uuid if meeting else None,
                "topic": (meeting.topic if meeting else None) or zf.file_initial,
                "start_time": meeting.start_time.isoformat() if meeting and meeting.start_time else None,
                "duration_minutes": duration_min,
                "date": zf.date,
                "time": zf.time,
                "class_name": classroom.display_name,
                "participants_count": len(participants_raw),
                "per_student": per_student,
                "speaker_stats": [
                    {
                        "speaker_name": name,
                        "interaction_count": s["count"],
                        "total_speaking_seconds": s["total_seconds"],
                    }
                    for name, s in interaction_by_speaker.items()
                ],
                "transcript_segments": transcript_count,
                "recording_available": bool(zf.video_file or zf.audio_file),
                "transcript_available": bool(zf.transcript_file),
                "speakers_with_interactions": speakers_with_interactions,
                "avg_attentiveness": avg_attentiveness,
            }
            meetings_data.append(entry)

        # ── Source 2: ProcessedMeeting (fallback if no ZoomFile data) ──
        if not meetings_data:
            pm_query = select(ProcessedMeeting).filter(
                ProcessedMeeting.topic.ilike(f"%{classroom.class_name}%")
            )
            if start_date:
                pm_query = pm_query.filter(ProcessedMeeting.meeting_date >= start_date)
            if end_date:
                pm_query = pm_query.filter(ProcessedMeeting.meeting_date <= end_date)
            pm_query = pm_query.order_by(ProcessedMeeting.start_time.desc())
            processed_meetings = list((await db.execute(pm_query)).scalars().all())

            for pm in processed_meetings:
                pp_list = list(
                    (await db.execute(
                        select(ProcessedParticipant).filter_by(meeting_id_fk=pm.id)
                    )).scalars().all()
                )
                per_student = [
                    {
                        "name": p.name,
                        "email": p.user_email,
                        "join_time": p.join_time.isoformat() if p.join_time else None,
                        "leave_time": p.leave_time.isoformat() if p.leave_time else None,
                        "duration_minutes": p.duration_minutes or 0,
                        "duration_seconds": p.duration_seconds or 0,
                        "status": p.status,
                        "attentiveness_score": p.attentiveness_score,
                        "interaction_count": 0,
                        "total_speaking_seconds": 0,
                        "interaction_times": [],
                    }
                    for p in pp_list
                ]
                total_participants += len(pp_list)
                total_duration += pm.duration_minutes or 0

                entry = {
                    "meeting_uuid": pm.uuid,
                    "topic": pm.topic or "Processed Meeting",
                    "start_time": pm.start_time.isoformat() if pm.start_time else None,
                    "duration_minutes": pm.duration_minutes or 0,
                    "date": str(pm.meeting_date) if pm.meeting_date else "",
                    "time": pm.start_time.strftime("%H:%M") if pm.start_time else "",
                    "class_name": classroom.display_name,
                    "participants_count": len(pp_list),
                    "per_student": per_student,
                    "speaker_stats": [],
                    "transcript_segments": 0,
                    "recording_available": False,
                    "transcript_available": False,
                    "speakers_with_interactions": 0,
                    "avg_attentiveness": 0,
                }
                meetings_data.append(entry)

        # ── Source 3: RawMeeting (fallback if nothing else) ──
        if not meetings_data:
            rm_query = select(RawMeeting)
            if start_date:
                rm_query = rm_query.filter(RawMeeting.start_time >= datetime.combine(start_date, datetime.min.time()))
            if end_date:
                rm_query = rm_query.filter(RawMeeting.start_time <= datetime.combine(end_date, datetime.max.time()))
            rm_query = rm_query.order_by(RawMeeting.start_time.desc())
            raw_meetings = list((await db.execute(rm_query)).scalars().all())

            for rm in raw_meetings:
                rp_list = list(
                    (await db.execute(
                        select(RawParticipant).filter_by(meeting_id_fk=rm.id)
                    )).scalars().all()
                )
                per_student = [
                    {
                        "name": p.name,
                        "email": p.user_email,
                        "join_time": p.join_time.isoformat() if p.join_time else None,
                        "leave_time": p.leave_time.isoformat() if p.leave_time else None,
                        "duration_minutes": 0,
                        "duration_seconds": p.duration_seconds or 0,
                        "status": p.status,
                        "attentiveness_score": p.attentiveness_score,
                        "interaction_count": 0,
                        "total_speaking_seconds": 0,
                        "interaction_times": [],
                    }
                    for p in rp_list
                ]
                total_participants += len(rp_list)
                total_duration += rm.duration_minutes or 0

                entry = {
                    "meeting_uuid": rm.uuid,
                    "topic": rm.topic or "Raw Meeting",
                    "start_time": rm.start_time.isoformat() if rm.start_time else None,
                    "duration_minutes": rm.duration_minutes or 0,
                    "date": rm.start_time.strftime("%Y-%m-%d") if rm.start_time else "",
                    "time": rm.start_time.strftime("%H:%M") if rm.start_time else "",
                    "class_name": classroom.display_name,
                    "participants_count": len(rp_list),
                    "per_student": per_student,
                    "speaker_stats": [],
                    "transcript_segments": 0,
                    "recording_available": False,
                    "transcript_available": False,
                    "speakers_with_interactions": 0,
                    "avg_attentiveness": 0,
                }
                meetings_data.append(entry)

        session_count = len(meetings_data)
        return {
            "classroom": {"id": classroom.id, "name": classroom.display_name},
            "summary": {
                "total_sessions": session_count,
                "total_duration_minutes": total_duration,
                "total_participants": total_participants,
                "total_interactions": total_interactions,
                "avg_duration_minutes": round(total_duration / session_count, 1) if session_count else 0,
                "avg_participants": round(total_participants / session_count, 1) if session_count else 0,
            },
            "meetings": meetings_data,
        }

    @staticmethod
    async def get_meeting_detail_report(
        db: AsyncSession,
        meeting_uuid: str,
    ) -> dict:
        """Detailed single meeting report with per-student detail:
        join/leave times, duration, interactions, and speaking stats."""
        meeting = await db.get(ZoomMeeting, meeting_uuid)
        if not meeting:
            raise ResourceNotFoundException("Meeting not found")

        # Get recording files
        recordings = list(
            (
                await db.execute(
                    select(ZoomRecordingFile).filter_by(meeting_uuid=meeting_uuid)
                )
            )
            .scalars()
            .all()
        )

        # Get participants
        participants_raw = list(
            (
                await db.execute(
                    select(ZoomParticipant).filter_by(meeting_uuid=meeting_uuid)
                )
            )
            .scalars()
            .all()
        )

        # Get ALL interactions across all recordings
        all_interactions = []
        for rec in recordings:
            interactions = list(
                (
                    await db.execute(
                        select(ZoomStudentInteraction).filter_by(recording_file_id=rec.id)
                    )
                )
                .scalars()
                .all()
            )
            for i in interactions:
                all_interactions.append(i)

        # Get ALL transcripts across all recordings
        all_transcripts = []
        for rec in recordings:
            transcripts = list(
                (
                    await db.execute(
                        select(ZoomTranscript).filter_by(recording_file_id=rec.id)
                    )
                )
                .scalars()
                .all()
            )
            for t in transcripts:
                all_transcripts.append(t)

        # Build per-student detail: link each participant with their interactions
        interaction_by_speaker = {}
        for i in all_interactions:
            name = i.speaker_name
            if name not in interaction_by_speaker:
                interaction_by_speaker[name] = {
                    "count": 0,
                    "total_seconds": 0,
                    "times": [],
                    "durations": [],
                }
            interaction_by_speaker[name]["count"] += 1
            interaction_by_speaker[name]["total_seconds"] += i.interaction_duration or 0
            interaction_by_speaker[name]["times"].append(i.interaction_time)
            interaction_by_speaker[name]["durations"].append(i.interaction_duration or 0)

        # Build per-student list with linked interaction data
        per_student = []
        for p in participants_raw:
            name = p.name
            stats = interaction_by_speaker.get(name, {
                "count": 0, "total_seconds": 0, "times": [], "durations": []
            })
            per_student.append({
                "name": name,
                "email": p.user_email,
                "join_time": p.join_time.isoformat() if p.join_time else None,
                "leave_time": p.leave_time.isoformat() if p.leave_time else None,
                "duration_minutes": p.duration_minutes or 0,
                "duration_seconds": p.duration_seconds or 0,
                "status": p.status,
                "attentiveness_score": p.attentiveness_score,
                "interaction_count": stats["count"],
                "total_speaking_seconds": stats["total_seconds"],
                "interaction_times": stats["times"],
                "interaction_durations": stats["durations"],
            })

        # Speaker summary stats
        speaker_stats = [
            {
                "speaker_name": name,
                "interaction_count": s["count"],
                "total_speaking_seconds": s["total_seconds"],
            }
            for name, s in interaction_by_speaker.items()
        ]

        # Find classroom name from zoom files
        classroom_name = None
        classroom_id = None
        if recordings:
            for rec in recordings:
                try:
                    zf_list = list(
                        (await db.execute(
                            select(ZoomFile).filter_by(recording_file_id=rec.id)
                        )).scalars().all()
                    )
                    for zf in zf_list:
                        if zf.classroom_id:
                            classroom_id = zf.classroom_id
                            from src.domain.academics.models import ClassRoom
                            cr = await db.get(ClassRoom, zf.classroom_id)
                            if cr:
                                classroom_name = cr.display_name
                                break
                    if classroom_name:
                        break
                except Exception:
                    pass

        # Compute summary
        speakers_with_interactions = sum(1 for p in per_student if p["interaction_count"] > 0)
        att_scores = [int(p.get("attentiveness_score") or 0) for p in per_student if p.get("attentiveness_score")]
        avg_attentiveness = round(sum(att_scores) / len(att_scores), 1) if att_scores else 0

        return {
            "meeting": {
                "uuid": meeting.uuid,
                "topic": meeting.topic,
                "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
                "duration_minutes": meeting.duration,
                "host_id": meeting.host_id,
                "recording_count": meeting.recording_count,
                "share_url": meeting.share_url,
                "classroom_name": classroom_name,
                "classroom_id": classroom_id,
            },
            "summary": {
                "participants_count": len(participants_raw),
                "total_interactions": len(all_interactions),
                "total_transcript_segments": len(all_transcripts),
                "total_speaking_seconds": sum(
                    s["total_speaking_seconds"] for s in speaker_stats
                ),
                "speakers_with_interactions": speakers_with_interactions,
                "avg_attentiveness": avg_attentiveness,
            },
            "per_student": per_student,
            "participants": per_student,  # alias for frontend compatibility
            "speaker_stats": speaker_stats,
            "transcripts": [
                {
                    "speaker": t.speaker,
                    "text": t.text,
                    "start_time": t.start_time,
                    "end_time": t.end_time,
                    "duration": t.duration,
                }
                for t in all_transcripts[:50]
            ],
        }

    @staticmethod
    async def list_all_meetings(
        db: AsyncSession,
        classroom_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        """List all meetings with basic stats, optionally filtered by
        classroom and date range."""
        query = select(ZoomMeeting)
        if start_date:
            query = query.filter(ZoomMeeting.start_time >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(ZoomMeeting.start_time <= datetime.combine(end_date, datetime.max.time()))
        query = query.order_by(ZoomMeeting.start_time.desc())
        meetings = list((await db.execute(query)).scalars().all())

        result = []
        for m in meetings:
            # Get participant count
            part_count = 0
            if m.participants:
                part_count = len(m.participants)

            # Get classroom name from linked zoom files
            classroom_name = None
            if m.recording_files:
                for rf in m.recording_files:
                    if rf.zoom_file_links:
                        for zf in rf.zoom_file_links:
                            if zf.classroom_id:
                                from src.domain.academics.models import ClassRoom
                                cr = await db.get(ClassRoom, zf.classroom_id)
                                if cr:
                                    classroom_name = cr.display_name
                                    break
                        if classroom_name:
                            break

            result.append({
                "uuid": m.uuid,
                "topic": m.topic,
                "start_time": m.start_time.isoformat() if m.start_time else None,
                "duration_minutes": m.duration,
                "participants_count": part_count,
                "recording_count": m.recording_count or 0,
                "classroom_name": classroom_name,
            })

        return result
