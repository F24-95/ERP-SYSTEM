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

from src.core.enums import ExamStatus
from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, AuditMixin, TimestampMixin


class Exam(Base, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True)
    exam_id = Column(String(30), unique=True, nullable=False, index=True)

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

    exam_name = Column(String(150), nullable=False)
    exam_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    exam_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    room_number = Column(String(50), nullable=True)

    total_marks = Column(Float, nullable=False)
    passing_marks = Column(Float, nullable=False)

    status = Column(
        SAEnum(ExamStatus),
        default=ExamStatus.DRAFT,
        nullable=False,
        index=True,
    )
    publish_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    total_students = Column(Integer, default=0)
    result_uploaded = Column(Integer, default=0)

    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    academic_sessions = relationship("AcademicSession")
    classroom = relationship("ClassRoom")
    class_subject = relationship("ClassSubject")
    teacher_subject = relationship("TeacherSubject")

    results = relationship(
        "ExamResult",
        back_populates="exam",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "class_subject_id", "exam_name", "exam_date",
            name="uq_exam",
        ),
        Index("idx_exam_class", "classroom_id", "exam_date"),
        Index("idx_exam_teacher", "teacher_subject_id", "status"),
    )


class ExamResult(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True)
    exam_id = Column(
        Integer,
        ForeignKey("exams.id"),
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
    rank_in_class = Column(Integer, nullable=True)
    is_absent = Column(Boolean, default=False)

    checked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    checked_at = Column(DateTime, nullable=True)

    exam = relationship("Exam", back_populates="results")
    student_class = relationship("StudentClass")

    __table_args__ = (
        UniqueConstraint(
            "exam_id", "student_class_id",
            name="uq_exam_result",
        ),
        Index("idx_exam_result", "student_class_id", "exam_id"),
        Index("idx_exam_rank", "exam_id", "rank_in_class"),
    )
