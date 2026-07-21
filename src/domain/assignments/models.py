from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from src.core.enums import AssignmentStatus
from src.core.id_generators import generate_assignment_id
from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, TimestampMixin


class Assignment(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(
        String(30),
        unique=True,
        nullable=False,
        default=generate_assignment_id,
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
        nullable=False,
        index=True,
    )
    class_subject_id = Column(
        Integer,
        ForeignKey("class_subjects.id"),
        nullable=False,
        index=True,
    )
    teacher_subject_id = Column(
        Integer,
        ForeignKey("teacher_subjects.id"),
        nullable=False,
        index=True,
    )

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    due_date = Column(Date, nullable=False, index=True)
    due_time = Column(Time, nullable=True)
    total_marks = Column(Float, nullable=False, default=0)
    passing_marks = Column(Float, nullable=False, default=0)

    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    status = Column(
        SAEnum(AssignmentStatus),
        nullable=False,
        default=AssignmentStatus.DRAFT,
        index=True,
    )
    publish_at = Column(DateTime, nullable=True)
    close_at = Column(DateTime, nullable=True)

    total_students = Column(Integer, default=0)
    checked_students = Column(Integer, default=0)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    academic_sessions = relationship("AcademicSession")
    classroom = relationship("ClassRoom")
    class_subject = relationship("ClassSubject")
    teacher_subject = relationship("TeacherSubject")

    results = relationship(
        "AssignmentResult",
        back_populates="assignment",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("class_subject_id", "title", "due_date", name="uq_assignment"),
        Index("idx_assignment_class", "classroom_id", "due_date"),
        Index("idx_assignment_teacher", "teacher_subject_id", "status"),
        Index("idx_assignment_session", "academic_sessions_id", "status"),
    )


class AssignmentResult(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "assignment_results"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(
        Integer,
        ForeignKey("assignments.id"),
        nullable=False,
        index=True,
    )
    student_class_id = Column(
        Integer,
        ForeignKey("student_classes.id"),
        nullable=False,
        index=True,
    )

    obtained_marks = Column(Float, nullable=False, default=0)
    percentage = Column(Float, default=0)
    grade = Column(String(10), nullable=True)
    remarks = Column(Text, nullable=True)

    is_checked = Column(Boolean, default=False, nullable=False)
    checked_at = Column(DateTime, nullable=True)
    checked_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    assignment = relationship("Assignment", back_populates="results")
    student_class = relationship("StudentClass")

    __table_args__ = (
        UniqueConstraint(
            "assignment_id",
            "student_class_id",
            name="uq_assignment_result",
        ),
        Index("idx_assignment_result", "student_class_id", "is_checked"),
    )
