from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import AuthorizationException, ResourceNotFoundException
from src.core.logger import get_logger
from src.domain.chat.crud import chat_message_crud, chat_room_crud
from src.domain.chat.models import ChatMessage, ChatRoom
from src.domain.chat.schemas import ChatRoomCreate
from src.domain.operations.models import StudentClass, TeacherSubject
from src.domain.users.models import StudentProfile, TeacherProfile, User

logger = get_logger(__name__)


class ChatService:
    """Chat room + message logic, ported from `app/routers/chat_routers.py`
    (the legacy `chat_service.py` is a 0-byte file — same "router is the
    source of truth" pattern as attendance/daily-class in Phase 2f).
    """

    @staticmethod
    async def create_chat_room(
        db: AsyncSession,
        data: ChatRoomCreate,
        current_user: User,
    ) -> ChatRoom:
        teacher = await db.scalar(
            select(TeacherProfile).filter_by(user_id=current_user.id),
        )
        if not teacher:
            raise ResourceNotFoundException("Teacher profile not found")

        teacher_subject = await db.scalar(
            select(TeacherSubject).filter_by(
                id=data.teacher_subject_id,
                teacher_id=current_user.id,
            ),
        )
        if not teacher_subject:
            raise AuthorizationException("You are not assigned to this class")

        existing = await db.scalar(
            select(ChatRoom).filter_by(
                student_class_id=data.student_class_id,
                teacher_subject_id=data.teacher_subject_id,
            ),
        )
        if existing:
            return existing

        new_room = await chat_room_crud.create(db, data.model_dump())
        logger.info(
            f"Chat room created: {new_room.chat_room_id} by teacher user={current_user.id}",
        )
        return new_room

    @staticmethod
    async def update_chat_room(
        db: AsyncSession,
        room_id: int,
        data: dict,
        current_user: User,
    ) -> ChatRoom:
        """ChatRoomUpdate schema already existed but had zero service
        method or router endpoint using it -- dead schema.
        """
        room = await ChatService.get_chat_room(db, room_id, current_user)
        if not data:
            return room
        return await chat_room_crud.update(db, room_id, data)

    @staticmethod
    async def archive_chat_room(
        db: AsyncSession,
        room_id: int,
        current_user: User,
    ) -> None:
        """Was missing entirely -- a chat room, once created, could never
        be archived/closed by either participant or an admin.
        """
        await ChatService.get_chat_room(db, room_id, current_user)
        await chat_room_crud.update(db, room_id, {"is_active": False})
        logger.info(
            f"Chat room archived: id={room_id} by user={current_user.id}"
        )

    @staticmethod
    async def get_chat_rooms(
        db: AsyncSession,
        current_user: User,
    ) -> list[ChatRoom]:
        # NOTE: legacy's `get_chat_rooms` never initializes `rooms` in the
        # TEACHER branch when no TeacherProfile exists for the user, and the
        # same gap exists implicitly if a lookup fails partway — that path
        # raises UnboundLocalError in the old code. Fixed here by defaulting
        # to an empty list, matching the (working) STUDENT branch's fallback
        # behavior for the equivalent case.
        rooms: list[ChatRoom] = []

        if current_user.role == UserRole.TEACHER:
            teacher = await db.scalar(
                select(TeacherProfile).filter_by(user_id=current_user.id),
            )
            if teacher:
                subject_ids = select(TeacherSubject.id).filter(
                    TeacherSubject.teacher_id == current_user.id,
                )
                result = await db.execute(
                    select(ChatRoom).filter(
                        ChatRoom.teacher_subject_id.in_(subject_ids),
                    ),
                )
                rooms = list(result.scalars().all())
        elif current_user.role == UserRole.STUDENT:
            student = await db.scalar(
                select(StudentProfile).filter_by(user_id=current_user.id),
            )
            if student:
                # Legacy takes the first matching StudentClass row (assumes
                # one active class per student), preserved as-is.
                student_class = await db.scalar(
                    select(StudentClass).filter_by(student_id=current_user.id),
                )
                if student_class:
                    result = await db.execute(
                        select(ChatRoom).filter_by(
                            student_class_id=student_class.id,
                        ),
                    )
                    rooms = list(result.scalars().all())
        else:
            result = await db.execute(select(ChatRoom))
            rooms = list(result.scalars().all())

        return rooms

    @staticmethod
    async def _check_room_membership(
        db: AsyncSession,
        room: ChatRoom,
        current_user: User,
    ) -> None:
        """Was missing everywhere -- get_chat_room/send_message/get_messages
        never verified the caller was actually a participant in the room at
        all. Any authenticated user (any student, any teacher) could read
        the full message history of, and send messages into, *any* chat
        room in the system just by guessing/incrementing a room_id -- a
        severe privacy hole, and worse than the exam/assignment result
        leaks fixed earlier since it's read+write, not just read.
        """
        if current_user.role == UserRole.ADMIN:
            return
        if current_user.role == UserRole.TEACHER:
            owns = await db.scalar(
                select(TeacherSubject).filter_by(
                    id=room.teacher_subject_id,
                    teacher_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException(
                    "You are not a participant in this chat room",
                )
            return
        if current_user.role == UserRole.STUDENT:
            owns = await db.scalar(
                select(StudentClass).filter_by(
                    id=room.student_class_id,
                    student_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException(
                    "You are not a participant in this chat room",
                )
            return
        raise AuthorizationException("Permission denied")

    @staticmethod
    async def get_chat_room(
        db: AsyncSession,
        room_id: int,
        current_user: User | None = None,
    ) -> ChatRoom:
        room = await chat_room_crud.get(db, room_id)
        if not room:
            raise ResourceNotFoundException("Chat room not found")
        if current_user is not None:
            await ChatService._check_room_membership(db, room, current_user)
        return room

    @staticmethod
    async def send_message(
        db: AsyncSession,
        room_id: int,
        message: str,
        current_user: User,
    ) -> ChatMessage:
        room = await ChatService.get_chat_room(db, room_id, current_user)

        new_message = ChatMessage(
            chat_room_id=room_id,
            sender_id=current_user.id,
            message=message,
            is_edited=False,
        )
        db.add(new_message)

        room.last_message = message[:500]
        room.last_message_at = datetime.utcnow()

        if current_user.role == UserRole.TEACHER:
            room.student_unread = (room.student_unread or 0) + 1
        elif current_user.role == UserRole.STUDENT:
            room.teacher_unread = (room.teacher_unread or 0) + 1

        await db.flush()
        logger.info(
            f"Message sent in room={room_id} by user={current_user.id}"
        )
        return new_message

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        room_id: int,
        current_user: User,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[ChatMessage]:
        room = await ChatService.get_chat_room(db, room_id, current_user)

        query = select(ChatMessage).filter(
            ChatMessage.chat_room_id == room_id
        )
        if before:
            query = query.filter(ChatMessage.created_at < before)
        query = query.order_by(
            ChatMessage.created_at.desc()
        ).limit(limit)

        result = await db.execute(query)
        messages = list(result.scalars().all())
        messages.reverse()  # chronological order, matching legacy

        # Mark as read, matching legacy exactly.
        if current_user.role == UserRole.TEACHER:
            room.student_unread = 0
        elif current_user.role == UserRole.STUDENT:
            room.teacher_unread = 0
        await db.flush()

        return messages

    @staticmethod
    async def edit_message(
        db: AsyncSession,
        room_id: int,
        message_id: int,
        new_text: str,
        current_user: User,
    ) -> ChatMessage:
        """Was missing entirely -- ChatMessage.is_edited/edited_at columns
        already existed on the model (clearly intended), but no endpoint
        ever set them because there was no edit endpoint at all.
        """
        message = await chat_message_crud.get(db, message_id)
        if not message or message.chat_room_id != room_id:
            raise ResourceNotFoundException("Message not found")
        if message.sender_id != current_user.id:
            raise AuthorizationException(
                "You can only edit your own messages"
            )

        message.message = new_text
        message.is_edited = True
        message.edited_at = datetime.utcnow()
        await db.flush()
        logger.info(
            f"Message edited: id={message_id} by user={current_user.id}"
        )
        return message

    @staticmethod
    async def delete_message(
        db: AsyncSession,
        room_id: int,
        message_id: int,
        current_user: User,
    ) -> None:
        """Was missing entirely. Deactivates (is_active=False) rather than
        hard-deleting so message history/read-receipts logic isn't disrupted
        -- same ActiveMixin-based convention used everywhere else in this
        project instead of removing the row.
        """
        message = await chat_message_crud.get(db, message_id)
        if not message or message.chat_room_id != room_id:
            raise ResourceNotFoundException("Message not found")
        if (
            message.sender_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            raise AuthorizationException(
                "You can only delete your own messages"
            )

        await chat_message_crud.update(
            db, message_id, {"is_active": False}
        )
        logger.info(
            f"Message deleted: id={message_id} by user={current_user.id}"
        )

    @staticmethod
    async def get_unread_counts(
        db: AsyncSession,
        current_user: User,
    ) -> dict[str, Any]:
        total_unread = 0
        room_counts: list[dict[str, Any]] = []

        if current_user.role == UserRole.TEACHER:
            teacher = await db.scalar(
                select(TeacherProfile).filter_by(user_id=current_user.id),
            )
            if teacher:
                subject_ids = select(TeacherSubject.id).filter(
                    TeacherSubject.teacher_id == current_user.id,
                )
                result = await db.execute(
                    select(ChatRoom).filter(
                        ChatRoom.teacher_subject_id.in_(subject_ids),
                    ),
                )
                rooms = list(result.scalars().all())
                total_unread = sum(r.student_unread for r in rooms)
                room_counts = [
                    {
                        "room_id": r.id,
                        "unread": r.student_unread,
                        "student_class": r.student_class_id,
                    }
                    for r in rooms
                ]
        elif current_user.role == UserRole.STUDENT:
            student = await db.scalar(
                select(StudentProfile).filter_by(user_id=current_user.id),
            )
            if student:
                student_class = await db.scalar(
                    select(StudentClass).filter_by(
                        student_id=current_user.id
                    ),
                )
                if student_class:
                    result = await db.execute(
                        select(ChatRoom).filter_by(
                            student_class_id=student_class.id
                        ),
                    )
                    rooms = list(result.scalars().all())
                    total_unread = sum(
                        r.teacher_unread for r in rooms
                    )
                    room_counts = [
                        {
                            "room_id": r.id,
                            "unread": r.teacher_unread,
                            "teacher": r.teacher_subject_id,
                        }
                        for r in rooms
                    ]

        return {
            "total_unread": total_unread,
            "rooms": room_counts,
        }
