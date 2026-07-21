from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.chat.schemas import (
    ChatMessageCreate,
    ChatMessageEdit,
    ChatMessageResponse,
    ChatRoomCreate,
    ChatRoomResponse,
    ChatRoomUpdate,
    ChatUnreadCountResponse,
)
from src.domain.chat.service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/rooms", response_model=ChatRoomResponse)
async def create_chat_room(
    room_data: ChatRoomCreate,
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a chat room between teacher and student."""
    return await ChatService.create_chat_room(db, room_data, current_user)


@router.get("/rooms", response_model=list[ChatRoomResponse])
async def get_chat_rooms(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat rooms for the current user."""
    return await ChatService.get_chat_rooms(db, current_user)


@router.get("/rooms/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room(
    room_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat room by ID. Only a participant (or admin) may view it --
    previously anyone authenticated could view (and, via the other
    endpoints, read/send messages in) any room in the system.
    """
    return await ChatService.get_chat_room(db, room_id, current_user)


@router.put("/rooms/{room_id}", response_model=ChatRoomResponse)
async def update_chat_room(
    room_id: int,
    data: ChatRoomUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a chat room. Was missing entirely -- the ChatRoomUpdate
    schema already existed with nothing using it.
    """
    return await ChatService.update_chat_room(
        db,
        room_id,
        data.model_dump(exclude_unset=True),
        current_user,
    )


@router.delete("/rooms/{room_id}", status_code=204)
async def archive_chat_room(
    room_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive a chat room. Was missing entirely -- a room, once created,
    could never be closed by either participant or an admin.
    """
    await ChatService.archive_chat_room(db, room_id, current_user)


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    room_id: int,
    message_data: ChatMessageCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in a chat room."""
    return await ChatService.send_message(
        db,
        room_id,
        message_data.message,
        current_user,
    )


@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    room_id: int,
    limit: int = Query(50, ge=1, le=200),
    before: datetime | None = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages in a chat room (also marks the room as read for the caller's role)."""
    return await ChatService.get_messages(
        db,
        room_id,
        current_user,
        limit=limit,
        before=before,
    )


@router.put(
    "/rooms/{room_id}/messages/{message_id}",
    response_model=ChatMessageResponse,
)
async def edit_message(
    room_id: int,
    message_id: int,
    data: ChatMessageEdit,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit your own message. Was missing entirely -- ChatMessage already
    had is_edited/edited_at columns, but nothing ever set them.
    """
    return await ChatService.edit_message(
        db,
        room_id,
        message_id,
        data.message,
        current_user,
    )


@router.delete("/rooms/{room_id}/messages/{message_id}", status_code=204)
async def delete_message(
    room_id: int,
    message_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete your own message. Was missing entirely."""
    await ChatService.delete_message(db, room_id, message_id, current_user)


@router.get("/unread", response_model=ChatUnreadCountResponse)
async def get_unread_counts(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unread message counts for the current user."""
    return await ChatService.get_unread_counts(db, current_user)
