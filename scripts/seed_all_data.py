"""
COMPREHENSIVE SEED SCRIPT — inserts 20-25 records into all 53 tables.
Uses SQLAlchemy Table objects so Python-level Column defaults are respected.
"""

import asyncio
import os
import sys
from datetime import date, datetime, timedelta, time, timezone
from uuid import uuid4
from decimal import Decimal
from random import randint, choice, uniform, shuffle
import bcrypt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env
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
from sqlalchemy.dialects.postgresql import insert as pg_insert

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

# Import Base metadata (module import side-effect registers every model on Base.metadata)
import src.database.base  # noqa: F401
from src.database.connection import Base

TABLES = Base.metadata.tables


# ── Helpers ──────────────────────────────────────────────────────────
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def random_date(start, end):
    return start + timedelta(days=randint(0, (end - start).days))


def gen_id(prefix, idx, digits=6):
    return f"{prefix}{idx:0{digits}d}"


def hash_pw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


async def insert_batch(s, table_name, rows):
    """Insert multiple rows with proper defaults using Table objects."""
    table = TABLES[table_name]
    for row in rows:
        compiled = pg_insert(table).values(**row).on_conflict_do_nothing()
        await s.execute(compiled)
    await s.commit()


async def insert_one(s, table_name, **row):
    """Insert a single row."""
    table = TABLES[table_name]
    compiled = pg_insert(table).values(**row).on_conflict_do_nothing()
    await s.execute(compiled)
    await s.commit()


# ── Data ─────────────────────────────────────────────────────────────
STUDENT_NAMES = [
    "Aarav Sharma",
    "Ananya Singh",
    "Arjun Patel",
    "Diya Verma",
    "Ishaan Gupta",
    "Kavya Reddy",
    "Lakshay Jain",
    "Myra Khanna",
    "Neha Joshi",
    "Om Tiwari",
    "Pari Yadav",
    "Rahul Das",
    "Sanya Mehta",
    "Tanvi Chauhan",
    "Uday Saxena",
    "Vanshika Rao",
    "Yash Agrawal",
    "Zara Khan",
    "Aryan Bose",
    "Ishita Nair",
    "Kabir Malhotra",
    "Navya Pillai",
    "Reyansh Sinha",
    "Aadhya Kumar",
    "Vihaan Roy",
]
TEACHER_NAMES = [
    "Dr. Suresh Iyer",
    "Mrs. Lakshmi Nair",
    "Mr. Rajesh Khanna",
    "Ms. Priya Menon",
    "Dr. Vivek Desai",
    "Mrs. Sunita Rao",
    "Mr. Anil Kulkarni",
    "Ms. Deepa Sharma",
    "Dr. Manoj Joshi",
    "Mrs. Kavita Mishra",
]
ADMIN_NAMES = [
    "Mr. Sanjay Gupta",
    "Mrs. Pooja Mehta",
    "Mr. Rakesh Kumar",
    "Ms. Anita Singh",
    "Dr. Amitabh Saxena",
]
PARENT_NAMES = [
    "Mr. Rajesh Kumar",
    "Mrs. Sunita Devi",
    "Mr. Amit Singh",
    "Mrs. Neha Gupta",
    "Mr. Vikram Patel",
]
SUBJECT_DATA = [
    ("MATH01", "Mathematics", "Core"),
    ("SCI01", "Science", "Core"),
    ("ENG01", "English", "Core"),
    ("HIN01", "Hindi", "Core"),
    ("SST01", "Social Studies", "Core"),
    ("COM01", "Computer Science", "Elective"),
    ("ART01", "Art & Craft", "Elective"),
    ("MUS01", "Music", "Elective"),
    ("PHE01", "Physical Education", "Core"),
    ("SNS01", "Sanskrit", "Elective"),
    ("GEC01", "General Knowledge", "Elective"),
    ("VAL01", "Value Education", "Core"),
]
CLASS_DATA = [
    ("CLS-06A", "VI-A", "Class 6", "A"),
    ("CLS-06B", "VI-B", "Class 6", "B"),
    ("CLS-07A", "VII-A", "Class 7", "A"),
    ("CLS-07B", "VII-B", "Class 7", "B"),
    ("CLS-08A", "VIII-A", "Class 8", "A"),
    ("CLS-08B", "VIII-B", "Class 8", "B"),
    ("CLS-09A", "IX-A", "Class 9", "A"),
    ("CLS-09B", "IX-B", "Class 9", "B"),
]
SESSION_DATA = [
    ("SES-2425", "2024-25", 2024, 2025),
    ("SES-2526", "2025-26", 2025, 2026),
    ("SES-2627", "2026-27", 2026, 2027),
]
WEEK_DAYS = [
    ("MON", "Monday", 1),
    ("TUE", "Tuesday", 2),
    ("WED", "Wednesday", 3),
    ("THU", "Thursday", 4),
    ("FRI", "Friday", 5),
    ("SAT", "Saturday", 6),
    ("SUN", "Sunday", 7),
]
TIME_SLOTS = [
    ("SLOT01", "Period 1", time(8, 0), time(8, 45), 45, 1, False),
    ("SLOT02", "Period 2", time(8, 45), time(9, 30), 45, 2, False),
    ("SLOT03", "Period 3", time(9, 30), time(10, 15), 45, 3, False),
    ("SLOT04", "Break", time(10, 15), time(10, 30), 15, 4, True),
    ("SLOT05", "Period 4", time(10, 30), time(11, 15), 45, 5, False),
    ("SLOT06", "Period 5", time(11, 15), time(12, 0), 45, 6, False),
    ("SLOT07", "Period 6", time(12, 0), time(12, 45), 45, 7, False),
    ("SLOT08", "Period 7", time(12, 45), time(13, 30), 45, 8, False),
]
EXAM_NAMES = [
    "Mid Term",
    "Final Exam",
    "Unit Test 1",
    "Unit Test 2",
    "Quarterly",
    "Half Yearly",
    "Pre-Board",
    "Weekly Test",
    "Monthly Assessment",
    "Practice Test",
]
NOTICE_TYPES = ["GENERAL", "ACADEMIC", "EXAM", "FEE", "EVENT"]
NOTICE_AUDIENCES = ["ALL", "CLASS", "SECTION", "TEACHER", "STUDENT"]
PROMO_TYPES = ["PROMOTED", "TRANSFERRED"]
LECTURE_STATUSES = ["Scheduled", "Completed", "Ongoing", "Cancelled"]
ATTEND_STATUSES = ["Present", "Absent", "Late", "Leave"]


