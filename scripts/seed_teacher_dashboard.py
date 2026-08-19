"""
Seed script to add today's timetable entries, daily classes,
assignments, and exams for the teacher dashboard to display.
Run with: python -m scripts.seed_teacher_dashboard
"""

import asyncio
import os
import sys
from datetime import date, datetime, timedelta, time, timezone
from uuid import uuid4
from random import choice, randint

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

env_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)
if os.path.isfile(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found")

if DATABASE_URL.startswith("postgresql+psycopg://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql+psycopg://", "postgresql+asyncpg://", 1
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

import src.database.base
from src.database.connection import Base

TABLES = Base.metadata.tables


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def gen_id(prefix, idx, digits=6):
    return f"{prefix}{idx:0{digits}d}"


async def seed_teacher_dashboard():
    async with AsyncSessionLocal() as s:
        now = utcnow()
        today = date.today()

        # Get current session
        res = await s.execute(
            text("SELECT id, session_name FROM academic_sessions WHERE is_current = true LIMIT 1")
        )
        sess = res.mappings().first()
        if not sess:
            print("[ERROR] No current academic session found")
            return
        current_session_id = sess["id"]
        print(f"[OK] Current session: {sess['session_name']} (id={current_session_id})")

        # Get classrooms for current session
        res = await s.execute(
            text("SELECT id, display_name, class_name, section FROM classroom WHERE academic_sessions_id = :sid"),
            {"sid": current_session_id},
        )
        classrooms = res.mappings().all()
        if not classrooms:
            print("[ERROR] No classrooms found for current session")
            return
        print(f"[OK] Found {len(classrooms)} classrooms")

        # Get subjects
        res = await s.execute(text("SELECT id, subject_name FROM subjects ORDER BY id"))
        subjects = res.mappings().all()
        subject_map = {sub["id"]: sub["subject_name"] for sub in subjects}
        print(f"[OK] Found {len(subjects)} subjects")

        # Get class_subjects for current session
        res = await s.execute(
            text("""
                SELECT cs.id, cs.classroom_id, cs.subject_id
                FROM class_subjects cs
                WHERE cs.academic_sessions_id = :sid
            """),
            {"sid": current_session_id},
        )
        class_subjects = res.mappings().all()
        cs_map = {}
        for cs in class_subjects:
            cs_map.setdefault(cs["classroom_id"], []).append(cs)
        print(f"[OK] Found {len(class_subjects)} class_subjects")

        # Get teacher_subjects for current session
        res = await s.execute(
            text("""
                SELECT ts.id, ts.teacher_id, ts.classroom_id, ts.subject_id, ts.class_subject_id
                FROM teacher_subjects ts
                WHERE ts.academic_sessions_id = :sid
            """),
            {"sid": current_session_id},
        )
        teacher_subjects = res.mappings().all()
        ts_map = {}
        for ts in teacher_subjects:
            ts_map.setdefault(ts["classroom_id"], []).append(ts)
        print(f"[OK] Found {len(teacher_subjects)} teacher_subjects")

        # Get week_days
        res = await s.execute(text("SELECT id, day_name, day_code FROM week_days ORDER BY display_order"))
        weekdays = res.mappings().all()
        weekday_map = {w["day_name"].lower(): w["id"] for w in weekdays}
        weekday_by_code = {w["day_code"]: w["id"] for w in weekdays}
        print(f"[OK] Found {len(weekdays)} weekdays: {list(weekday_map.keys())}")

        # Get time slots
        res = await s.execute(
            text("SELECT id, slot_name, start_time, end_time FROM time_slots WHERE is_break = false ORDER BY display_order")
        )
        timeslots = res.mappings().all()
        print(f"[OK] Found {len(timeslots)} time slots")

        # Get students for each classroom
        res = await s.execute(
            text("""
                SELECT id, student_id, classroom_id
                FROM student_classes
                WHERE academic_sessions_id = :sid AND status = 'ACTIVE'
            """),
            {"sid": current_session_id},
        )
        student_classes = res.mappings().all()
        sc_by_class = {}
        for sc in student_classes:
            sc_by_class.setdefault(sc["classroom_id"], []).append(sc)
        print(f"[OK] Found {len(student_classes)} active student_class records")

        # ──────────────────────────────────────────────────
        # 1. CLASS TIMETABLE entries for each weekday this week
        # ──────────────────────────────────────────────────
        timetable_count = 0
        existing_tt = await s.execute(
            text("SELECT classroom_id, week_day_id FROM class_timetable WHERE academic_sessions_id = :sid"),
            {"sid": current_session_id},
        )
        existing_tt_set = {(r[0], r[1]) for r in existing_tt.fetchall()}

        for cl in classrooms:
            cl_id = cl["id"]
            tss = ts_map.get(cl_id, [])
            css = cs_map.get(cl_id, [])
            if not tss or not css:
                continue

            # Create timetable entries for each weekday (Mon-Sat)
            day_codes = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
            for di, day_code in enumerate(day_codes):
                wd_id = weekday_by_code.get(day_code)
                if not wd_id:
                    continue

                # Assign 4-6 periods per day, cycling through subjects
                n_periods = min(len(timeslots), len(css), len(tss))
                used_slots = set()
                for pi in range(n_periods):
                    ts_row = tss[pi % len(tss)]
                    cs_row = css[pi % len(css)]

                    # Pick a time slot not yet used today
                    slot_idx = pi % len(timeslots)
                    attempts = 0
                    while slot_idx in used_slots and attempts < len(timeslots):
                        slot_idx = (slot_idx + 1) % len(timeslots)
                        attempts += 1
                    used_slots.add(slot_idx)
                    slot = timeslots[slot_idx]

                    if (cl_id, wd_id) in existing_tt_set:
                        continue

                    await s.execute(
                        text("""
                            INSERT INTO class_timetable
                                (timetable_id, academic_sessions_id, classroom_id, class_subject_id,
                                 teacher_subject_id, week_day_id, time_slot_id, is_active, created_at, updated_at)
                            VALUES
                                (:tid, :sid, :clid, :csid, :tsid, :wdid, :slid, true, :now, :now)
                            ON CONFLICT DO NOTHING
                        """),
                        {
                            "tid": gen_id("TT", timetable_count + 1, 6),
                            "sid": current_session_id,
                            "clid": cl_id,
                            "csid": ts_row["class_subject_id"],
                            "tsid": ts_row["id"],
                            "wdid": wd_id,
                            "slid": slot["id"],
                            "now": now,
                        },
                    )
                    timetable_count += 1

        await s.commit()
        print(f"[OK] Inserted {timetable_count} class_timetable entries for this week")

        # ──────────────────────────────────────────────────
        # 2. DAILY CLASSES for today and recent days
        # ──────────────────────────────────────────────────
        dc_count = 0
        # Create daily classes for today and the past 3 weekdays
        days_to_create = [today - timedelta(days=d) for d in range(4)]
        for cl in classrooms:
            cl_id = cl["id"]
            tss = ts_map.get(cl_id, [])
            css = cs_map.get(cl_id, [])
            if not tss or not css:
                continue

            for day_date in days_to_create:
                n_classes = min(len(tss), len(css), 4)  # 4 classes per day per classroom
                for ci in range(n_classes):
                    ts_row = tss[ci % len(tss)]
                    cs_row = css[ci % len(css)]

                    daily_id = f"DC-TODAY-{cl_id}-{day_date.strftime('%Y%m%d')}-{ci}"
                    sub_name = subject_map.get(ts_row["subject_id"], "Subject")

                    # Check if already exists
                    existing = await s.execute(
                        text("SELECT id FROM daily_classes WHERE daily_class_id = :did"),
                        {"did": daily_id},
                    )
                    if existing.first():
                        continue

                    await s.execute(
                        text("""
                            INSERT INTO daily_classes
                                (daily_class_id, academic_sessions_id, classroom_id, class_subject_id,
                                 teacher_subject_id, class_date, topic, description, lecture_status,
                                 is_active, created_at, updated_at)
                            VALUES
                                (:did, :sid, :clid, :csid, :tsid, :dt, :topic, :desc, :status,
                                 true, :now, :now)
                        """),
                        {
                            "did": daily_id,
                            "sid": current_session_id,
                            "clid": cl_id,
                            "csid": ts_row["class_subject_id"],
                            "tsid": ts_row["id"],
                            "dt": day_date,
                            "topic": f"{sub_name} - Chapter {ci + 1}",
                            "desc": f"Regular {sub_name} class for {cl['display_name']}",
                            "status": "Completed" if day_date < today else "Scheduled",
                            "now": now,
                        },
                    )
                    dc_count += 1

                    # Add students for this daily class
                    dc_res = await s.execute(
                        text("SELECT id FROM daily_classes WHERE daily_class_id = :did"),
                        {"did": daily_id},
                    )
                    dc_row = dc_res.first()
                    if dc_row:
                        students = sc_by_class.get(cl_id, [])
                        for sc in students[:6]:  # Up to 6 students per class
                            attend_status = choice(["Present", "Present", "Present", "Present", "Absent", "Late"])
                            await s.execute(
                                text("""
                                    INSERT INTO daily_class_students
                                        (daily_class_id, student_class_id, attendance_status,
                                         is_late, late_minutes, is_active, created_at, updated_at)
                                    VALUES
                                        (:dcid, :scid, :status, :late, :mins, true, :now, :now)
                                    ON CONFLICT DO NOTHING
                                """),
                                {
                                    "dcid": dc_row["id"],
                                    "scid": sc["id"],
                                    "status": attend_status,
                                    "late": attend_status == "Late",
                                    "mins": randint(5, 15) if attend_status == "Late" else 0,
                                    "now": now,
                                },
                            )

        await s.commit()
        print(f"[OK] Inserted {dc_count} daily_classes for today + recent days")

        # ──────────────────────────────────────────────────
        # 3. UPCOMING ASSIGNMENTS (PUBLISHED, future dates)
        # ──────────────────────────────────────────────────
        asn_count = 0
        assignment_topics = [
            "Algebra Practice Set", "Grammar Worksheet", "Science Lab Report",
            "History Essay", "Geography Map Work", "Computer Programming Exercise",
            "Physics Numericals", "Chemistry Equations", "Hindi Composition",
            "English Literature Review", "Maths Problem Solving", "Biology Diagram",
        ]
        for cl in classrooms:
            cl_id = cl["id"]
            tss = ts_map.get(cl_id, [])
            css = cs_map.get(cl_id, [])
            if not tss or not css:
                continue

            for i in range(3):  # 3 assignments per class
                ts_row = tss[i % len(tss)]
                cs_row = css[i % len(css)]
                topic = assignment_topics[asn_count % len(assignment_topics)]

                # Check if already exists
                existing = await s.execute(
                    text("""
                        SELECT id FROM assignments
                        WHERE teacher_subject_id = :tsid
                          AND title = :title
                          AND academic_sessions_id = :sid
                    """),
                    {"tsid": ts_row["id"], "title": topic, "sid": current_session_id},
                )
                if existing.first():
                    continue

                await s.execute(
                    text("""
                        INSERT INTO assignments
                            (assignment_id, academic_sessions_id, classroom_id, class_subject_id,
                             teacher_subject_id, title, description, due_date, total_marks,
                             passing_marks, status, total_students, checked_students,
                             created_by, is_active, created_at, updated_at)
                        VALUES
                            (:aid, :sid, :clid, :csid, :tsid, :title, :desc, :due,
                             :total, :pass, :status, :total_s, :checked_s,
                             :created_by, true, :now, :now)
                    """),
                    {
                        "aid": gen_id("ASN", asn_count + 1, 8),
                        "sid": current_session_id,
                        "clid": cl_id,
                        "csid": ts_row["class_subject_id"],
                        "tsid": ts_row["id"],
                        "title": topic,
                        "desc": f"Assignment: {topic} for {cl['display_name']}",
                        "due": today + timedelta(days=randint(3, 14)),
                        "total": 50,
                        "pass": 17,
                        "status": "PUBLISHED",
                        "total_s": len(sc_by_class.get(cl_id, [])),
                        "checked_s": 0,
                        "created_by": ts_row["teacher_id"],
                        "now": now,
                    },
                )
                asn_count += 1

        await s.commit()
        print(f"[OK] Inserted {asn_count} upcoming assignments")

        # ──────────────────────────────────────────────────
        # 4. UPCOMING EXAMS (PUBLISHED, future dates)
        # ──────────────────────────────────────────────────
        exam_count = 0
        exam_names = [
            "Unit Test 1", "Unit Test 2", "Mid Term Exam", "Quarterly Exam",
            "Practice Test", "Monthly Assessment", "Pre-Final",
        ]
        for cl in classrooms:
            cl_id = cl["id"]
            tss = ts_map.get(cl_id, [])
            css = cs_map.get(cl_id, [])
            if not tss or not css:
                continue

            for i in range(2):  # 2 exams per class
                ts_row = tss[i % len(tss)]
                cs_row = css[i % len(css)]
                sub_name = subject_map.get(ts_row["subject_id"], "Subject")
                exam_name = exam_names[exam_count % len(exam_names)]

                existing = await s.execute(
                    text("""
                        SELECT id FROM exams
                        WHERE teacher_subject_id = :tsid
                          AND exam_name = :ename
                          AND academic_sessions_id = :sid
                    """),
                    {"tsid": ts_row["id"], "ename": f"{sub_name} - {exam_name}", "sid": current_session_id},
                )
                if existing.first():
                    continue

                await s.execute(
                    text("""
                        INSERT INTO exams
                            (exam_id, academic_sessions_id, classroom_id, class_subject_id,
                             teacher_subject_id, exam_name, exam_type, exam_date, total_marks,
                             passing_marks, status, total_students, is_active, created_at, updated_at)
                        VALUES
                            (:eid, :sid, :clid, :csid, :tsid, :ename, :etype, :edate,
                             :total, :pass, :status, :total_s, true, :now, :now)
                    """),
                    {
                        "eid": gen_id("EXM", exam_count + 1, 8),
                        "sid": current_session_id,
                        "clid": cl_id,
                        "csid": ts_row["class_subject_id"],
                        "tsid": ts_row["id"],
                        "ename": f"{sub_name} - {exam_name}",
                        "etype": "Theory",
                        "edate": today + timedelta(days=randint(7, 30)),
                        "total": 100,
                        "pass": 33,
                        "status": "PUBLISHED",
                        "total_s": len(sc_by_class.get(cl_id, [])),
                        "now": now,
                    },
                )
                exam_count += 1

        await s.commit()
        print(f"[OK] Inserted {exam_count} upcoming exams")

        # Summary
        res = await s.execute(
            text("""
                SELECT
                    (SELECT COUNT(*) FROM daily_classes WHERE class_date >= :today - INTERVAL '7 days'
                     AND class_date <= :today) as recent_classes,
                    (SELECT COUNT(*) FROM assignments WHERE status = 'PUBLISHED'
                     AND academic_sessions_id = :sid) as published_assignments,
                    (SELECT COUNT(*) FROM exams WHERE status = 'PUBLISHED'
                     AND academic_sessions_id = :sid) as published_exams,
                    (SELECT COUNT(*) FROM class_timetable WHERE academic_sessions_id = :sid
                     AND is_active = true) as timetable_entries
            """),
            {"today": today, "sid": current_session_id},
        )
        summary = res.mappings().first()
        print(f"\n[SUMMARY]")
        print(f"  Recent classes (last 7 days): {summary['recent_classes']}")
        print(f"  Published assignments: {summary['published_assignments']}")
        print(f"  Published exams: {summary['published_exams']}")
        print(f"  Timetable entries: {summary['timetable_entries']}")
        print(f"\n[DONE] Teacher dashboard seed data ready!")


async def main():
    try:
        await seed_teacher_dashboard()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
