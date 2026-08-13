from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.core.id_generators import generate_topic_id
from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, AuditMixin, TimestampMixin


class Subject(Base, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_code = Column(String(30), nullable=False, unique=True, index=True)
    subject_name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=1, nullable=False)
    subject_type = Column(String(20), default="Core", nullable=False)

    class_subjects = relationship(
        "ClassSubject",
        back_populates="subject",
        cascade="all, delete-orphan",
    )
    topics = relationship(
        "Topic",
        back_populates="subject",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("subject_name", name="uq_subject_name"),
        UniqueConstraint("subject_code", name="uq_subject_code"),
        Index("idx_subject_name", "subject_name"),
        Index("idx_subject_active", "is_active"),
    )


class Topic(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "ka_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(
        String(30),
        unique=True,
        nullable=False,
        default=generate_topic_id,
        index=True,
    )

    ka_topic_id = Column(String(200), unique=True, nullable=False, index=True)
    topic_name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=1, nullable=False)

    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    classroom_id = Column(
        Integer,
        ForeignKey("classroom.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    subject = relationship("Subject", back_populates="topics")
    classroom = relationship("ClassRoom", back_populates="topics")
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_topics",
    )
    updater = relationship(
        "User",
        foreign_keys=[updated_by],
        back_populates="updated_topics",
    )

    ka_subject_activities = relationship(
        "KaSubjectActivity",
        back_populates="topic",
        cascade="all, delete-orphan",
    )
    ka_topic_progress_entries = relationship(
        "KaTopicProgress",
        back_populates="topic",
        cascade="all, delete-orphan",
    )
    report_links = relationship(
        "StudentTopicProgressReport",
        back_populates="topic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("ka_topic_id", name="uq_ka_topic_topic_id"),
        UniqueConstraint(
            "subject_id",
            "classroom_id",
            "topic_name",
            name="uq_topic_subject_classroom_name",
        ),
        Index("idx_ka_topic_subject", "subject_id"),
        Index("idx_ka_topic_classroom", "classroom_id"),
        Index("idx_ka_topic_name", "topic_name"),
        Index("idx_ka_topic_active", "is_active"),
    )


# Late imports to register all cross-module classes with Base before
# SQLAlchemy mapper configuration. Subject and Topic have string-based
# relationships that reference models in other domains (ClassSubject,
# ClassRoom, KaSubjectActivity, KaTopicProgress, User, etc.), and those
# classes must be registered before any mapper is configured at query time.
from src.domain.academics import models as _academics_models  # noqa: E402, F401
from src.domain.khan_academy import models as _ka_models  # noqa: E402, F401
from src.domain.reports import models as _reports_models  # noqa: E402, F401
