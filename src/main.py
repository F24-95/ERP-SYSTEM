import os
import time
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load environment variables from .env file BEFORE any other imports
# that call os.getenv(), so that all configs read from .env properly.
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Importing src.database.base (not just src.database.connection) is required
# here: it pulls in every domain's models.py so Base.metadata is fully
# populated before create_all() runs below. Importing only `connection`
# gives the same declarative Base object but with no tables registered on
# it yet if this module happens to import before any router/service chain
# does — so this import must stay even though nothing in it is referenced
# directly.
import src.database.base  # noqa: F401
from src.core.exceptions import BaseDomainException, global_exception_handler
from src.core.logger import get_logger, request_id_ctx
from src.database.connection import AsyncSessionLocal, Base, engine

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(request_id)

        start_time = time.time()
        logger.info(f"Incoming Request: {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"Completed Request: {request.method} {request.url.path} "
            f"Status: {response.status_code} Time: {process_time:.4f}s",
        )

        response.headers["X-Request-ID"] = request_id
        return response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Modern School ERP API",
        version="2.0.0",
        description="Enterprise-grade School Management System API",
    )

    # CORS - Restrict in production via CORS_ORIGINS env var
    cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins != ["*"] else ["*"],
        allow_credentials=cors_origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom Middleware
    app.add_middleware(RequestContextMiddleware)

    # Routers
    from src.api.routers.academics import router as academics_router
    from src.api.routers.admin import router as admin_router
    from src.api.routers.assignments import router as assignments_router
    from src.api.routers.attachments import router as attachments_router
    from src.api.routers.auth import router as auth_router
    from src.api.routers.chat import router as chat_router
    from src.api.routers.curriculum import router as curriculum_router
    from src.api.routers.daily_class import router as daily_class_router
    from src.api.routers.dashboard import router as dashboard_router
    from src.api.routers.exams import router as exams_router
    from src.api.routers.fees import router as fees_router
    from src.api.routers.id_cards import router as id_cards_router
    from src.api.routers.khan_academy import router as khan_academy_router
    from src.api.routers.notices import router as notices_router
    from src.api.routers.operations import router as operations_router
    from src.api.routers.reports import router as reports_router
    from src.api.routers.search import router as search_router

    # Merged in from the other project variant -- self-service portals,
    # role dashboards, and a generic polymorphic attachment store that
    # this branch was missing entirely.
    from src.api.routers.student import router as student_router
    from src.api.routers.study_material import router as study_material_router
    from src.api.routers.teacher import router as teacher_router
    from src.api.routers.timetable import router as timetable_router
    from src.api.routers.users import router as users_router
    from src.api.routers.zoom import router as zoom_router

    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(users_router)
    app.include_router(academics_router)
    app.include_router(operations_router)
    app.include_router(fees_router)
    app.include_router(exams_router)
    app.include_router(assignments_router)
    app.include_router(study_material_router)
    app.include_router(notices_router)
    app.include_router(daily_class_router)
    app.include_router(timetable_router)
    app.include_router(chat_router)
    app.include_router(curriculum_router)
    app.include_router(id_cards_router)
    app.include_router(search_router)
    app.include_router(khan_academy_router)
    app.include_router(zoom_router)
    app.include_router(reports_router)
    app.include_router(student_router)
    app.include_router(teacher_router)
    app.include_router(dashboard_router)
    app.include_router(attachments_router)

    # Exception Handlers
    app.add_exception_handler(BaseDomainException, global_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting up Modern School ERP API")
        # No Alembic migrations existed in this project at all (no
        # alembic/versions/, no script.py.mako) — meaning a fresh DB had
        # zero tables and every endpoint would fail. Alembic is now fixed
        # to actually work (see alembic/versions/README.md), but until an
        # initial migration is generated and run against a real DB, this
        # create_all() is the only thing that makes the app usable.
        # Set AUTO_CREATE_TABLES=false once Alembic migrations are the
        # source of truth (staging/production), so the two mechanisms don't
        # fight each other.
        if os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true":
            async with engine.begin() as conn:
                from sqlalchemy import text
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables ensured via Base.metadata.create_all()")

        # Every user-creation endpoint requires an existing admin
        # (require_role(ADMIN)), by design -- see the security fix note in
        # src/api/routers/users.py. That means a brand new deployment has
        # no way to get its first admin account through the API at all.
        # Surface that clearly on startup instead of leaving it as a silent
        # dead end the first person to try to log in would hit.
        try:
            from sqlalchemy import select

            from src.core.enums import UserRole
            from src.domain.users.models import User

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).filter_by(role=UserRole.ADMIN).limit(1),
                )
                if result.scalars().first() is None:
                    logger.warning(
                        "No admin account exists yet. Run: "
                        "python -m scripts.create_first_admin",
                    )
        except Exception:
            # Don't let this convenience check block startup if the DB
            # genuinely isn't reachable yet -- the app will fail loudly on
            # the first real request either way.
            logger.debug(
                "Could not check for an existing admin account at startup",
                exc_info=True,
            )
        yield
        logger.info("Shutting down Modern School ERP API")
        await engine.dispose()

    app.router.lifespan_context = lifespan

    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "healthy", "version": "2.0.0"}

    return app


app = create_app()
