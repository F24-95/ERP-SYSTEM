from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.common.schemas import MessageResponse
from src.domain.curriculum.schemas import (
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
    TopicCreate,
    TopicResponse,
    TopicUpdate,
)
from src.domain.curriculum.service import SubjectService, TopicService

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])


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


@router.delete("/subjects/{subject_id}", response_model=MessageResponse)
async def deactivate_subject(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    await SubjectService.deactivate(db, subject_id)
    return MessageResponse(message="Subject deactivated")


@router.post("/topics", response_model=TopicResponse)
async def create_topic(
    data: TopicCreate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    return await TopicService.create_topic(db, data.model_dump())


@router.get("/topics", response_model=list[TopicResponse])
async def list_topics(
    subject_id: int | None = None,
    classroom_id: int | None = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TopicService.list_topics(
        db,
        subject_id=subject_id,
        classroom_id=classroom_id,
    )


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TopicService.get_topic(db, topic_id)


@router.put("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: int,
    data: TopicUpdate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    return await TopicService.update_topic(
        db,
        topic_id,
        data.model_dump(exclude_unset=True),
    )


@router.delete("/topics/{topic_id}")
async def delete_topic(
    topic_id: int,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await TopicService.delete_topic(db, topic_id)
    return {"success": True, "message": "Topic deactivated"}
