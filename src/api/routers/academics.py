from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.academics.schemas import (
    AcademicSessionCreate,
    AcademicSessionResponse,
    AcademicSessionUpdate,
    ClassRoomCreate,
    ClassRoomResponse,
    ClassRoomUpdate,
    ClassSubjectCreate,
    ClassSubjectResponse,
    ClassSubjectUpdate,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)
from src.domain.academics.service import (
    AcademicSessionService,
    ClassRoomService,
    ClassSubjectService,
    SubjectService,
)

router = APIRouter(prefix="/academics", tags=["Academics"])

# ============================================================
# Academic Sessions
# ============================================================


@router.post(
    "/sessions",
    response_model=AcademicSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    data: AcademicSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    return await AcademicSessionService.create(db, data)


@router.get("/sessions", response_model=list[AcademicSessionResponse])
async def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    items, _total = await AcademicSessionService.list(db, skip=skip, limit=limit)
    return items


@router.get("/sessions/{session_id}", response_model=AcademicSessionResponse)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    return await AcademicSessionService.get(db, session_id)


@router.put("/sessions/{session_id}", response_model=AcademicSessionResponse)
async def update_session(
    session_id: int,
    data: AcademicSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    return await AcademicSessionService.update(db, session_id, data)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    await AcademicSessionService.deactivate(db, session_id)


# ============================================================
# ClassRooms
# ============================================================


@router.post(
    "/classrooms",
    response_model=ClassRoomResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_classroom(
    data: ClassRoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    return await ClassRoomService.create(db, data)


@router.get("/classrooms", response_model=list[ClassRoomResponse])
async def list_classrooms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    academic_sessions_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    items, _total = await ClassRoomService.list(
        db,
        skip=skip,
        limit=limit,
        academic_sessions_id=academic_sessions_id,
    )
    return items


@router.get("/classrooms/{classroom_id}", response_model=ClassRoomResponse)
async def get_classroom(classroom_id: int, db: AsyncSession = Depends(get_db)):
    return await ClassRoomService.get(db, classroom_id)


@router.put("/classrooms/{classroom_id}", response_model=ClassRoomResponse)
async def update_classroom(
    classroom_id: int,
    data: ClassRoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    return await ClassRoomService.update(db, classroom_id, data)


@router.delete("/classrooms/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_classroom(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    await ClassRoomService.deactivate(db, classroom_id)


# ============================================================
# Subjects
# ============================================================


@router.post(
    "/subjects",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subject(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    return await SubjectService.create(db, data)


@router.get("/subjects", response_model=list[SubjectResponse])
async def list_subjects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    items, _total = await SubjectService.list(db, skip=skip, limit=limit)
    return items


@router.get("/subjects/{subject_id}", response_model=SubjectResponse)
async def get_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    return await SubjectService.get(db, subject_id)


@router.put("/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    data: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    return await SubjectService.update(db, subject_id, data)


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_subject(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    await SubjectService.deactivate(db, subject_id)


# ============================================================
# Class-Subjects (classroom <-> subject mapping for a session)
# ------------------------------------------------------------
# This resource previously had NO API at all -- no schemas, no crud
# instance, no router. It's a hard dependency for other domains:
# TeacherSubject.class_subject_id and StudyMaterial.class_subject_id are
# both required foreign keys here, so without this endpoint teachers could
# never be assigned to a class+subject and study material could never be
# uploaded.
# ============================================================


@router.post(
    "/class-subjects",
    response_model=ClassSubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_class_subject(
    data: ClassSubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    return await ClassSubjectService.create(db, data)


@router.get("/class-subjects", response_model=list[ClassSubjectResponse])
async def list_class_subjects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    classroom_id: int | None = None,
    academic_sessions_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    items, _total = await ClassSubjectService.list(
        db,
        skip=skip,
        limit=limit,
        classroom_id=classroom_id,
        academic_sessions_id=academic_sessions_id,
    )
    return items


@router.get("/class-subjects/{class_subject_id}", response_model=ClassSubjectResponse)
async def get_class_subject(class_subject_id: int, db: AsyncSession = Depends(get_db)):
    return await ClassSubjectService.get(db, class_subject_id)


@router.put("/class-subjects/{class_subject_id}", response_model=ClassSubjectResponse)
async def update_class_subject(
    class_subject_id: int,
    data: ClassSubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    return await ClassSubjectService.update(db, class_subject_id, data)


@router.delete(
    "/class-subjects/{class_subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_class_subject(
    class_subject_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    await ClassSubjectService.deactivate(db, class_subject_id)
