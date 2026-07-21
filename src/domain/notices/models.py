from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from src.core.enums import NoticeAudience, NoticeType
from src.core.id_generators import generate_notice_code
from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, TimestampMixin


class Notice(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True)
    notice_id = Column(
        String(30),
        unique=True,
        nullable=False,
        default=generate_notice_code,
        index=True,
    )

    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id"),
        nullable=False,
        index=True,
    )
    classroom_id = Column(
        Integer,
        ForeignKey("classroom.id"),
        nullable=True,
        index=True,
    )

    title = Column(String(250), nullable=False)
    description = Column(Text, nullable=False)
    notice_type = Column(
        SAEnum(NoticeType),
        nullable=False,
        default=NoticeType.GENERAL,
        index=True,
    )
    audience = Column(
        SAEnum(NoticeAudience),
        nullable=False,
        default=NoticeAudience.ALL,
        index=True,
    )

    publish_date = Column(Date, nullable=False, index=True)
    expiry_date = Column(Date, nullable=True, index=True)

    attachment_name = Column(String(255), nullable=True)
    attachment_path = Column(String(500), nullable=True)
    attachment_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    is_pinned = Column(Boolean, default=False, nullable=False, index=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    academic_sessions = relationship("AcademicSession")
    classroom = relationship("ClassRoom", foreign_keys=[classroom_id])

    __table_args__ = (
        Index("idx_notice_publish", "publish_date", "audience"),
        Index("idx_notice_class", "classroom_id", "publish_date"),
        Index("idx_notice_pin", "is_pinned", "publish_date"),
        CheckConstraint(
            "(expiry_date IS NULL) OR (expiry_date >= publish_date)",
            name="ck_notice_expiry",
        ),
    )
