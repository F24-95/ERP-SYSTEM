"""Comprehensive seed script for School ERP.
Run: python seed_all_data.py
Creates realistic test data across ALL tables with varied conditions.
"""

import asyncio
import random
import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import async_session_factory, Base, engine
from src.core.enums import (
    UserRole, Gender, AssignmentStatus, ExamStatus,
    FeeStatus, NoticeType, NoticeAudience, AttendanceStatus,
)
from src.core.security import hash_password
from src.domain.users.models import User, StudentProfile, TeacherProfile, AdminProfile
from src.domain.academics.models import AcademicSession, ClassRoom, ClassSubject
from src.domain.curriculum.models import Subject
from src.domain.operations.models import (
    TeacherSubject, StudentClass, StudentAttendance,
    DailyClass, DailyClassStudent, ClassTimeTable,
    WeekDay, TimeSlot,
)
from src.domain.exams.models import Exam, ExamResult
from src.domain.assignments.models import Assignment, AssignmentResult
from src.domain.fees.models import Fee
from src.domain.notices.models import Notice
from src.domain.zoom.models import (
    ZoomMeeting, ZoomRecordingFile, ZoomParticipant,
    ZoomStudentInteraction, ZoomTranscript, ZoomFile,
)
try:
    from src.domain.materials.models import Material
except ImportError:
    Material = None
try:
    from src.domain.messages.models import Message
except ImportError:
    Message = None

# ============================================================
# SEED DATA DEFINITIONS
# ============================================================

STUDENT_NAMES = [
    ("Aarav Sharma", "Male"), ("Priya Patel", "Female"), ("Rohan Gupta", "Male"),
    ("Ananya Singh", "Female"), ("Vikram Kumar", "Male"), ("Neha Reddy", "Female"),
    ("Arjun Mehta", "Male"), ("Kavya Nair", "Female"), ("Aditya Verma", "Male"),
    ("Ishita Joshi", "Female"), ("Rahul Yadav", "Male"), ("Sneha Rao", "Female"),
    ("Karan Malhotra", "Male"), ("Pooja Desai", "Female"), ("Nikhil Bhat", "Male"),
    ("Tanvi Kulkarni", "Female"), ("Amit Tiwari", "Male"), ("Deepika Choudhary", "Female"),
    ("Sanjay Mishra", "Male"), ("Ritu Agarwal", "Female"), ("Manish Pandey", "Female"),
    ("Shruti Kulkarni", "Female"), ("Ravi Shankar", "Male"), ("Meera Krishnan", "Female"),
    ("Arun Nair", "Male"), ("Divya Menon", "Female"), ("Suresh Pillai", "Male"),
    ("Lakshmi Iyer", "Female"), ("Prakash Raj", "Male"), ("Swathi Shetty", "Female"),
]

TEACHER_NAMES = [
    ("Dr. Suresh Kumar", "Male", "Senior Teacher", "Science", 15),
    ("Mrs. Anita Deshpande", "Female", "HOD", "Mathematics", 12),
    ("Mr. Rakesh Singh", "Male", "Teacher", "English", 8),
    ("Mrs. Preeti Sharma", "Female", "Teacher", "Hindi", 10),
    ("Mr. Abhay Deshmukh", "Male", "Teacher", "Social Studies", 6),
    ("Mrs. Nandini Patil", "Female", "Senior Teacher", "Science", 14),
]

SUBJECTS = [
    ("MATH", "Mathematics", "Core", 1),
    ("ENG", "English", "Core", 2),
    ("SCI", "Science", "Core", 3),
    ("HIN", "Hindi", "Core", 4),
    ("SST", "Social Studies", "Core", 5),
    ("CS", "Computer Science", "Elective", 6),
]

CLASSES = [
    ("CL1", "Class 1", "A", "Class 1-A"),
    ("CL2", "Class 1", "B", "Class 1-B"),
    ("CL3", "Class 2", "A", "Class 2-A"),
    ("CL4", "Class 2", "B", "Class 2-B"),
    ("CL5", "Class 3", "A", "Class 3-A"),
]

