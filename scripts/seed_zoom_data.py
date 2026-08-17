"""Seed Zoom meeting data for testing reports.

Run from the project root:
    python -m scripts.seed_zoom_data

Requires DATABASE_URL environment variable to be set (PostgreSQL).
"""

import asyncio
import os
import random
import sys
import uuid as uuid_mod
from datetime import date, datetime, timedelta

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database.connection import DATABASE_URL
from src.domain.academics.models import ClassRoom
from src.domain.zoom.models import (
    ZoomFile,
    ZoomMeeting,
    ZoomParticipant,
    ZoomRecordingFile,
    ZoomStudentInteraction,
    ZoomTranscript,
)


async def seed_zoom_data():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        classrooms = list(
            (await db.execute(
                select(ClassRoom).filter(ClassRoom.is_active == True)  # noqa: E712
            )).scalars().all()
        )
        if not classrooms:
            print("No active classrooms found. Run seed_all_data.py first.")
            return

        # Check if properly seeded data already exists
        existing = list(
            (await db.execute(
                select(ZoomFile).filter(ZoomFile.classroom_id.isnot(None)).limit(1)
            )).scalars().all()
        )
        if existing:
            print("Zoom data already seeded with classroom links. Skipping.")
            return

        created_count = 0

        CLASS_STUDENT_POOLS = [
            [
                ("Aarav Sharma", "aarav@school.com"),
                ("Priya Patel", "priya@school.com"),
                ("Rohan Gupta", "rohan@school.com"),
                ("Ananya Singh", "ananya@school.com"),
                ("Vikram Kumar", "vikram@school.com"),
            ],
            [
                ("Neha Reddy", "neha@school.com"),
                ("Arjun Mehta", "arjun@school.com"),
                ("Kavya Nair", "kavya@school.com"),
                ("Aditya Verma", "aditya@school.com"),
                ("Ishita Joshi", "ishita@school.com"),
            ],
            [
                ("Rahul Yadav", "rahul@school.com"),
                ("Sneha Rao", "sneha@school.com"),
                ("Karan Malhotra", "karan@school.com"),
                ("Pooja Desai", "pooja@school.com"),
                ("Nikhil Bhat", "nikhil@school.com"),
            ],
            [
                ("Tanvi Kulkarni", "tanvi@school.com"),
                ("Amit Tiwari", "amit@school.com"),
                ("Deepika Choudhary", "deepika@school.com"),
                ("Sanjay Mishra", "sanjay@school.com"),
                ("Ritu Agarwal", "ritu@school.com"),
            ],
            [
                ("Manish Pandey", "manish@school.com"),
                ("Shruti Kulkarni", "shruti@school.com"),
                ("Ravi Shankar", "ravi@school.com"),
                ("Meera Krishnan", "meera@school.com"),
                ("Arun Nair", "arun@school.com"),
            ],
        ]

        TOPICS_BY_CLASS = [
            ["Introduction to Numbers", "Basic Addition", "Shapes and Patterns"],
            ["Reading Comprehension", "Grammar Basics", "Creative Writing"],
            ["Plant Life", "Animal Habitats", "Simple Machines"],
            ["Indian History", "World Geography", "Civics Basics"],
            ["Algebra Fundamentals", "Geometry", "Data Handling"],
        ]

        DURATION_PATTERNS = [
            [35, 40, 45],
            [40, 45, 50],
            [45, 50, 55],
            [40, 42, 48],
            [50, 55, 60],
        ]

        SESSIONS_PER_CLASS = [4, 3, 5, 3, 4]

        TIME_SLOTS = [
            [9, 10, 11, 9],
            [10, 11, 10],
            [9, 10, 11, 9, 10],
            [11, 10, 11],
            [9, 11, 10, 9],
        ]

        interaction_types = [
            "asked a question",
            "answered a question",
            "raised hand",
            "shared screen",
            "made a comment",
            "responded to teacher",
            "asked for clarification",
            "gave a presentation",
        ]

        for ci, cr in enumerate(classrooms):
            students = CLASS_STUDENT_POOLS[ci % len(CLASS_STUDENT_POOLS)]
            topics = TOPICS_BY_CLASS[ci % len(TOPICS_BY_CLASS)]
            durations = DURATION_PATTERNS[ci % len(DURATION_PATTERNS)]
            sessions = SESSIONS_PER_CLASS[ci % len(SESSIONS_PER_CLASS)]
            time_slots = TIME_SLOTS[ci % len(TIME_SLOTS)]

            for si in range(sessions):
                meeting_uuid = str(uuid_mod.uuid4())
                meeting_date = date(2024, 6, 1) + timedelta(days=ci * 30 + si * 14)
                start = datetime(meeting_date.year, meeting_date.month, meeting_date.day,
                                 time_slots[si % len(time_slots)], 0)
                duration = durations[si % len(durations)]
                topic = topics[si % len(topics)]

                meeting = ZoomMeeting(
                    uuid=meeting_uuid,
                    meeting_id=200000 + ci * 100 + si,
                    host_id=f"teacher_{cr.id}",
                    topic=f"{cr.display_name} - {topic}",
                    type=2,
                    start_time=start,
                    timezone="Asia/Kolkata",
                    duration=duration,
                    recording_count=1,
                )
                db.add(meeting)
                await db.flush()

                rec_id = str(uuid_mod.uuid4())
                recording = ZoomRecordingFile(
                    id=rec_id,
                    meeting_uuid=meeting_uuid,
                    recording_start=start,
                    recording_end=start + timedelta(minutes=duration),
                    file_type="MP4",
                    file_extension="mp4",
                    status="completed",
                )
                db.add(recording)
                await db.flush()

                zf = ZoomFile(
                    file_initial=f"{cr.display_name} - {topic}",
                    raw_date=start.strftime("%Y-%m-%d"),
                    raw_time=start.strftime("%H:%M"),
                    date=start.strftime("%Y-%m-%d"),
                    time=start.strftime("%H:%M"),
                    classroom_id=cr.id,
                    recording_file_id=rec_id,
                )
                db.add(zf)

                for pi, (name, email) in enumerate(students):
                    join_delay = random.choice([0, 1, 2, 3, 5]) if pi > 0 else 0
                    join = start + timedelta(minutes=join_delay)
                    leave_offset = random.choice([0, 2, 3, 5, 8]) if pi < len(students) - 1 else 0
                    leave = start + timedelta(minutes=duration - leave_offset)
                    if leave <= join:
                        leave = join + timedelta(minutes=5)

                    duration_sec = int((leave - join).total_seconds())
                    duration_min = int(duration_sec / 60)
                    attentiveness = random.randint(55, 98)

                    participant = ZoomParticipant(
                        meeting_uuid=meeting_uuid,
                        zoom_participant_id=str(uuid_mod.uuid4()),
                        name=name,
                        user_email=email,
                        join_time=join,
                        leave_time=leave,
                        meeting_date=start.date(),
                        duration_seconds=duration_sec,
                        duration_minutes=duration_min,
                        status="in_meeting",
                        attentiveness_score=str(attentiveness),
                    )
                    db.add(participant)

                    base_interactions = max(1, 6 - ci)
                    num_interactions = random.randint(
                        max(1, base_interactions - 2),
                        base_interactions + 2,
                    )

                    for inter_idx in range(num_interactions):
                        inter_minute = random.randint(2, max(3, duration - 3))
                        interaction = ZoomStudentInteraction(
                            recording_file_id=rec_id,
                            class_date=start,
                            class_name=cr.display_name,
                            interaction_time=f"00:{inter_minute:02d}:{random.randint(0, 59):02d}",
                            interaction_duration=random.randint(8, 90),
                            speaker_name=name,
                        )
                        db.add(interaction)

                    num_transcripts = random.randint(2, min(6, duration // 8))
                    for ti in range(num_transcripts):
                        seg_time = random.randint(0, max(1, duration - 5))
                        transcript = ZoomTranscript(
                            recording_file_id=rec_id,
                            segment_index=pi * 10 + ti,
                            start_time=f"00:{seg_time:02d}:00",
                            end_time=f"00:{min(seg_time + 2, duration - 1):02d}:00",
                            duration=random.uniform(60.0, 180.0),
                            speaker=name,
                            text=f"Discussion about {topic.lower()} in {cr.display_name}",
                            class_name=cr.display_name,
                            class_date=start,
                        )
                        db.add(transcript)

                created_count += 1

        await db.commit()
        print(f"Seeded {created_count} unique Zoom sessions across {len(classrooms)} classes with varied data.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_zoom_data())
