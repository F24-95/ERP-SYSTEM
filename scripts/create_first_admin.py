"""
One-time CLI script to create the first accounts on a fresh deployment.

Supports adding any role (admin, teacher, student).
Safe to re-run: skips accounts whose email already exists.

USAGE
-----
    python -m scripts.create_first_admin

Or pass details as arguments:
    python -m scripts.create_first_admin --email admin@school.com --phone 9999999999 --password "ChangeMe123!" --role admin
"""

import argparse
import asyncio
import getpass
from dotenv import load_dotenv

load_dotenv()

# Import base FIRST so every model module is registered on
# Base.metadata before any mapper configuration runs.
import src.database.base  # noqa: F401

from sqlalchemy import select

from src.database.connection import AsyncSessionLocal
from src.core.enums import UserRole
from src.core.id_generators import generate_admin_id, generate_teacher_id, generate_student_id
from src.core.security import hash_password
from src.domain.users.models import User, AdminProfile, TeacherProfile, StudentProfile

ROLE_MAP = {
    "admin": UserRole.ADMIN,
    "teacher": UserRole.TEACHER,
    "student": UserRole.STUDENT,
}


async def create_account(email: str, phone: str, password: str, role: UserRole, name: str | None = None, super_admin: bool = False) -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).filter_by(email=email))
        if existing:
            print(f"Account with email '{email}' already exists. Skipping.")
            return

        display_name = name or email.split("@")[0].replace(".", " ").replace("_", " ").title()

        user = User(
            email=email,
            phone=phone,
            role=role,
            password_hash=hash_password(password),
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
                admin_name=display_name,
                is_super_admin=super_admin,
            ))

        elif role == UserRole.TEACHER:
            user.teacher_id = generate_teacher_id(user.id)
            await db.flush()
            await db.refresh(user)
            db.add(TeacherProfile(
                user_id=user.id,
                teacher_name=display_name,
            ))

        elif role == UserRole.STUDENT:
            user.student_id = generate_student_id(user.id)
            await db.flush()
            await db.refresh(user)
            db.add(StudentProfile(
                user_id=user.id,
                student_name=display_name,
            ))

        await db.commit()
        print(f"{role.value} created: {user.email} (id={getattr(user, f'{role.value}_id')})")


def main():
    parser = argparse.ArgumentParser(description="Create accounts (admin/teacher/student).")
    parser.add_argument("--email", help="Account email")
    parser.add_argument("--phone", help="Phone number")
    parser.add_argument("--password", help="Password (min 8 chars). Omit to be prompted.")
    parser.add_argument("--role", choices=list(ROLE_MAP), default="admin", help="Account role (default: admin)")
    parser.add_argument("--name", help="Display name (auto-derived from email if omitted)")
    parser.add_argument("--super-admin", action="store_true", help="Mark admin as super admin")
    args = parser.parse_args()

    email = args.email or input("Email: ").strip()
    phone = args.phone or input("Phone: ").strip()
    password = args.password or getpass.getpass("Password: ")
    role = ROLE_MAP[args.role]
    name = args.name or None

    asyncio.run(create_account(email, phone, password, role, name, super_admin=args.super_admin))


if __name__ == "__main__":
    main()
