from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    id: int
    is_active: bool | None = None

    model_config = {"from_attributes": True}


# ===========================
# Chat Room
# ===========================
class ChatRoomBase(BaseModel):
    last_message: str | None = Field(None, max_length=500)
    last_message_at: datetime | None = None
    student_unread: int = 0
    teacher_unread: int = 0


class ChatRoomCreate(ChatRoomBase):
    # NOTE: chat_room_id is client-supplied here (schema requires it and the
    # legacy router always passes it through explicitly), even though the
    # model column also carries `default=generate_chat_room_id`. Same
    # precedent as ExamCreate.exam_id / ClassTimeTableCreate.timetable_id:
    # the column default exists but production behavior is client-supplied.
    chat_room_id: str = Field(..., max_length=30)
    academic_sessions_id: int
    student_class_id: int
    teacher_subject_id: int


class ChatRoomUpdate(BaseModel):
    last_message: str | None = Field(None, max_length=500)
    last_message_at: datetime | None = None
    student_unread: int | None = None
    teacher_unread: int | None = None
    is_active: bool | None = None


class ChatRoomResponse(ChatRoomBase, BaseResponse):
    chat_room_id: str
    academic_sessions_id: int
    student_class_id: int
    teacher_subject_id: int


# ===========================
# Chat Message
# ===========================
class ChatMessageBase(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    is_edited: bool = False
    edited_at: datetime | None = None


class ChatMessageCreate(ChatMessageBase):
    # NOTE: legacy's ChatMessageCreate also has a `sender_id` field, but the
    # actual router (`send_message`) ignores it entirely and always uses
    # `current_user.id` as the sender. Preserved: no sender_id field is
    # accepted here since the client-supplied value was never honored in
    # production, and there's no reason to invite spoofed values in for a
    # field that isn't used.
    pass


class ChatMessageEdit(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)


class ChatMessageResponse(ChatMessageBase, BaseResponse):
    chat_room_id: int
    sender_id: int


class ChatConversationResponse(BaseModel):
    chat_room: ChatRoomResponse
    messages: list[ChatMessageResponse] = []


class ChatUnreadCountResponse(BaseModel):
    total_unread: int = 0
    rooms: list[dict[str, Any]] = []
