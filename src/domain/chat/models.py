from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.core.id_generators import generate_chat_room_id
from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, TimestampMixin


class ChatRoom(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True)
    chat_room_id = Column(
        String(30),
        unique=True,
        nullable=False,
        default=generate_chat_room_id,
        index=True,
    )

    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id"),
        nullable=False,
        index=True,
    )
    student_class_id = Column(
        Integer,
        ForeignKey("student_classes.id"),
        nullable=False,
        index=True,
    )
    teacher_subject_id = Column(
        Integer,
        ForeignKey("teacher_subjects.id"),
        nullable=False,
        index=True,
    )

    last_message = Column(String(500))
    last_message_at = Column(DateTime)
    student_unread = Column(Integer, default=0, nullable=False)
    teacher_unread = Column(Integer, default=0, nullable=False)

    messages = relationship(
        "ChatMessage",
        back_populates="chat_room",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("student_class_id", "teacher_subject_id", name="uq_chat_room"),
        Index("idx_chat_room", "teacher_subject_id", "student_class_id"),
    )


class ChatMessage(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    chat_room_id = Column(
        Integer,
        ForeignKey("chat_rooms.id"),
        nullable=False,
        index=True,
    )
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    message = Column(Text, nullable=False)
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime)

    chat_room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User")

    __table_args__ = (Index("idx_chat_message", "chat_room_id", "created_at"),)
