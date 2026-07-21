import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# PostgreSQL connection — DATABASE_URL must be set in .env or environment.
# Expected format: postgresql://user:password@host:port/dbname
_DATABASE_URL = os.getenv("DATABASE_URL")
if not _DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Please set it in your .env file or environment. "
        "Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/dbname",
    )

DATABASE_URL = _DATABASE_URL

# Replace postgresql:// with postgresql+asyncpg:// if necessary
# Handle all common postgresql prefixes
if DATABASE_URL.startswith("postgresql+psycopg://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql+psycopg://",
        "postgresql+asyncpg://",
        1,
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true",
    future=True,
    # pool_size and max_overflow can be configured here for Postgres
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function for FastAPI to get async DB sessions.

    Commits on a clean request, rolls back on any exception, always closes.
    (Previously this only rolled back on error and never committed on
    success -- since services only call session.flush(), not .commit(),
    every write across the API was silently discarded when the session
    closed at the end of the request. A couple of routers worked around
    it locally with their own explicit db.commit() call; everything else
    was actually not persisting.)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
