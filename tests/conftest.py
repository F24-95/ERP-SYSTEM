import asyncio
import os
from collections.abc import AsyncGenerator
from datetime import date, time
from typing import Any

from dotenv import load_dotenv
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

load_dotenv()

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/erp_test",
    ),
)
if TEST_DATABASE_URL.startswith("postgresql://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )

os.environ.setdefault(
    "DATABASE_URL",
    TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1),
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("AUTO_CREATE_TABLES", "false")

from src.core.security import create_access_token, hash_password  # noqa: E402
from src.database.connection import Base, get_db  # noqa: E402
from src.main import create_app  # noqa: E402

from src.core.enums import UserRole  # noqa: E402
from src.domain.operations.models import TimeSlot, WeekDay  # noqa: E402
from src.domain.academics.models import AcademicSession, ClassRoom  # noqa: E402
from src.domain.curriculum.models import Subject  # noqa: E402
from src.domain.users.models import (  # noqa: E402
    AdminProfile,
    StudentProfile,
    TeacherProfile,
    User,
)

DEFAULT_PASSWORD = "TestPass123!"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        for code, name, order in [
            ("MON", "Monday", 1),
            ("TUE", "Tuesday", 2),
            ("WED", "Wednesday", 3),
            ("THU", "Thursday", 4),
            ("FRI", "Friday", 5),
            ("SAT", "Saturday", 6),
            ("SUN", "Sunday", 7),
        ]:
            session.add(WeekDay(day_code=code, day_name=name, display_order=order))

        for code, name, start, end, dur, order, is_break in [
            ("SLOT01", "Period 1", time(8, 0), time(8, 45), 45, 1, False),
            ("SLOT02", "Period 2", time(8, 45), time(9, 30), 45, 2, False),
            ("SLOT03", "Period 3", time(9, 30), time(10, 15), 45, 3, False),
            ("SLOT04", "Break", time(10, 15), time(10, 30), 15, 4, True),
            ("SLOT05", "Period 4", time(10, 30), time(11, 15), 45, 5, False),
            ("SLOT06", "Period 5", time(11, 15), time(12, 0), 45, 6, False),
            ("SLOT07", "Period 6", time(12, 0), time(12, 45), 45, 7, False),
        ]:
            session.add(
                TimeSlot(
                    slot_code=code,
                    slot_name=name,
                    start_time=start,
                    end_time=end,
                    duration_minutes=dur,
                    display_order=order,
                    is_break=is_break,
                )
            )
        await session.commit()

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    yield session
    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def override_get_db(db_session: AsyncSession):
    async def _override():
        yield db_session

    return _override


@pytest_asyncio.fixture
async def app(override_get_db) -> AsyncGenerator:
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    yield app


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _create_user(
    session: AsyncSession,
    email: str,
    role: UserRole,
    password: str = DEFAULT_PASSWORD,
    phone: str | None = None,
    **extra: Any,
) -> User:
    if phone is None:
        import secrets
        phone = f"98{secrets.randbelow(100000000):08d}"
    user = User(
        email=email,
        phone=phone,
        role=role,
        password_hash=hash_password(password),
        is_verified=True,
        **extra,
    )
    session.add(user)
    await session.flush()
    return user


async def _create_admin_profile(
    session: AsyncSession,
    user: User,
    admin_name: str = "Test Admin",
) -> AdminProfile:
    profile = AdminProfile(user_id=user.id, admin_name=admin_name)
    session.add(profile)
    await session.flush()
    return profile


async def _create_teacher_profile(
    session: AsyncSession,
    user: User,
    teacher_name: str = "Test Teacher",
) -> TeacherProfile:
    profile = TeacherProfile(user_id=user.id, teacher_name=teacher_name)
    session.add(profile)
    await session.flush()
    return profile


async def _create_student_profile(
    session: AsyncSession,
    user: User,
    student_name: str = "Test Student",
) -> StudentProfile:
    profile = StudentProfile(user_id=user.id, student_name=student_name)
    session.add(profile)
    await session.flush()
    return profile


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = await _create_user(
        db_session, "admin@test.com", UserRole.ADMIN, phone="9876543210"
    )
    await _create_admin_profile(db_session, user)
    user.admin_id = "ADM00001"
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def teacher_user(db_session: AsyncSession) -> User:
    user = await _create_user(
        db_session, "teacher@test.com", UserRole.TEACHER, phone="9876543211"
    )
    await _create_teacher_profile(db_session, user)
    user.teacher_id = "TEA00001"
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession) -> User:
    user = await _create_user(
        db_session, "student@test.com", UserRole.STUDENT, phone="9876543212"
    )
    await _create_student_profile(db_session, user)
    user.student_id = "STU00001"
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def parent_user(db_session: AsyncSession) -> User:
    user = await _create_user(
        db_session, "parent@test.com", UserRole.PARENT, phone="9876543213"
    )
    await db_session.flush()
    return user


async def _auth_token(user: User) -> str:
    return create_access_token({"sub": str(user.id), "role": user.role.value})


@pytest_asyncio.fixture
async def admin_token(admin_user: User) -> str:
    return await _auth_token(admin_user)


@pytest_asyncio.fixture
async def teacher_token(teacher_user: User) -> str:
    return await _auth_token(teacher_user)


@pytest_asyncio.fixture
async def student_token(student_user: User) -> str:
    return await _auth_token(student_user)


async def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(admin_token: str) -> dict[str, str]:
    return await _auth_headers(admin_token)


@pytest_asyncio.fixture
async def teacher_headers(teacher_token: str) -> dict[str, str]:
    return await _auth_headers(teacher_token)


@pytest_asyncio.fixture
async def student_headers(student_token: str) -> dict[str, str]:
    return await _auth_headers(student_token)


@pytest_asyncio.fixture
async def admin_client(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> AsyncClient:
    client.headers.update(admin_headers)
    return client


@pytest_asyncio.fixture
async def teacher_client(
    client: AsyncClient,
    teacher_headers: dict[str, str],
) -> AsyncClient:
    client.headers.update(teacher_headers)
    return client


@pytest_asyncio.fixture
async def student_client(
    client: AsyncClient,
    student_headers: dict[str, str],
) -> AsyncClient:
    client.headers.update(student_headers)
    return client


@pytest_asyncio.fixture
async def academic_session(db_session: AsyncSession) -> AcademicSession:
    sess = AcademicSession(
        session_code="SES-2026",
        session_name="2025-2026",
        start_year=2025,
        end_year=2026,
        start_date=date(2025, 4, 1),
        end_date=date(2026, 3, 31),
        is_current=True,
    )
    db_session.add(sess)
    await db_session.flush()
    return sess


@pytest_asyncio.fixture
async def classroom(
    academic_session: AcademicSession,
    db_session: AsyncSession,
) -> ClassRoom:
    cls = ClassRoom(
        class_code="CLS-10",
        class_name="Class 10",
        section="A",
        display_name="Class 10 - A",
        academic_sessions_id=academic_session.id,
    )
    db_session.add(cls)
    await db_session.flush()
    return cls


@pytest_asyncio.fixture
async def subject(db_session: AsyncSession) -> Subject:
    subj = Subject(
        subject_code="MATH",
        subject_name="Mathematics",
        display_order=1,
    )
    db_session.add(subj)
    await db_session.flush()
    return subj
