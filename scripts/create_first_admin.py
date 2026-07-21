"""
One-time CLI script to create the first admin account on a fresh
deployment.

WHY THIS EXISTS AS A SCRIPT AND NOT AN API ROUTE
--------------------------------------------------
Every user-creation path in this API (`POST /admin/user`) requires an
existing admin to call it (`require_role(UserRole.ADMIN)`). That's
correct and should stay that way. But it creates a chicken-and-egg
problem on a brand new deployment: there is no admin yet, so nothing can
call that route.

A previous version of this project "solved" that by leaving
`POST /users/` completely unauthenticated with a client-controlled
`role` field -- which meant *anyone* could self-register as an admin at
any time, not just during initial setup. That was a critical security
hole and has been removed (see src/api/routers/users.py). An
"only works if zero users exist yet" API escape hatch would still be a
live network-reachable endpoint that has to be reasoned about
forever -- a one-time script that a deploy operator runs directly
against the database, and which never ships as an HTTP route, is the
standard, safer pattern for this problem.

USAGE
-----
    python -m scripts.create_first_admin --email admin@school.com --phone 9999999999 --password "ChangeMe123!"

Or interactively (it will prompt for anything not passed as a flag):

    python -m scripts.create_first_admin

Safe to re-run: refuses to do anything if an admin already exists.
"""

import argparse
import asyncio
import getpass
import sys
from dotenv import load_dotenv

# Load .env BEFORE any project imports that read environment variables
load_dotenv()

from sqlalchemy import select

from src.database.connection import AsyncSessionLocal

# Required so every domain's models.py is imported and registered on
# Base.metadata before SQLAlchemy configures mappers below -- User has
# relationships (e.g. to Topic) that live in other domains' model files.
# Without this, running this script standalone (not via src.main, which
# does its own `import src.database.base`) crashes with
# "InvalidRequestError: ... failed to locate a name" the first time any
# mapper touches a cross-domain relationship.
import src.database.base  # noqa: F401
from src.core.enums import UserRole
from src.domain.users.models import User
from src.domain.users.schemas import AdminUserCreate
from src.domain.admin.service import AdminService


async def _admin_already_exists(session) -> bool:
    result = await session.execute(select(User).filter_by(role=UserRole.ADMIN))
    return result.scalars().first() is not None


async def create_first_admin(email: str, phone: str, password: str) -> None:
    async with AsyncSessionLocal() as session:
        if await _admin_already_exists(session):
            print(
                "An admin account already exists. Refusing to create another via this "
                "bootstrap script -- use POST /admin/user (as an existing admin) instead."
            )
            sys.exit(1)

        user_data = AdminUserCreate(
            email=email, phone=phone, password=password, role=UserRole.ADMIN
        )
        try:
            new_admin = await AdminService.create_user_with_profile(
                session, user_data, current_user_id=None
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise

        print(f"Admin created: {new_admin.email} (admin_id={new_admin.admin_id})")


def main():
    parser = argparse.ArgumentParser(description="Create the first admin account.")
    parser.add_argument("--email", help="Admin email")
    parser.add_argument("--phone", help="Admin phone number")
    parser.add_argument(
        "--password", help="Admin password (min 8 chars). Omit to be prompted securely."
    )
    args = parser.parse_args()

    email = args.email or input("Admin email: ").strip()
    phone = args.phone or input("Admin phone: ").strip()
    password = args.password or getpass.getpass("Admin password: ")

    asyncio.run(create_first_admin(email, phone, password))


if __name__ == "__main__":
    main()
