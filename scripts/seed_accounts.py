"""
Seed script — creates all user accounts (Admin, Teacher, Student).

This is the ONLY seed script. After running, the admin can log in
and manage everything else (academics, exams, fees, etc.) via the API.

USAGE
-----
    python -m scripts.seed_accounts

Safe to re-run — skips accounts that already exist (matched by email).
All accounts use the password: password123
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

import src.database.base  # noqa: F401

from sqlalchemy import select, text

from src.database.connection import AsyncSessionLocal, engine, Base
from src.core.enums import UserRole, Gender
from src.core.id_generators import (
    generate_admin_id,
    generate_teacher_id,
    generate_student_id,
)
from src.core.security import hash_password
from src.domain.users.models import (
    User,
    AdminProfile,
    TeacherProfile,
    StudentProfile,
)

DEFAULT_PASSWORD = "password123"

# ────────────────────────────────────────────────────────────
# ACCOUNTS — add/remove entries here as needed
# ────────────────────────────────────────────────────────────

ADMIN_ACCOUNTS = [
    {
        "email": "faizansidd601@gmail.com",
        "phone": "9517122461",
        "name": "Super Admin",
        "super_admin": True,
    },
    {
        "email": "admin2@school.com",
        "phone": "9000000002",
        "name": "Admin Two",
    },
    {
        "email": "admin3@school.com",
        "phone": "9000000003",
        "name": "Admin Three",
    },
]

TEACHER_ACCOUNTS = [
    {
        "email": "teacher1@school.com", "phone": "9100000001",
        "name": "Dr. Suresh Kumar", "gender": "Male",
        "designation": "Senior Teacher", "department": "Science",
        "experience": 15,
    },
    {
        "email": "teacher2@school.com", "phone": "9100000002",
        "name": "Mrs. Anita Deshpande", "gender": "Female",
        "designation": "HOD", "department": "Mathematics",
        "experience": 12,
    },
    {
        "email": "teacher3@school.com", "phone": "9100000003",
        "name": "Mr. Rakesh Singh", "gender": "Male",
        "designation": "Teacher", "department": "English",
        "experience": 8,
    },
    {
        "email": "teacher4@school.com", "phone": "9100000004",
        "name": "Mrs. Preeti Sharma", "gender": "Female",
        "designation": "Teacher", "department": "Hindi",
        "experience": 10,
    },
    {
        "email": "teacher5@school.com", "phone": "9100000005",
        "name": "Mr. Abhay Deshmukh", "gender": "Male",
        "designation": "Teacher", "department": "Social Studies",
        "experience": 6,
    },
    {
        "email": "teacher6@school.com", "phone": "9100000006",
        "name": "Mrs. Nandini Patil", "gender": "Female",
        "designation": "Senior Teacher", "department": "Science",
        "experience": 14,
    },
]

STUDENT_ACCOUNTS = [
    {"email": "student1@school.com",  "phone": "9200000001", "name": "Aarav Sharma",      "gender": "Male"},
    {"email": "student2@school.com",  "phone": "9200000002", "name": "Priya Patel",       "gender": "Female"},
    {"email": "student3@school.com",  "phone": "9200000003", "name": "Rohan Gupta",       "gender": "Male"},
    {"email": "student4@school.com",  "phone": "9200000004", "name": "Ananya Singh",      "gender": "Female"},
    {"email": "student5@school.com",  "phone": "9200000005", "name": "Vikram Kumar",      "gender": "Male"},
    {"email": "student6@school.com",  "phone": "9200000006", "name": "Neha Reddy",        "gender": "Female"},
    {"email": "student7@school.com",  "phone": "9200000007", "name": "Arjun Mehta",       "gender": "Male"},
    {"email": "student8@school.com",  "phone": "9200000008", "name": "Kavya Nair",        "gender": "Female"},
    {"email": "student9@school.com",  "phone": "9200000009", "name": "Aditya Verma",      "gender": "Male"},
    {"email": "student10@school.com", "phone": "9200000010", "name": "Ishita Joshi",      "gender": "Female"},
    {"email": "student11@school.com", "phone": "9200000011", "name": "Rahul Yadav",       "gender": "Male"},
    {"email": "student12@school.com", "phone": "9200000012", "name": "Sneha Rao",         "gender": "Female"},
    {"email": "student13@school.com", "phone": "9200000013", "name": "Karan Malhotra",    "gender": "Male"},
    {"email": "student14@school.com", "phone": "9200000014", "name": "Pooja Desai",       "gender": "Female"},
    {"email": "student15@school.com", "phone": "9200000015", "name": "Nikhil Bhat",       "gender": "Male"},
    {"email": "student16@school.com", "phone": "9200000016", "name": "Tanvi Kulkarni",    "gender": "Female"},
    {"email": "student17@school.com", "phone": "9200000017", "name": "Amit Tiwari",       "gender": "Male"},
    {"email": "student18@school.com", "phone": "9200000018", "name": "Deepika Choudhary", "gender": "Female"},
    {"email": "student19@school.com", "phone": "9200000019", "name": "Sanjay Mishra",     "gender": "Male"},
    {"email": "student20@school.com", "phone": "9200000020", "name": "Ritu Agarwal",      "gender": "Female"},
    {"email": "student21@school.com", "phone": "9200000021", "name": "Manish Pandey",     "gender": "Male"},
    {"email": "student22@school.com", "phone": "9200000022", "name": "Shruti Kulkarni",   "gender": "Female"},
    {"email": "student23@school.com", "phone": "9200000023", "name": "Ravi Shankar",      "gender": "Male"},
    {"email": "student24@school.com", "phone": "9200000024", "name": "Meera Krishnan",    "gender": "Female"},
    {"email": "student25@school.com", "phone": "9200000025", "name": "Arun Nair",         "gender": "Male"},
    {"email": "student26@school.com", "phone": "9200000026", "name": "Divya Menon",       "gender": "Female"},
    {"email": "student27@school.com", "phone": "9200000027", "name": "Suresh Pillai",     "gender": "Male"},
    {"email": "student28@school.com", "phone": "9200000028", "name": "Lakshmi Iyer",      "gender": "Female"},
    {"email": "student29@school.com", "phone": "9200000029", "name": "Prakash Raj",       "gender": "Male"},
    {"email": "student30@school.com", "phone": "9200000030", "name": "Swathi Shetty",     "gender": "Female"},
]


async def create_user(db, email, phone, name, role, extra=None):
    existing = await db.scalar(select(User).filter_by(email=email))
    if existing:
        return None

    user = User(
        email=email,
        phone=phone,
        role=role,
        password_hash=hash_password(DEFAULT_PASSWORD),
        is_verified=True,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    if role == UserRole.ADMIN:
        user.admin_id = generate_admin_id(user.id)
        await db.flush()
        await db.refresh(user)
        db.add(AdminProfile(
            user_id=user.id,
            admin_name=name,
            is_super_admin=extra.get("super_admin", False) if extra else False,
        ))

    elif role == UserRole.TEACHER:
        user.teacher_id = generate_teacher_id(user.id)
        await db.flush()
        await db.refresh(user)
        gender = extra.get("gender", "Male") if extra else "Male"
        db.add(TeacherProfile(
            user_id=user.id,
            teacher_name=name,
            gender=Gender.MALE if gender == "Male" else Gender.FEMALE,
            employee_code=extra.get("employee_code", ""),
            designation=extra.get("designation", "Teacher"),
            department=extra.get("department", ""),
            experience_years=extra.get("experience", 0),
        ))

    elif role == UserRole.STUDENT:
        user.student_id = generate_student_id(user.id)
        await db.flush()
        await db.refresh(user)
        gender = extra.get("gender", "Male") if extra else "Male"
        db.add(StudentProfile(
            user_id=user.id,
            student_name=name,
            gender=Gender.MALE if gender == "Male" else Gender.FEMALE,
        ))

    return user


async def seed():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        created, skipped = [], []

        try:
            # ── Admins ──
            for acc in ADMIN_ACCOUNTS:
                user = await create_user(
                    db,
                    acc["email"],
                    acc["phone"],
                    acc["name"],
                    UserRole.ADMIN,
                    {"super_admin": acc.get("super_admin", False)},
                )
                if user:
                    created.append(("admin", acc["email"]))
                else:
                    skipped.append(acc["email"])

            # ── Teachers ──
            for i, acc in enumerate(TEACHER_ACCOUNTS):
                user = await create_user(
                    db,
                    acc["email"],
                    acc["phone"],
                    acc["name"],
                    UserRole.TEACHER,
                    {
                        "gender": acc["gender"],
                        "employee_code": f"EMP{i + 1:03d}",
                        "designation": acc["designation"],
                        "department": acc["department"],
                        "experience": acc["experience"],
                    },
                )
                if user:
                    created.append(("teacher", acc["email"]))
                else:
                    skipped.append(acc["email"])

            # ── Students ──
            for acc in STUDENT_ACCOUNTS:
                user = await create_user(
                    db,
                    acc["email"],
                    acc["phone"],
                    acc["name"],
                    UserRole.STUDENT,
                    {"gender": acc["gender"]},
                )
                if user:
                    created.append(("student", acc["email"]))
                else:
                    skipped.append(acc["email"])

            await db.commit()

        except Exception:
            await db.rollback()
            raise

    print("\n" + "=" * 50)
    print("  SEED COMPLETE")
    print("=" * 50)

    if created:
        print(f"\n  Created {len(created)} account(s):")
        for role, email in created:
            print(f"    [{role:7}] {email}")

    if skipped:
        print(f"\n  Skipped {len(skipped)} account(s) already exist:")
        for email in skipped:
            print(f"    {email}")

    print(f"\n  Password for all accounts: {DEFAULT_PASSWORD}")
    print("  Change passwords after first login (POST /auth/change-password).")
    print()


if __name__ == "__main__":
    asyncio.run(seed())
