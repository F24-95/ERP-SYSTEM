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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, AuditMixin, TimestampMixin


class AcademicSession(Base, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "academic_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_code = Column(String(30), unique=True, nullable=False, index=True)
    session_name = Column(String(20), unique=True, nullable=False)
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False, nullable=False, index=True)
    description = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("end_year > start_year", name="ck_session_year"),
        Index("idx_session_name", "session_name"),
        Index("idx_session_active", "is_current"),
        UniqueConstraint("session_name", name="uq_session_name"),
    )

    classrooms = relationship(
        "ClassRoom",
        back_populates="academic_session",
        cascade="all, delete-orphan",
    )
    class_subjects = relationship(
        "ClassSubject",
        back_populates="academic_session",
        cascade="all, delete-orphan",
    )


class ClassRoom(Base, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "classroom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_code = Column(String(30), nullable=False)
    class_name = Column(String(100), nullable=False)
    section = Column(String(30), nullable=False)
    display_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    class_teacher_id = Column(
        String(30),
        nullable=True,
        index=True,
    )  # Teacher ID string

    academic_session = relationship("AcademicSession", back_populates="classrooms")
    class_subjects = relationship(
        "ClassSubject",
        back_populates="classroom",
        cascade="all, delete-orphan",
    )
    topics = relationship("Topic", back_populates="classroom")
    zoom_files = relationship("ZoomFile", back_populates="classroom")

    __table_args__ = (
        UniqueConstraint(
            "academic_sessions_id",
            "class_code",
            name="uq_classroom_session_classcode",
        ),
        UniqueConstraint(
            "academic_sessions_id",
            "display_name",
            name="uq_classroom_session_display",
        ),
        UniqueConstraint("academic_sessions_id", "class_name", "section"),
        Index("idx_classroom_code", "class_code"),
        Index("idx_classroom_name", "class_name"),
        Index("idx_classroom_section", "section"),
        Index("idx_classroom_session", "academic_sessions_id"),
        Index("idx_classroom_teacher", "class_teacher_id"),
        Index("idx_classroom_active", "is_active"),
    )


class ClassSubject(Base, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "class_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    classroom_id = Column(
        Integer,
        ForeignKey("classroom.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    display_order = Column(Integer, default=1, nullable=False)

    academic_session = relationship("AcademicSession", back_populates="class_subjects")
    classroom = relationship("ClassRoom", back_populates="class_subjects")
    subject = relationship("Subject", back_populates="class_subjects")

    __table_args__ = (
        UniqueConstraint(
            "academic_sessions_id",
            "classroom_id",
            "subject_id",
            name="uq_class_subject",
        ),
        Index("idx_class_subject_class", "classroom_id"),
        Index("idx_class_subject_subject", "subject_id"),
        Index("idx_class_subject_session", "academic_sessions_id"),
        Index("idx_class_subject_active", "is_active"),
    )