# ── Main seeder ──────────────────────────────────────────────────────
async def seed_all():
    async with AsyncSessionLocal() as s:
        # Truncate all tables
        all_tables = list(TABLES.keys())
        for t in all_tables:
            if t == "alembic_version":
                continue
            await s.execute(text(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE"))
        await s.commit()
        print("[OK] All tables truncated")

        now = utcnow()
        pw = hash_pw("password@123")

        # ══════════════════════════════════════════════════════════════
        # 1. USERS (25)
        # ══════════════════════════════════════════════════════════════
        admins_data = [
            {
                "admin_id": gen_id("ADM", i + 1),
                "email": f"admin{i + 1}@school.com",
                "phone": f"9876543{i + 1:03d}",
            }
            for i in range(2)
        ]
        teachers_data = [
            {
                "teacher_id": gen_id("TEA", i + 1),
                "email": f"teacher{i + 1}@school.com",
                "phone": f"9876543{i + 3:03d}",
            }
            for i in range(4)
        ]
        students_data = [
            {
                "student_id": gen_id("STU", i + 1),
                "email": f"student{i + 1}@school.com",
                "phone": f"9876543{i + 7:03d}",
            }
            for i in range(14)
        ]
        parents_data = [
            {"email": f"parent{i + 1}@school.com", "phone": f"9876543{i + 21:03d}"}
            for i in range(5)
        ]

        all_user_rows = []
        for d in admins_data:
            r = dict(
                d,
                public_id=str(uuid4()),
                password_hash=pw,
                role="ADMIN",
                is_verified=True,
                created_at=now,
                updated_at=now,
            )
            r.setdefault("login_count", 0)
            r.setdefault("failed_login_count", 0)
            all_user_rows.append(r)
        for d in teachers_data:
            r = dict(
                d,
                public_id=str(uuid4()),
                password_hash=pw,
                role="TEACHER",
                is_verified=True,
                created_at=now,
                updated_at=now,
            )
            r.setdefault("login_count", 0)
            r.setdefault("failed_login_count", 0)
            all_user_rows.append(r)
        for d in students_data:
            r = dict(
                d,
                public_id=str(uuid4()),
                password_hash=pw,
                role="STUDENT",
                is_verified=True,
                created_at=now,
                updated_at=now,
            )
            r.setdefault("login_count", 0)
            r.setdefault("failed_login_count", 0)
            all_user_rows.append(r)
        for d in parents_data:
            r = dict(
                d,
                public_id=str(uuid4()),
                password_hash=pw,
                role="PARENT",
                is_verified=True,
                created_at=now,
                updated_at=now,
            )
            r.setdefault("login_count", 0)
            r.setdefault("failed_login_count", 0)
            all_user_rows.append(r)

        await insert_batch(s, "users", all_user_rows)
        print(f"[OK] Inserted {len(all_user_rows)} users")

        res = await s.execute(
            text(
                "SELECT id, role, student_id, teacher_id, admin_id FROM users ORDER BY id"
            )
        )
        us = res.fetchall()
        admin_ids = [r.id for r in us if r.role == "ADMIN"]
        teacher_ids = [r.id for r in us if r.role == "TEACHER"]
        student_ids = [r.id for r in us if r.role == "STUDENT"]
        [r.id for r in us if r.role == "PARENT"]

        # ══════════════════════════════════════════════════════════════
        # 2. ACADEMIC SESSIONS (3)
        # ══════════════════════════════════════════════════════════════
        sessions = []
        for sc, sn, sy, ey in SESSION_DATA:
            sessions.append(
                {
                    "session_code": sc,
                    "session_name": sn,
                    "start_year": sy,
                    "end_year": ey,
                    "start_date": date(sy, 4, 1),
                    "end_date": date(ey, 3, 31),
                    "is_current": sy == 2025,
                    "created_at": now,
                    "updated_at": now,
                }
            )
        await insert_batch(s, "academic_sessions", sessions)
        print(f"[OK] Inserted {len(sessions)} academic sessions")

        res_s = await s.execute(
            text("SELECT id, session_code FROM academic_sessions ORDER BY id")
        )
        sess_rows = res_s.fetchall()
        session_ids_all = [r.id for r in sess_rows]
        current_sess_id = [r.id for r in sess_rows if r.session_code == "SES-2526"][0]

        # ══════════════════════════════════════════════════════════════
        # 3. CLASSROOM (8)
        # ══════════════════════════════════════════════════════════════
        classrooms = []
        for cc, dn, cn, sec in CLASS_DATA:
            classrooms.append(
                {
                    "class_code": cc,
                    "class_name": cn,
                    "section": sec,
                    "display_name": dn,
                    "academic_sessions_id": choice(session_ids_all),
                    "created_at": now,
                    "updated_at": now,
                }
            )
        await insert_batch(s, "classroom", classrooms)
        print(f"[OK] Inserted {len(classrooms)} classrooms")
        res_c = await s.execute(
            text(
                "SELECT id, class_code, academic_sessions_id FROM classroom ORDER BY id"
            )
        )
        cl_rows = res_c.fetchall()
        cl_ids = [r.id for r in cl_rows]

        # ══════════════════════════════════════════════════════════════
        # 4. SUBJECTS (12)
        # ══════════════════════════════════════════════════════════════
        subjects = [
            {
                "subject_code": sc,
                "subject_name": sn,
                "subject_type": st,
                "display_order": i + 1,
                "created_at": now,
                "updated_at": now,
            }
            for i, (sc, sn, st) in enumerate(SUBJECT_DATA)
        ]
        await insert_batch(s, "subjects", subjects)
        print(f"[OK] Inserted {len(subjects)} subjects")
        res_sub = await s.execute(
            text("SELECT id, subject_name FROM subjects ORDER BY id")
        )
        sub_rows = res_sub.fetchall()
        [r.id for r in sub_rows]

        # ════════════════════════════════════════════════════════════════
        # 5. CLASS_SUBJECTS
        # ════════════════════════════════════════════════════════════════
        cs_rows = []
        for cl in cl_rows:
            for sub in sub_rows:
                cs_rows.append(
                    {
                        "academic_sessions_id": choice(session_ids_all),
                        "classroom_id": cl.id,
                        "subject_id": sub.id,
                        "display_order": len(cs_rows) + 1,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
        await insert_batch(s, "class_subjects", cs_rows)
        print(f"[OK] Inserted {len(cs_rows)} class_subjects")
        res_cs = await s.execute(
            text(
                "SELECT id, classroom_id, subject_id, academic_sessions_id FROM class_subjects ORDER BY id"
            )
        )
        cs_all = res_cs.fetchall()

        # ════════════════════════════════════════════════════════════════
        # 6. PROFILES
        # ════════════════════════════════════════════════════════════════
        for i, uid in enumerate(admin_ids[:2]):
            await insert_one(
                s,
                "admin_profiles",
                public_id=str(uuid4()),
                user_id=uid,
                admin_name=ADMIN_NAMES[i],
                department=choice(["Administration", "Academic", "Finance"]),
                is_super_admin=(i == 0),
                created_at=now,
                updated_at=now,
            )
        for i, uid in enumerate(teacher_ids[:4]):
            await insert_one(
                s,
                "teacher_profiles",
                public_id=str(uuid4()),
                user_id=uid,
                teacher_name=TEACHER_NAMES[i],
                gender=choice(["MALE", "FEMALE"]),
                employee_code=f"EMP{1001 + i}",
                designation=choice(
                    [
                        "Senior Teacher",
                        "Junior Teacher",
                        "Head of Department",
                        "Lab Instructor",
                    ]
                ),
                department=choice(["Science", "Mathematics", "Languages", "Arts"]),
                experience_years=round(uniform(2, 15), 1),
                created_at=now,
                updated_at=now,
            )
        for i, uid in enumerate(student_ids[:14]):
            await insert_one(
                s,
                "student_profiles",
                public_id=str(uuid4()),
                user_id=uid,
                admission_number=f"ADM{2024001 + i}",
                registration_number=f"REG{2024001 + i}",
                student_name=STUDENT_NAMES[i],
                gender=choice(["MALE", "FEMALE", "OTHER"]),
                date_of_birth=random_date(date(2008, 1, 1), date(2012, 12, 31)),
                blood_group=choice(["A+", "B+", "O+", "AB+", "A-"]),
                address=f"{randint(1, 999)} Main Street",
                city=choice(["Mumbai", "Delhi", "Bangalore", "Pune", "Chennai"]),
                state=choice(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu"]),
                parent_name=choice(PARENT_NAMES),
                parent_phone=f"9876543{randint(100, 999)}",
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted profiles (admin, teacher, student)")

        res_sp = await s.execute(
            text("SELECT id, user_id FROM student_profiles ORDER BY id")
        )
        sp_rows = res_sp.fetchall()

        # ════════════════════════════════════════════════════════════════
        # 7. WEEK DAYS (7)
        # ════════════════════════════════════════════════════════════════
        days = [
            {
                "day_code": dc,
                "day_name": dn,
                "display_order": do,
                "created_at": now,
                "updated_at": now,
            }
            for dc, dn, do in WEEK_DAYS
        ]
        await insert_batch(s, "week_days", days)
        res_wd = await s.execute(text("SELECT id FROM week_days ORDER BY id"))
        wd_ids = [r.id for r in res_wd.fetchall()]
        print("[OK] Inserted week days")

        # ════════════════════════════════════════════════════════════════
        # 8. TIME SLOTS (8)
        # ════════════════════════════════════════════════════════════════
        slots = [
            {
                "slot_code": sc,
                "slot_name": sn,
                "start_time": st,
                "end_time": et,
                "duration_minutes": dur,
                "display_order": do,
                "is_break": brk,
                "created_at": now,
                "updated_at": now,
            }
            for sc, sn, st, et, dur, do, brk in TIME_SLOTS
        ]
        await insert_batch(s, "time_slots", slots)
        res_ts = await s.execute(text("SELECT id FROM time_slots ORDER BY id"))
        ts_ids = [r.id for r in res_ts.fetchall()]
        print("[OK] Inserted time slots")

        # ════════════════════════════════════════════════════════════════
        # 9. TEACHER_SUBJECTS (ensure unique (session, class, subject) per teacher)
        # ════════════════════════════════════════════════════════════════
        ts_teach_rows = []
        used_combos = set()
        for tid in teacher_ids[:4]:
            count = 0
            shuffled = cs_all.copy()
            shuffle(shuffled)
            for cs in shuffled:
                key = (cs.academic_sessions_id, cs.classroom_id, cs.subject_id)
                if key not in used_combos:
                    used_combos.add(key)
                    ts_teach_rows.append(
                        {
                            "academic_sessions_id": cs.academic_sessions_id,
                            "class_subject_id": cs.id,
                            "classroom_id": cs.classroom_id,
                            "subject_id": cs.subject_id,
                            "teacher_id": tid,
                            "is_class_teacher": len(ts_teach_rows) < 4,
                            "created_at": now,
                            "updated_at": now,
                        }
                    )
                    count += 1
                    if count >= 6:
                        break
        await insert_batch(s, "teacher_subjects", ts_teach_rows)
        print(f"[OK] Inserted {len(ts_teach_rows)} teacher_subjects")
        res_ts_t = await s.execute(
            text("""
            SELECT id, teacher_id, class_subject_id, classroom_id, subject_id, academic_sessions_id
            FROM teacher_subjects ORDER BY id
        """)
        )
        ts_t_rows = res_ts_t.fetchall()

        # ════════════════════════════════════════════════════════════════
        # 10. STUDENT_CLASSES (ensure unique roll per class per session)
        # ════════════════════════════════════════════════════════════════
        stuclass = []
        roll_tracker = {}  # (sess_id, classroom_id) -> set of roll_numbers
        for i, uid in enumerate(student_ids[:14]):
            cl = choice(cl_rows)
            key = (cl.academic_sessions_id, cl.id)
            if key not in roll_tracker:
                roll_tracker[key] = set()
            used_rolls = roll_tracker[key]
            rn = randint(1, 40)
            while rn in used_rolls:
                rn = randint(1, 40)
            used_rolls.add(rn)
            stuclass.append(
                {
                    "academic_sessions_id": cl.academic_sessions_id,
                    "student_id": uid,
                    "classroom_id": cl.id,
                    "roll_number": rn,
                    "admission_date": random_date(date(2024, 6, 1), date(2024, 7, 31)),
                    "created_at": now,
                    "updated_at": now,
                }
            )
        await insert_batch(s, "student_classes", stuclass)
        print(f"[OK] Inserted {len(stuclass)} student_classes")
        res_sc = await s.execute(
            text(
                "SELECT id, student_id, classroom_id, academic_sessions_id FROM student_classes ORDER BY id"
            )
        )
        sc_rows = res_sc.fetchall()

        # ════════════════════════════════════════════════════════════════
        # 11-13. TIMETABLE, AVAILABILITY, DAILY CLASSES
        # ════════════════════════════════════════════════════════════════
        timetable = []
        for i in range(20):
            ts_row = choice(ts_t_rows)
            timetable.append(
                {
                    "timetable_id": gen_id("TT", i + 1),
                    "academic_sessions_id": ts_row.academic_sessions_id,
                    "classroom_id": ts_row.classroom_id,
                    "class_subject_id": ts_row.class_subject_id,
                    "teacher_subject_id": ts_row.id,
                    "week_day_id": choice(wd_ids),
                    "time_slot_id": choice(ts_ids),
                    "room_number": f"Room {randint(101, 305)}",
                    "created_at": now,
                    "updated_at": now,
                }
            )
        await insert_batch(s, "class_timetable", timetable)
        print(f"[OK] Inserted {len(timetable)} timetable entries")
        res_tt = await s.execute(text("SELECT id FROM class_timetable ORDER BY id"))
        tt_ids = [r.id for r in res_tt.fetchall()]

        # Teacher availability
        for i in range(20):
            ts_row = choice(ts_t_rows)
            await insert_one(
                s,
                "teacher_availability",
                availability_id=gen_id("TA", i + 1),
                academic_sessions_id=ts_row.academic_sessions_id,
                teacher_subject_id=ts_row.id,
                week_day_id=choice(wd_ids),
                time_slot_id=choice(ts_ids),
                is_available=choice([True, True, True, False]),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted teacher_availability")

        # Daily classes
        dcs = []
        for i in range(25):
            ts_row = choice(ts_t_rows)
            dcs.append(
                {
                    "daily_class_id": gen_id("DCL", i + 1, 4),
                    "academic_sessions_id": ts_row.academic_sessions_id,
                    "classroom_id": ts_row.classroom_id,
                    "class_subject_id": ts_row.class_subject_id,
                    "teacher_subject_id": ts_row.id,
                    "timetable_id": choice(tt_ids) if tt_ids else None,
                    "class_date": random_date(date(2025, 7, 1), date(2025, 9, 30)),
                    "topic": f"Chapter {randint(1, 15)}: Lesson {randint(1, 5)}",
                    "lecture_status": choice(LECTURE_STATUSES),
                    "created_at": now,
                    "updated_at": now,
                }
            )
        await insert_batch(s, "daily_classes", dcs)
        print(f"[OK] Inserted {len(dcs)} daily_classes")
        res_dc = await s.execute(text("SELECT id FROM daily_classes ORDER BY id"))
        dc_ids = [r.id for r in res_dc.fetchall()]

        # ════════════════════════════════════════════════════════════════
        # 14-15. DAILY CLASS STUDENTS + STUDENT ATTENDANCE
        # ════════════════════════════════════════════════════════════════
        dcs_count = 0
        for dcid in dc_ids:
            used_student_classes = set()
            for _ in range(randint(1, 3)):
                sc = choice(sc_rows)
                while sc.id in used_student_classes:
                    sc = choice(sc_rows)
                used_student_classes.add(sc.id)
                dcs_count += 1
                await insert_one(
                    s,
                    "daily_class_students",
                    daily_class_id=dcid,
                    student_class_id=sc.id,
                    attendance_status=choice(ATTEND_STATUSES),
                    marked_at=now,
                    created_at=now,
                    updated_at=now,
                )
        print(f"[OK] Inserted {dcs_count} daily_class_students")

        for sc in sc_rows:
            total = randint(40, 60)
            present = randint(total - 15, total)
            await insert_one(
                s,
                "student_attendance",
                student_class_id=sc.id,
                total_classes=total,
                present_classes=present,
                absent_classes=total - present,
                attendance_percentage=round((present / total) * 100, 2),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted student_attendance")

        # ════════════════════════════════════════════════════════════════
        # 16. FEES
        # ════════════════════════════════════════════════════════════════
        fee_count = 0
        fee_tracker = set()
        for sc in sc_rows:
            for month in range(4, 8):
                fee_key = (sc.id, month, 2025)
                if fee_key in fee_tracker:
                    continue
                fee_tracker.add(fee_key)
                fee_count += 1
                amt = Decimal(str(round(uniform(1000, 5000), 2)))
                paid = amt if choice([True, False]) else Decimal("0.00")
                fine = Decimal("0.00")
                status = "PAID" if paid == amt else choice(["PENDING", "OVERDUE"])
                if status == "OVERDUE":
                    fine = Decimal(str(round(uniform(50, 200), 2)))
                await insert_one(
                    s,
                    "fees",
                    fee_id=gen_id("FEE", fee_count, 8),
                    academic_sessions_id=current_sess_id,
                    student_class_id=sc.id,
                    fee_month=month,
                    fee_year=2025,
                    total_amount=amt,
                    paid_amount=paid,
                    fine_amount=fine,
                    due_date=date(2025, month, 15),
                    paid_date=date(2025, month, randint(1, 14))
                    if paid == amt
                    else None,
                    status=status,
                    created_by=choice(admin_ids),
                    created_at=now,
                    updated_at=now,
                )
        print(f"[OK] Inserted {fee_count} fees")

        # ════════════════════════════════════════════════════════════════
        # 17-18. EXAMS + RESULTS
        # ════════════════════════════════════════════════════════════════
        for i in range(25):
            ts_row = choice(ts_t_rows)
            total_marks = choice([25, 50, 80, 100])
            await insert_one(
                s,
                "exams",
                exam_id=gen_id("EXM", i + 1, 8),
                academic_sessions_id=ts_row.academic_sessions_id,
                classroom_id=ts_row.classroom_id,
                class_subject_id=ts_row.class_subject_id,
                teacher_subject_id=ts_row.id,
                exam_name=choice(EXAM_NAMES),
                exam_type=choice(["Theory", "Practical", "Oral", "Project"]),
                exam_date=random_date(date(2025, 7, 1), date(2025, 9, 30)),
                total_marks=total_marks,
                passing_marks=total_marks // 2,
                status=choice(["DRAFT", "PUBLISHED", "COMPLETED", "CANCELLED"]),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted 25 exams")

        res_ex = await s.execute(text("SELECT id, total_marks FROM exams ORDER BY id"))
        ex_rows = res_ex.fetchall()
        for ex in ex_rows:
            used_sc = set()
            for _ in range(randint(1, 3)):
                sc = choice(sc_rows)
                while sc.id in used_sc:
                    sc = choice(sc_rows)
                used_sc.add(sc.id)
                obt = round(uniform(0, float(ex.total_marks)), 2)
                pct = round((obt / ex.total_marks) * 100, 2)
                await insert_one(
                    s,
                    "exam_results",
                    exam_id=ex.id,
                    student_class_id=sc.id,
                    obtained_marks=obt,
                    percentage=pct,
                    grade="A"
                    if pct >= 80
                    else "B"
                    if pct >= 60
                    else "C"
                    if pct >= 35
                    else "F",
                    is_absent=choice([False, False, False, True]),
                    checked_at=now,
                    created_at=now,
                    updated_at=now,
                )
        print("[OK] Inserted exam results")

        # ════════════════════════════════════════════════════════════════
        # 19-20. ASSIGNMENTS + RESULTS
        # ════════════════════════════════════════════════════════════════
        for i in range(25):
            ts_row = choice(ts_t_rows)
            total_marks = choice([10, 20, 25, 50])
            await insert_one(
                s,
                "assignments",
                assignment_id=gen_id("ASN", i + 1, 8),
                academic_sessions_id=ts_row.academic_sessions_id,
                classroom_id=ts_row.classroom_id,
                class_subject_id=ts_row.class_subject_id,
                teacher_subject_id=ts_row.id,
                title=f"Assignment {i + 1}: {choice(['Algebra', 'Grammar', 'Motion', 'Periodic Table', 'Geography', 'Civics', 'Programming', 'Drawing'])}",
                due_date=random_date(date(2025, 7, 1), date(2025, 9, 30)),
                total_marks=total_marks,
                passing_marks=total_marks // 2,
                status=choice(["DRAFT", "PUBLISHED", "CLOSED"]),
                created_by=choice(teacher_ids),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted 25 assignments")

        res_asn = await s.execute(
            text("SELECT id, total_marks FROM assignments ORDER BY id")
        )
        asn_rows = res_asn.fetchall()
        for asn in asn_rows:
            used_sc = set()
            for _ in range(randint(1, 3)):
                sc = choice(sc_rows)
                while sc.id in used_sc:
                    sc = choice(sc_rows)
                used_sc.add(sc.id)
                obt = round(uniform(0, float(asn.total_marks)), 2)
                pct = round((obt / asn.total_marks) * 100, 2)
                await insert_one(
                    s,
                    "assignment_results",
                    assignment_id=asn.id,
                    student_class_id=sc.id,
                    obtained_marks=obt,
                    percentage=pct,
                    grade="A" if pct >= 80 else "B" if pct >= 60 else "C",
                    is_checked=True,
                    checked_at=now,
                    created_at=now,
                    updated_at=now,
                )
        print("[OK] Inserted assignment results")

        # ════════════════════════════════════════════════════════════════
        # 21. STUDY MATERIALS (25)
        # ════════════════════════════════════════════════════════════════
        for i in range(25):
            ts_row = choice(ts_t_rows)
            await insert_one(
                s,
                "study_materials",
                material_id=gen_id("MAT", i + 1, 8),
                academic_sessions_id=ts_row.academic_sessions_id,
                classroom_id=ts_row.classroom_id,
                class_subject_id=ts_row.class_subject_id,
                teacher_subject_id=ts_row.id,
                title=f"Chapter {randint(1, 15)} Notes - {choice(['Math', 'Science', 'English', 'Hindi', 'SST'])}",
                material_type=choice(["PDF", "VIDEO", "DOCUMENT", "LINK"]),
                file_name=f"chapter_{randint(1, 15)}.pdf",
                file_url=f"https://storage.school.com/materials/{gen_id('MAT', i + 1, 8)}.pdf",
                uploaded_by=choice(teacher_ids),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted 25 study materials")

        # ════════════════════════════════════════════════════════════════
        # 22. NOTICES (25)
        # ════════════════════════════════════════════════════════════════
        for i in range(25):
            pub = random_date(date(2025, 6, 1), date(2025, 9, 30))
            await insert_one(
                s,
                "notices",
                notice_id=gen_id("NOT", i + 1, 8),
                academic_sessions_id=choice(session_ids_all),
                classroom_id=choice(cl_ids + [None]),
                title=f"{choice(['Holiday', 'Exam Schedule', 'PTM', 'Event', 'Fee Reminder', 'Sports Day', 'Workshop', 'Field Trip'])} - {i + 1}",
                description=f"This notice is about {choice(['upcoming exams', 'school holiday', 'parent-teacher meeting', 'annual event', 'fee payment', 'sports day', 'educational workshop', 'field trip'])}.",
                notice_type=choice(NOTICE_TYPES),
                audience=choice(NOTICE_AUDIENCES),
                publish_date=pub,
                expiry_date=pub + timedelta(days=randint(7, 30)),
                is_pinned=choice([True, False]),
                created_by=choice(admin_ids),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted 25 notices")

        # ════════════════════════════════════════════════════════════════
        # 23-24. CHAT ROOMS + MESSAGES
        # ════════════════════════════════════════════════════════════════
        cr_db_ids = []
        for i in range(20):
            sc = choice(sc_rows)
            ts_row = choice(ts_t_rows)
            cr_id_ = gen_id("CHT", i + 1, 8)
            await insert_one(
                s,
                "chat_rooms",
                chat_room_id=cr_id_,
                academic_sessions_id=sc.academic_sessions_id,
                student_class_id=sc.id,
                teacher_subject_id=ts_row.id,
                last_message=f"Hello, I have a question about {choice(['homework', 'exam', 'chapter 5', 'assignment'])}",
                last_message_at=now - timedelta(hours=randint(1, 72)),
                student_unread=randint(0, 5),
                teacher_unread=randint(0, 3),
                created_at=now,
                updated_at=now,
            )
        res_cr = await s.execute(text("SELECT id FROM chat_rooms ORDER BY id"))
        cr_db_ids = [r.id for r in res_cr.fetchall()]
        msg_count = 0
        for crid in cr_db_ids:
            for _ in range(randint(1, 4)):
                msg_count += 1
                await insert_one(
                    s,
                    "chat_messages",
                    chat_room_id=crid,
                    sender_id=choice(student_ids + teacher_ids),
                    message=f"Message {msg_count}: {choice(['Help me with homework', 'When is the exam?', 'Good morning sir', 'Please check my assignment', 'Thank you'])}",
                    created_at=now,
                    updated_at=now,
                )
        print(f"[OK] Inserted {msg_count} chat messages")

        # ════════════════════════════════════════════════════════════════
        # 25. STUDENT ID CARDS
        # ════════════════════════════════════════════════════════════════
        for i, sp in enumerate(sp_rows):
            await insert_one(
                s,
                "student_id_cards",
                student_profile_id=sp.id,
                academic_sessions_id=current_sess_id,
                student_name=STUDENT_NAMES[i],
                parent_name=choice(PARENT_NAMES),
                class_display_name=choice([cd[1] for cd in CLASS_DATA]),
                institute_name="Springfield International School",
                institute_contact_number="1800-123-4567",
                academic_session_label="2025-26",
                student_id_business=gen_id("STU", i + 1),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted student ID cards")

        # ════════════════════════════════════════════════════════════════
        # 26-27. OTP + REVOKED TOKENS
        # ════════════════════════════════════════════════════════════════
        for i in range(20):
            u = choice(us)
            code_hash = hash_pw(str(randint(100000, 999999)))
            await insert_one(
                s,
                "otp_codes",
                user_id=u.id,
                code_hash=code_hash,
                purpose=choice(["email_verify", "login"]),
                expires_at=now + timedelta(minutes=15),
                is_used=choice([True, False]),
            )
        for i in range(20):
            await insert_one(
                s,
                "revoked_tokens",
                jti=str(uuid4()),
                expires_at=now + timedelta(days=randint(1, 7)),
            )
        print("[OK] Inserted OTP codes and revoked tokens")

        # ════════════════════════════════════════════════════════════════
        # 28-32. KHAN ACADEMY (topics, activities, progress)
        # ════════════════════════════════════════════════════════════════
        for i in range(25):
            sub = choice(sub_rows)
            await insert_one(
                s,
                "ka_topics",
                topic_id=gen_id("TPC", i + 1, 8),
                ka_topic_id=f"ka_{uuid4().hex[:8]}",
                topic_name=f"Topic {i + 1}: {choice(['Algebra Basics', 'Cell Structure', 'Grammar Rules', 'Ancient History', 'Programming Loops', 'Chemical Reactions', 'Poetry Analysis', 'Maps & Globe', 'Data Structures', 'Trigonometry'])}",
                display_order=i + 1,
                subject_id=sub.id,
                classroom_id=choice(cl_ids),
                created_at=now,
                updated_at=now,
            )
        res_kt = await s.execute(
            text("SELECT id, subject_id FROM ka_topics ORDER BY id")
        )
        kt_rows = res_kt.fetchall()

        for i in range(20):
            sp = choice(sp_rows)
            from_d = random_date(date(2025, 6, 1), date(2025, 8, 31))
            to_d = from_d + timedelta(days=randint(1, 14))
            await insert_one(
                s,
                "ka_student_activities",
                student_profile_id=sp.id,
                from_date=from_d,
                to_date=to_d,
                worked_on=randint(1, 20),
                attempted=randint(1, 15),
                familiar=randint(0, 10),
                proficient=randint(0, 10),
                leveled_to_proficient=randint(0, 5),
                leveled_up=randint(0, 5),
                mastered=randint(0, 5),
                minutes=randint(10, 120),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted KA data (topics + student activities)")

        for i in range(25):
            sp = choice(sp_rows)
            kt = choice(kt_rows)
            await insert_one(
                s,
                "ka_subject_activities",
                student_profile_id=sp.id,
                subject_id=kt.subject_id,
                topic_id=kt.id,
                activity_date=random_date(date(2025, 7, 1), date(2025, 9, 30)),
                created_at=now,
                updated_at=now,
            )

        for i in range(25):
            sp = choice(sp_rows)
            sub = choice(sub_rows)
            avail = randint(50, 200)
            earned = randint(0, avail)
            await insert_one(
                s,
                "ka_subject_progress",
                student_profile_id=sp.id,
                subject_id=sub.id,
                point_available=avail,
                point_earned=earned,
                percentage_earned=round((earned / avail) * 100, 2) if avail else 0,
                snapshot_date=random_date(date(2025, 7, 1), date(2025, 9, 30)),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted KA subject activities + progress")

        res_ksp = await s.execute(
            text("SELECT id FROM ka_subject_progress ORDER BY id")
        )
        ksp_ids = [r.id for r in res_ksp.fetchall()]

        for i in range(25):
            sp = choice(sp_rows)
            kt = choice(kt_rows)
            avail = randint(20, 100)
            earned = randint(0, avail)
            await insert_one(
                s,
                "ka_topic_progress",
                student_profile_id=sp.id,
                subject_id=kt.subject_id,
                topic_id=kt.id,
                point_available=avail,
                point_earned=earned,
                percentage_earned=round((earned / avail) * 100, 2) if avail else 0,
                snapshot_date=random_date(date(2025, 7, 1), date(2025, 9, 30)),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted KA topic progress")

        res_ktp = await s.execute(text("SELECT id FROM ka_topic_progress ORDER BY id"))
        ktp_ids = [r.id for r in res_ktp.fetchall()]

        # ════════════════════════════════════════════════════════════════
        # 33. ATTACHMENTS (20)
        # ════════════════════════════════════════════════════════════════
        for i in range(20):
            await insert_one(
                s,
                "attachments",
                attachment_code=f"ATT{i + 1:06d}",
                entity_type=choice(["assignment", "study_material", "notice", "exam"]),
                entity_id=randint(1, 25),
                file_name=f"file_{i + 1}.pdf",
                mime_type="application/pdf",
                file_size=randint(1024, 1048576),
                file_data=bytes(randint(0, 255) for _ in range(100)),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted 20 attachments")

        # ════════════════════════════════════════════════════════════════
        # 34-39. ZOOM
        # ════════════════════════════════════════════════════════════════
        z_uuids = []
        for i in range(10):
            muid = str(uuid4())
            z_uuids.append(muid)
            start = now - timedelta(days=randint(1, 60), hours=randint(1, 12))
            await insert_one(
                s,
                "zoom_meetings",
                uuid=muid,
                meeting_id=randint(10000000000, 99999999999),
                topic=f"{choice(['Math Class', 'Science Lab', 'English Literature', 'Hindi Grammar', 'SST Lecture'])} - {i + 1}",
                type=choice([1, 2, 3]),
                start_time=start,
                timezone="Asia/Kolkata",
                duration=randint(30, 90),
                total_size=randint(50000000, 500000000),
                recording_count=randint(0, 3),
                share_url=f"https://zoom.us/rec/share/{uuid4().hex[:12]}",
                created_at=now,
                updated_at=now,
            )
        zrf_ids = []
        for i in range(20):
            rfid = str(uuid4())
            zrf_ids.append(rfid)
            rstart = now - timedelta(days=randint(1, 30))
            await insert_one(
                s,
                "zoom_recording_files",
                id=rfid,
                meeting_uuid=choice(z_uuids),
                recording_start=rstart,
                recording_end=rstart + timedelta(minutes=randint(30, 90)),
                file_type=choice(["MP4", "M4A", "TRANSCRIPT", "CHAT"]),
                file_extension=choice([".mp4", ".m4a", ".txt", ".json"]),
                file_size=randint(10000000, 500000000),
                recording_type=choice(
                    [
                        "shared_screen_with_speaker_view",
                        "shared_screen",
                        "audio_only",
                        "audio_transcript",
                    ]
                ),
                play_url=f"https://zoom.us/play/{uuid4().hex[:12]}",
                download_url=f"https://zoom.us/download/{uuid4().hex[:12]}",
                status=choice(["completed", "processing", "failed"]),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted zoom meetings + recording files")

        for i in range(30):
            rfid = choice(zrf_ids)
            await insert_one(
                s,
                "zoom_transcripts",
                recording_file_id=rfid,
                segment_index=i,
                start_time=f"00:{randint(0, 59):02d}:{randint(0, 59):02d}.{randint(0, 999):03d}",
                end_time=f"00:{randint(0, 59):02d}:{randint(0, 59):02d}.{randint(0, 999):03d}",
                duration=round(uniform(5, 60), 3),
                speaker=choice(TEACHER_NAMES + STUDENT_NAMES),
                text=f"Sample transcript segment {i}.",
                class_name=choice(["Class 6A", "Class 7B", "Class 8A", "Class 9B"]),
                class_date=random_date(date(2025, 6, 1), date(2025, 9, 30)),
                file_name=f"transcript_{i + 1}.json",
                created_at=now,
                updated_at=now,
            )
        for i in range(25):
            rfid = choice(zrf_ids)
            await insert_one(
                s,
                "zoom_student_interactions",
                recording_file_id=rfid,
                class_date=random_date(date(2025, 6, 1), date(2025, 9, 30)),
                class_name=choice(["Class 6A", "Class 7B", "Class 8A", "Class 9B"]),
                interaction_time=f"00:{randint(0, 59):02d}:{randint(0, 59):02d}",
                interaction_duration=round(uniform(5, 120), 2),
                speaker_name=choice(STUDENT_NAMES),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted zoom transcripts + interactions")

        for i in range(30):
            muid = choice(z_uuids)
            join = now - timedelta(days=randint(1, 30))
            dur_sec = randint(300, 5400)
            await insert_one(
                s,
                "zoom_participants",
                meeting_uuid=muid,
                zoom_participant_id=str(uuid4()),
                name=choice(TEACHER_NAMES + STUDENT_NAMES),
                user_email=f"participant{i + 1}@school.com",
                join_time=join,
                leave_time=join + timedelta(seconds=dur_sec),
                meeting_date=join.date(),
                duration_seconds=dur_sec,
                duration_minutes=round(dur_sec / 60),
                status=choice(["in_meeting", "left", "waiting"]),
                created_at=now,
                updated_at=now,
            )
        for i in range(20):
            await insert_one(
                s,
                "zoom_files",
                zoom_file_code=gen_id("ZMF", i + 1, 8),
                file_initial=f"CLASS_{chr(65 + i)}",
                raw_date=f"2025-{randint(6, 9):02d}-{randint(1, 30):02d}",
                raw_time=f"{randint(8, 16):02d}:{randint(0, 59):02d}:{randint(0, 59):02d}",
                date=f"2025-{randint(6, 9):02d}-{randint(1, 30):02d}",
                time=f"{randint(8, 16):02d}:{randint(0, 59):02d}",
                recording_file_id=choice(zrf_ids),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted zoom participants + files")

        # ════════════════════════════════════════════════════════════════
        # 40-43. PROCESSED + RAW MEETINGS
        # ════════════════════════════════════════════════════════════════
        pm_ids = []
        for i in range(10):
            m_start = now - timedelta(days=randint(1, 30))
            await insert_one(
                s,
                "processed_meetings",
                meeting_id=str(randint(10000000000, 99999999999)),
                uuid=choice(z_uuids),
                topic=f"Processed Meeting {i + 1}",
                start_time=m_start,
                end_time=m_start + timedelta(minutes=randint(30, 90)),
                meeting_date=m_start.date(),
                duration_minutes=randint(30, 90),
                participants_count=randint(5, 30),
                created_at=now,
                updated_at=now,
            )
        res_pm = await s.execute(text("SELECT id FROM processed_meetings ORDER BY id"))
        pm_ids = [r.id for r in res_pm.fetchall()]
        for i in range(25):
            await insert_one(
                s,
                "processed_participants",
                meeting_id_fk=choice(pm_ids),
                name=choice(STUDENT_NAMES + TEACHER_NAMES),
                user_email=f"proc_p{i + 1}@school.com",
                join_time=now - timedelta(days=randint(1, 30)),
                leave_time=now - timedelta(days=randint(0, 29)),
                meeting_date=random_date(date(2025, 6, 1), date(2025, 9, 30)),
                duration_seconds=randint(300, 5400),
                duration_minutes=randint(5, 90),
                status=choice(["in_meeting", "left"]),
                created_at=now,
                updated_at=now,
            )

        rm_ids = []
        for i in range(10):
            m_start = now - timedelta(days=randint(1, 60))
            await insert_one(
                s,
                "raw_meetings",
                meeting_id=str(randint(10000000000, 99999999999)),
                uuid=str(uuid4()),
                topic=f"Raw Meeting {i + 1}",
                start_time=m_start,
                end_time=m_start + timedelta(minutes=randint(30, 90)),
                duration_minutes=randint(30, 90),
                participants_count=randint(5, 25),
                created_at=now,
                updated_at=now,
            )
        res_rm = await s.execute(text("SELECT id FROM raw_meetings ORDER BY id"))
        rm_ids = [r.id for r in res_rm.fetchall()]
        for i in range(25):
            await insert_one(
                s,
                "raw_participants",
                meeting_id_fk=choice(rm_ids),
                name=choice(STUDENT_NAMES + TEACHER_NAMES),
                user_email=f"raw_p{i + 1}@school.com",
                join_time=now - timedelta(days=randint(1, 30)),
                leave_time=now - timedelta(days=randint(0, 29)),
                duration_seconds=randint(300, 5400),
                status=choice(["in_meeting", "left", "waiting"]),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted processed + raw meetings")

        # ════════════════════════════════════════════════════════════════
        # 44-49. REPORTS
        # ════════════════════════════════════════════════════════════════
        rep_ids = []
        for i in range(20):
            sp = choice(sp_rows)
            sd = random_date(date(2025, 4, 1), date(2025, 6, 30))
            ed = sd + timedelta(days=randint(15, 45))
            await insert_one(
                s,
                "student_reports",
                student_profile_id=sp.id,
                report_date=ed + timedelta(days=randint(1, 5)),
                data_start_date=sd,
                data_end_date=ed,
                created_at=now,
                updated_at=now,
            )
        res_rep = await s.execute(text("SELECT id FROM student_reports ORDER BY id"))
        rep_ids = [r.id for r in res_rep.fetchall()]

        for rid in rep_ids:
            await insert_one(
                s,
                "student_activity_reports",
                report_id=rid,
                mean_duration_minutes=randint(20, 60),
                total_duration_minutes=randint(200, 2000),
                total_worked_hours=randint(5, 40),
                total_attempted=randint(10, 100),
                total_familiar=randint(5, 50),
                total_proficient=randint(5, 50),
                total_leveled_up=randint(0, 20),
                total_mastered=randint(0, 15),
                created_at=now,
                updated_at=now,
            )
            for _ in range(randint(1, 3)):
                sub = choice(sub_rows)
                await insert_one(
                    s,
                    "student_subject_progress_reports",
                    report_id=rid,
                    subject_id=sub.id,
                    subject_progress_id=choice(ksp_ids) if ksp_ids else None,
                    created_at=now,
                    updated_at=now,
                )
            for _ in range(randint(1, 3)):
                kt = choice(kt_rows)
                await insert_one(
                    s,
                    "student_topic_progress_reports",
                    report_id=rid,
                    topic_id=kt.id,
                    topic_progress_id=choice(ktp_ids) if ktp_ids else None,
                    created_at=now,
                    updated_at=now,
                )
            await insert_one(
                s,
                "zoom_duration_reports",
                report_id=rid,
                mean_duration_minutes=randint(20, 60),
                min_duration_minutes=randint(5, 20),
                max_duration_minutes=randint(60, 120),
                created_at=now,
                updated_at=now,
            )
            await insert_one(
                s,
                "zoom_interaction_reports",
                report_id=rid,
                mean_interaction_count=randint(5, 30),
                min_interaction_count=randint(0, 5),
                max_interaction_count=randint(20, 50),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted all report types")

        # ════════════════════════════════════════════════════════════════
        # 50. STUDENT PROMOTION HISTORY
        # ════════════════════════════════════════════════════════════════
        for i in range(15):
            sc = choice(sc_rows)
            f_sess = choice(session_ids_all)
            t_sess = choice([s for s in session_ids_all if s != f_sess])
            await insert_one(
                s,
                "student_promotion_history",
                student_id=sc.student_id,
                from_session_id=f_sess,
                to_session_id=t_sess,
                from_classroom_id=choice(cl_ids),
                to_classroom_id=choice(cl_ids),
                previous_roll_number=randint(1, 40),
                new_roll_number=randint(1, 40),
                promotion_date=random_date(date(2025, 3, 1), date(2025, 4, 30)),
                promotion_type=choice(PROMO_TYPES),
                promoted_by_user_id=choice(admin_ids),
                created_at=now,
                updated_at=now,
            )
        print("[OK] Inserted 15 promotion history records")

        print("\n[COMPLETE] SEEDING COMPLETE! All 53 tables populated.")
        print(
            "   Credentials: admin1@school.com / teacher1@school.com / student1@school.com"
        )
        print("   Password: password@123")


async def main():
    try:
        await seed_all()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