EXAM_TYPES = ["Unit Test", "Mid Term", "Final Term", "Quiz", "Practical"]
NOTICE_TITLES = [
    "Parent-Teacher Meeting Scheduled",
    "Annual Day Celebration",
    "Science Exhibition",
    "Sports Day Notice",
    "Holiday Declaration",
    "Exam Schedule Released",
    "Fee Payment Reminder",
    "Library Hours Extended",
]


def rand_date(start_year=2024, end_year=2025):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def rand_datetime(d):
    return datetime.combine(d, datetime.min.time()) + timedelta(
        hours=random.randint(8, 16), minutes=random.randint(0, 59)
    )


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # Check if data already exists
        existing = await db.scalar(select(User).limit(1))
        if existing:
            print("Database already has data. Skipping seed.")
            return

        print("Seeding database...")

        # ── 1. Admin ──
        admin_user = User(
            email="admin@school.com", phone="9000000001",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN, is_verified=True,
        )
        db.add(admin_user)
        await db.flush()
        db.add(AdminProfile(user_id=admin_user.id, admin_name="School Admin", department="Administration", is_super_admin=True))

        # ── 2. Teachers ──
        teacher_users = []
        for i, (name, gender, desig, dept, exp) in enumerate(TEACHER_NAMES):
            u = User(
                email=f"teacher{i+1}@school.com", phone=f"91000000{i+1:02d}",
                password_hash=hash_password("teacher123"),
                role=UserRole.TEACHER, is_verified=True,
            )
            db.add(u)
            await db.flush()
            db.add(TeacherProfile(
                user_id=u.id, teacher_name=name,
                gender=Gender.MALE if gender == "Male" else Gender.FEMALE,
                employee_code=f"EMP{i+1:03d}", designation=desig,
                department=dept, experience_years=exp,
            ))
            teacher_users.append(u)
        await db.flush()

        # ── 3. Academic Session ──
        session_2024 = AcademicSession(
            session_code="SES2024", session_name="2024-25",
            start_year=2024, end_year=2025,
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31),
            is_current=True, description="Academic Year 2024-25",
        )
        session_2023 = AcademicSession(
            session_code="SES2023", session_name="2023-24",
            start_year=2023, end_year=2024,
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31),
            is_current=False, description="Academic Year 2023-24",
        )
        db.add_all([session_2024, session_2023])
        await db.flush()

        # ── 4. Subjects ──
        subject_objs = []
        for code, name, stype, order in SUBJECTS:
            s = Subject(subject_code=code, subject_name=name, subject_type=stype, display_order=order)
            db.add(s)
            subject_objs.append(s)
        await db.flush()

        # ── 5. Classrooms ──
        classroom_objs = []
        for cls_code, cls_name, section, display in CLASSES:
            cr = ClassRoom(
                class_code=cls_code, class_name=cls_name, section=section,
                display_name=display, academic_sessions_id=session_2024.id,
            )
            db.add(cr)
            classroom_objs.append(cr)
        await db.flush()

        # ── 6. Class-Subject mappings ──
        cs_objs = {}
        for cr in classroom_objs:
            cs_objs[cr.id] = []
            for subj in subject_objs:
                cs = ClassSubject(
                    academic_sessions_id=session_2024.id,
                    classroom_id=cr.id, subject_id=subj.id,
                    display_order=subj.display_order,
                )
                db.add(cs)
                cs_objs[cr.id].append(cs)
        await db.flush()

        # ── 7. Teacher-Subject assignments ──
        ts_objs = []
        teacher_idx = 0
        for cr in classroom_objs:
            for cs in cs_objs[cr.id]:
                ts = TeacherSubject(
                    academic_sessions_id=session_2024.id,
                    class_subject_id=cs.id, classroom_id=cr.id,
                    subject_id=cs.subject_id,
                    teacher_id=teacher_users[teacher_idx % len(teacher_users)].id,
                )
                db.add(ts)
                ts_objs.append(ts)
            teacher_idx += 1
        await db.flush()

        # ── 8. WeekDays & TimeSlots ──
        days = [
            ("MON", "Monday", 1), ("TUE", "Tuesday", 2), ("WED", "Wednesday", 3),
            ("THU", "Thursday", 4), ("FRI", "Friday", 5), ("SAT", "Saturday", 6),
        ]
        weekday_objs = []
        for code, name, order in days:
            wd = WeekDay(day_code=code, day_name=name, display_order=order)
            db.add(wd)
            weekday_objs.append(wd)

        slots = []
        for i in range(6):
            start = datetime(2024, 1, 1, 8 + i, 0)
            end = start + timedelta(minutes=50)
            slot = TimeSlot(
                slot_code=f"S{i+1:02d}", slot_name=f"Period {i+1}",
                start_time=start.time(), end_time=end.time(),
                duration_minutes=50, display_order=i + 1,
            )
            db.add(slot)
            slots.append(slot)
        await db.flush()

        # ── 9. Students + Profiles + Enrollments + Attendance ──
        student_users = []
        student_profiles = []
        enrollment_objs = []
        roll_counter = {cr.id: 1 for cr in classroom_objs}

        for i, (name, gender) in enumerate(STUDENT_NAMES):
            u = User(
                email=f"student{i+1}@school.com", phone=f"92000000{i+1:02d}",
                password_hash=hash_password("student123"),
                role=UserRole.STUDENT, is_verified=True,
            )
            db.add(u)
            await db.flush()

            sp = StudentProfile(
                user_id=u.id, student_name=name,
                gender=Gender.MALE if gender == "Male" else Gender.FEMALE,
                admission_number=f"ADM{i+1:04d}",
                registration_number=f"REG{i+1:04d}",
                date_of_birth=date(random.randint(2010, 2016), random.randint(1, 12), random.randint(1, 28)),
                blood_group=random.choice(["A+", "B+", "O+", "AB+", "A-", "B-"]),
                address=f"{random.randint(1, 200)} Main Street",
                city=random.choice(["Mumbai", "Delhi", "Bangalore", "Pune"]),
                state=random.choice(["Maharashtra", "Delhi", "Karnataka"]),
                parent_name=f"Parent of {name.split()[0]}",
                parent_phone=f"93000000{i+1:02d}",
            )
            db.add(sp)
            student_users.append(u)
            student_profiles.append(sp)
        await db.flush()

        # Enroll students into classes (6 per class)
        for i, sp in enumerate(student_profiles):
            class_idx = i // 6
            if class_idx >= len(classroom_objs):
                class_idx = i % len(classroom_objs)
            cr = classroom_objs[class_idx]
            roll = roll_counter[cr.id]
            roll_counter[cr.id] += 1

            sc = StudentClass(
                academic_sessions_id=session_2024.id,
                student_id=sp.user_id,
                classroom_id=cr.id,
                roll_number=roll,
                admission_date=date(2024, 4, 1),
                status="ACTIVE",
            )
            db.add(sc)
            enrollment_objs.append(sc)
        await db.flush()

        # ── 10. Attendance records ──
        for sc in enrollment_objs:
            total = random.randint(80, 180)
            present_pct = random.uniform(0.5, 0.98)
            present = int(total * present_pct)
            absent = total - present
            att = StudentAttendance(
                student_class_id=sc.id,
                total_classes=total,
                present_classes=present,
                absent_classes=absent,
                attendance_percentage=round(present / total * 100, 1),
            )
            db.add(att)
        await db.flush()

        # ── 11. DailyClass + DailyClassStudent ──
        for cr in classroom_objs:
            for day_offset in range(0, 90, 7):
                d = date(2024, 6, 3) + timedelta(days=day_offset)
                if d > date(2025, 3, 31):
                    break
                ts_list = cs_objs[cr.id]
                if not ts_list:
                    continue
                cs = ts_list[day_offset // 7 % len(ts_list)]
                ts_query = select(TeacherSubject).filter_by(
                    classroom_id=cr.id, subject_id=cs.subject_id,
                    academic_sessions_id=session_2024.id,
                )
                ts = (await db.execute(ts_query)).scalar()
                if not ts:
                    continue

                dc = DailyClass(
                    daily_class_id=f"DC-{cr.id}-{day_offset:04d}",
                    academic_sessions_id=session_2024.id,
                    classroom_id=cr.id,
                    class_subject_id=cs.id,
                    teacher_subject_id=ts.id,
                    class_date=d,
                    topic=f"Topic for {d.strftime('%b %d')}",
                    description=f"Lesson conducted on {d}",
                    lecture_status="Completed",
                )
                db.add(dc)
                await db.flush()

                stu_list = [e for e in enrollment_objs if e.classroom_id == cr.id]
                for sc in stu_list:
                    status = random.choices(
                        ["Present", "Absent", "Late", "Leave"],
                        weights=[70, 15, 10, 5],
                    )[0]
                    dcs = DailyClassStudent(
                        daily_class_id=dc.id,
                        student_class_id=sc.id,
                        attendance_status=status,
                        is_late=(status == "Late"),
                        late_minutes=random.randint(5, 20) if status == "Late" else 0,
                    )
                    db.add(dcs)
            await db.flush()

        # ── 12. Exams + Results ──
        for cr in classroom_objs:
            for cs in cs_objs[cr.id]:
                subj = await db.get(Subject, cs.subject_id)
                ts_query = select(TeacherSubject).filter_by(
                    classroom_id=cr.id, subject_id=cs.subject_id,
                    academic_sessions_id=session_2024.id,
                )
                ts = (await db.execute(ts_query)).scalar()
                if not ts:
                    continue

                for exam_idx, exam_type in enumerate(EXAM_TYPES[:3]):
                    exam = Exam(
                        exam_id=f"EXM-{uuid.uuid4().hex[:8].upper()}",
                        academic_sessions_id=session_2024.id,
                        classroom_id=cr.id,
                        class_subject_id=cs.id,
                        teacher_subject_id=ts.id,
                        exam_name=f"{subj.subject_name} - {exam_type}",
                        exam_type=exam_type,
                        exam_date=date(2024, 6 + exam_idx * 2, 15),
                        total_marks=100,
                        passing_marks=33,
                        status=ExamStatus.COMPLETED,
                        total_students=6,
                    )
                    db.add(exam)
                    await db.flush()

                    stu_list = [e for e in enrollment_objs if e.classroom_id == cr.id]
                    for sc in stu_list:
                        marks = random.randint(15, 98)
                        er = ExamResult(
                            exam_id=exam.id,
                            student_class_id=sc.id,
                            obtained_marks=marks,
                            percentage=marks,
                            grade="A" if marks >= 80 else "B" if marks >= 60 else "C" if marks >= 40 else "D",
                            is_absent=False,
                        )
                        db.add(er)
            await db.flush()

        # ── 13. Assignments + Results ──
        for cr in classroom_objs:
            for cs in cs_objs[cr.id]:
                subj = await db.get(Subject, cs.subject_id)
                ts_query = select(TeacherSubject).filter_by(
                    classroom_id=cr.id, subject_id=cs.subject_id,
                    academic_sessions_id=session_2024.id,
                )
                ts = (await db.execute(ts_query)).scalar()
                if not ts:
                    continue

                for a_idx in range(4):
                    assignment = Assignment(
                        assignment_id=f"ASN-{uuid.uuid4().hex[:8].upper()}",
                        academic_sessions_id=session_2024.id,
                        classroom_id=cr.id,
                        class_subject_id=cs.id,
                        teacher_subject_id=ts.id,
                        title=f"{subj.subject_name} Assignment {a_idx + 1}",
                        description=f"Assignment {a_idx + 1} for {subj.subject_name}",
                        due_date=date(2024, 7 + a_idx, 15),
                        total_marks=50,
                        passing_marks=17,
                        status=AssignmentStatus.PUBLISHED,
                        total_students=6,
                        checked_students=6,
                        created_by=teacher_users[0].id,
                    )
                    db.add(assignment)
                    await db.flush()

                    stu_list = [e for e in enrollment_objs if e.classroom_id == cr.id]
                    for sc in stu_list:
                        marks = random.randint(10, 50)
                        ar = AssignmentResult(
                            assignment_id=assignment.id,
                            student_class_id=sc.id,
                            obtained_marks=marks,
                            percentage=round(marks / 50 * 100, 1),
                            grade="A" if marks >= 40 else "B" if marks >= 30 else "C",
                            is_checked=True,
                        )
                        db.add(ar)
            await db.flush()

        # ── 14. Fees ──
        fee_months = [(m, 2024) for m in range(4, 13)] + [(m, 2025) for m in range(1, 4)]
        for sc in enrollment_objs:
            for month, year in fee_months:
                total = random.choice([3000, 4000, 5000, 6000])
                status = random.choices(
                    ["PAID", "PENDING", "PARTIAL"],
                    weights=[50, 30, 20],
                )[0]
                paid = total if status == "PAID" else (total * random.uniform(0.3, 0.7) if status == "PARTIAL" else 0)
                fee = Fee(
                    fee_id=f"FEE-{uuid.uuid4().hex[:8].upper()}",
                    academic_sessions_id=session_2024.id,
                    student_class_id=sc.id,
                    fee_month=month, fee_year=year,
                    total_amount=total,
                    paid_amount=round(paid, 2),
                    due_date=date(year, month, 10),
                    paid_date=date(year, month, random.randint(5, 9)) if status == "PAID" else None,
                    status=status,
                    created_by=admin_user.id,
                )
                db.add(fee)
            await db.flush()

        # ── 15. Notices ──
        for i, title in enumerate(NOTICE_TITLES):
            n = Notice(
                academic_sessions_id=session_2024.id,
                title=title,
                description=f"This is a notice about {title.lower()}. Please follow the instructions.",
                notice_type=random.choice(list(NoticeType)),
                audience=random.choice(list(NoticeAudience)),
                publish_date=date(2024, 6 + i % 6, 1),
                expiry_date=date(2025, 3, 31),
                is_pinned=i < 2,
                created_by=admin_user.id,
            )
            db.add(n)
        await db.flush()

        # ── 16. Zoom data (varied per class) ──
        student_names_for_zoom = [
            ("Aarav Sharma", "aarav@school.com"), ("Priya Patel", "priya@school.com"),
            ("Rohan Gupta", "rohan@school.com"), ("Ananya Singh", "ananya@school.com"),
            ("Vikram Kumar", "vikram@school.com"), ("Neha Reddy", "neha@school.com"),
        ]

        for cr_idx, cr in enumerate(classroom_objs):
            for session_idx in range(5):
                meeting_uuid = str(uuid.uuid4())
                start = datetime(2024, 6 + cr_idx, 5 + session_idx * 14, 9 + cr_idx, 0)
                duration = 40 + random.randint(0, 20)

                meeting = ZoomMeeting(
                    uuid=meeting_uuid,
                    meeting_id=200000 + cr_idx * 100 + session_idx,
                    host_id=f"teacher_{cr.id}",
                    topic=f"{cr.display_name} - {random.choice(SUBJECTS)[1]} Session {session_idx + 1}",
                    type=2, start_time=start, timezone="Asia/Kolkata",
                    duration=duration, recording_count=1,
                )
                db.add(meeting)
                await db.flush()

                rec_id = str(uuid.uuid4())
                recording = ZoomRecordingFile(
                    id=rec_id, meeting_uuid=meeting_uuid,
                    recording_start=start,
                    recording_end=start + timedelta(minutes=duration),
                    file_type="MP4", file_extension="mp4", status="completed",
                )
                db.add(recording)
                await db.flush()

                zf = ZoomFile(
                    file_initial=f"{cr.display_name} Session {session_idx + 1}",
                    raw_date=start.strftime("%Y-%m-%d"),
                    raw_time=start.strftime("%H:%M"),
                    date=start.strftime("%Y-%m-%d"),
                    time=start.strftime("%H:%M"),
                    classroom_id=cr.id,
                    recording_file_id=rec_id,
                )
                db.add(zf)

                for std_idx, (name, email) in enumerate(student_names_for_zoom):
                    part_id = str(uuid.uuid4())
                    join = start + timedelta(minutes=std_idx * random.randint(1, 3))
                    leave = join + timedelta(minutes=duration - std_idx * 2 - random.randint(0, 5))
                    if leave <= join:
                        leave = join + timedelta(minutes=5)

                    participant = ZoomParticipant(
                        meeting_uuid=meeting_uuid,
                        zoom_participant_id=part_id,
                        name=name, user_email=email,
                        join_time=join, leave_time=leave,
                        meeting_date=start.date(),
                        duration_seconds=int((leave - join).total_seconds()),
                        duration_minutes=int((leave - join).total_seconds() / 60),
                        status="in_meeting",
                        attentiveness_score=str(random.randint(60, 95)),
                    )
                    db.add(participant)

                    for inter_idx in range(random.randint(2, 6)):
                        interaction = ZoomStudentInteraction(
                            recording_file_id=rec_id,
                            class_date=start, class_name=cr.display_name,
                            interaction_time=f"00:{random.randint(2, 40):02d}:{random.randint(0, 59):02d}",
                            interaction_duration=random.randint(10, 120),
                            speaker_name=name,
                        )
                        db.add(interaction)

                    for seg_idx in range(random.randint(3, 8)):
                        transcript = ZoomTranscript(
                            recording_file_id=rec_id,
                            segment_index=std_idx * 10 + seg_idx,
                            start_time=f"00:{seg_idx * 3:02d}:00",
                            end_time=f"00:{seg_idx * 3 + 2:02d}:00",
                            duration=120.0,
                            speaker=name,
                            text=f"Discussion about {random.choice(['math concepts', 'science experiments', 'English grammar', 'history topics'])} in {cr.display_name}",
                            class_name=cr.display_name,
                            class_date=start,
                        )
                        db.add(transcript)
            await db.flush()

        # ── 17. Messages (if model exists) ──
        if Message is not None:
            for i in range(10):
                msg = Message(
                    sender_id=random.choice(teacher_users + [admin_user]).id,
                    receiver_id=random.choice(student_users).id,
                    subject=f"Message {i+1}",
                    body=f"This is a test message number {i+1} for testing purposes.",
                    is_read=random.choice([True, False]),
                )
                db.add(msg)
            await db.flush()

        await db.commit()
        print("=" * 60)
        print("SEED COMPLETE!")
        print("=" * 60)
        print(f"  Users:       {len(student_users)} students + {len(teacher_users)} teachers + 1 admin")
        print(f"  Classes:     {len(classroom_objs)}")
        print(f"  Subjects:    {len(subject_objs)}")
        print(f"  Enrollments: {len(enrollment_objs)}")
        print(f"  Exams:       ~{len(classroom_objs) * len(subject_objs) * 3}")
        print(f"  Assignments: ~{len(classroom_objs) * len(subject_objs) * 4}")
        print(f"  Fees:        ~{len(enrollment_objs) * len(fee_months)}")
        print(f"  Zoom meetings: {len(classroom_objs) * 5}")
        print()
        print("LOGIN CREDENTIALS:")
        print("  Admin:   admin@school.com / admin123")
        print("  Teacher: teacher1@school.com / teacher123")
        print("  Student: student1@school.com / student123")


if __name__ == "__main__":
    asyncio.run(seed())
