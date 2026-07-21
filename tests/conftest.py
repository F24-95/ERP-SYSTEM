import os
import sys
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:Faizan9517@localhost:5432/faizan20_test",
)

from src.database.connection import Base, get_db
from src.core.security import hash_password, create_auth_tokens
from src.core.enums import UserRole
from src.domain.users.models import User, StudentProfile, TeacherProfile, AdminProfile
from src.domain.academics.models import AcademicSession, ClassRoom, Subject
from src.main import create_app


@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncSession:
    TestSessionLocal = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(engine) -> AsyncGenerator:
    TestSessionLocal = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _get_db():
        async with TestSessionLocal() as s:
            yield s

    application = create_app()
    application.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _create_user(db, email, password, role, phone="9999999999", is_active=True):
    user = User(
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
        is_deleted=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db) -> User:
    user = await _create_user(db, "admin@test.com", "Admin123!", UserRole.ADMIN)
    profile = AdminProfile(user_id=user.id, admin_name="Test Admin")
    db.add(profile)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def teacher_user(db) -> User:
    user = await _create_user(db, "teacher@test.com", "Teacher123!", UserRole.TEACHER)
    profile = TeacherProfile(
        user_id=user.id, teacher_name="Test Teacher", employee_code="TEA001"
    )
    db.add(profile)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def student_user(db) -> User:
    user = await _create_user(db, "student@test.com", "Student123!", UserRole.STUDENT)
    profile = StudentProfile(
        user_id=user.id,
        student_name="Test Student",
        admission_number="STU001",
        date_of_birth=datetime(2005, 1, 1),
        gender="MALE",
    )
    db.add(profile)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def admin_tokens(admin_user) -> dict:
    return create_auth_tokens(admin_user.id, UserRole.ADMIN.value)


@pytest_asyncio.fixture
async def teacher_tokens(teacher_user) -> dict:
    return create_auth_tokens(teacher_user.id, UserRole.TEACHER.value)


@pytest_asyncio.fixture
async def student_tokens(student_user) -> dict:
    return create_auth_tokens(student_user.id, UserRole.STUDENT.value)


@pytest_asyncio.fixture
async def admin_headers(admin_tokens) -> dict:
    return {"Authorization": f"Bearer {admin_tokens['access_token']}"}


@pytest_asyncio.fixture
async def teacher_headers(teacher_tokens) -> dict:
    return {"Authorization": f"Bearer {teacher_tokens['access_token']}"}


@pytest_asyncio.fixture
async def student_headers(student_tokens) -> dict:
    return {"Authorization": f"Bearer {student_tokens['access_token']}"}


@pytest_asyncio.fixture
async def academic_session(db) -> AcademicSession:
    ac = AcademicSession(
        session_code="2024-25",
        session_name="2024-2025",
        start_year=2024,
        end_year=2025,
        start_date=datetime(2024, 4, 1),
        end_date=datetime(2025, 3, 31),
        is_current=True,
    )
    db.add(ac)
    await db.commit()
    await db.refresh(ac)
    return ac


@pytest_asyncio.fixture
async def classroom(db, academic_session) -> ClassRoom:
    room = ClassRoom(
        class_code="10A",
        class_name="Class 10",
        section="A",
        display_name="Class 10-A",
        academic_sessions_id=academic_session.id,
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@pytest_asyncio.fixture
async def subject(db) -> Subject:
    subj = Subject(
        subject_code="MATH101",
        subject_name="Mathematics",
    )
    db.add(subj)
    await db.commit()
    await db.refresh(subj)
    return subj
