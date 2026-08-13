"""
Seed script: creates 10 ready-to-login accounts (4 admin, 3 teacher, 3 student)
directly in the database.

WHY THIS EXISTS
----------------
Account creation in this project is admin-only (POST /admin/user), which means
on a brand-new database there is no way to log in at all -- there's no
bootstrap admin. This script inserts the first batch of accounts directly via
SQLAlchemy so you can log in immediately. Once you have a couple of admin
accounts, use them (via /admin/user, /admin/student-profiles,
/admin/teacher-profiles, /admin/admin-profiles) to create everyone else.

USAGE
-----
    python -m scripts.seed_accounts

Run it again any time -- it skips accounts that already exist (matched by
email), so it's safe to re-run.

All seeded accounts use the password:  password123
(change it after first login)
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

# Import base FIRST so every model module is registered on
# Base.metadata before any mapper configuration runs.
import src.database.base  # noqa: F401

from sqlalchemy import select, text

from src.database.connection import AsyncSessionLocal, engine, Base
from src.core.enums import UserRole
from src.core.id_generators import generate_admin_id, generate_teacher_id, generate_student_id
from src.core.security import hash_password
from src.domain.users.models import User, AdminProfile, TeacherProfile, StudentProfile

DEFAULT_PASSWORD = "password123"

ACCOUNTS = [
    {"role": UserRole.ADMIN,   "email": "ffaizan@student.iul.ac.in",  "phone": "9517122461", "name": "Mohd Faizan", "super_admin": True},
    {"role": UserRole.ADMIN,   "email": "admin2@school.edu",          "phone": "9000000002", "name": "Admin Two"},
    {"role": UserRole.ADMIN,   "email": "admin3@school.edu",          "phone": "9000000003", "name": "Admin Three"},
    {"role": UserRole.ADMIN,   "email": "admin4@school.edu",          "phone": "9000000004", "name": "Admin Four"},
    {"role": UserRole.TEACHER, "email": "teacher1@school.com",        "phone": "9000000011", "name": "Teacher One"},
    {"role": UserRole.TEACHER, "email": "teacher2@school.com",        "phone": "9000000012", "name": "Teacher Two"},
    {"role": UserRole.TEACHER, "email": "teacher3@school.com",        "phone": "9000000013", "name": "Teacher Three"},
    {"role": UserRole.STUDENT, "email": "student1@school.com",        "phone": "9000000021", "name": "Student One"},
    {"role": UserRole.STUDENT, "email": "student2@school.com",        "phone": "9000000022", "name": "Student Two"},
    {"role": UserRole.STUDENT, "email": "student3@school.com",        "phone": "9000000023", "name": "Student Three"},
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        created, skipped = [], []

        try:
            for acc in ACCOUNTS:
                existing = await db.scalar(
                    select(User).filter_by(email=acc["email"]),
                )
                if existing:
                    skipped.append(acc["email"])
                    continue

                user = User(
                    email=acc["email"],
                    phone=acc["phone"],
                    role=acc["role"],
                    password_hash=hash_password(DEFAULT_PASSWORD),
                    is_verified=True,
                    is_active=True,
                )
                db.add(user)
                await db.flush()
                await db.refresh(user)

                if acc["role"] == UserRole.ADMIN:
                    user.admin_id = generate_admin_id(user.id)
                    await db.flush()
                    await db.refresh(user)

                    db.add(AdminProfile(
                        user_id=user.id,
                        admin_name=acc["name"],
                        is_super_admin=acc.get("super_admin", False),
                    ))

                elif acc["role"] == UserRole.TEACHER:
                    user.teacher_id = generate_teacher_id(user.id)
                    await db.flush()
                    await db.refresh(user)

                    db.add(TeacherProfile(
                        user_id=user.id,
                        teacher_name=acc["name"],
                    ))

                elif acc["role"] == UserRole.STUDENT:
                    user.student_id = generate_student_id(user.id)
                    await db.flush()
                    await db.refresh(user)

                    db.add(StudentProfile(
                        user_id=user.id,
                        student_name=acc["name"],
                    ))

                created.append((acc["role"].value, acc["email"]))

            await db.commit()

        except Exception:
            await db.rollback()
            raise

    print("\n=== Seed complete ===")
    if created:
        print(f"\nCreated {len(created)} account(s):")
        for role, email in created:
            print(f"  [{role:7}] {email}  /  password: {DEFAULT_PASSWORD}")
    if skipped:
        print(f"\nSkipped {len(skipped)} account(s) that already exist:")
        for email in skipped:
            print(f"  {email}")
    print(f"\nLogin at POST /auth/login with any of the emails above and password '{DEFAULT_PASSWORD}'.")
    print("Change these passwords after first login (POST /auth/change-password).")


if __name__ == "__main__":
    asyncio.run(main())
