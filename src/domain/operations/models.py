from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
from sqlalchemy.orm import relationship

from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, AuditMixin, TimestampMixin


# ============================================================
# TEACHER SUBJECT (Assignment)
# ============================================================
class TeacherSubject(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "teacher_subjects"

    id = Column(Integer, primary_key=True, index=True)
    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_subject_id = Column(
        Integer,
        ForeignKey("class_subjects.id", ondelete="CASCADE"),
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
    teacher_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # Changed from string to integer (user PK) to enforce true FK
    is_class_teacher = Column(Boolean, default=False, nullable=False)
    remarks = Column(String(300), nullable=True)

    academic_session = relationship("AcademicSession")
    class_subject = relationship("ClassSubject")
    classroom = relationship("ClassRoom")
    subject = relationship("Subject")
    teacher = relationship("User", foreign_keys=[teacher_id])

    __table_args__ = (
        UniqueConstraint(
            "academic_sessions_id",
            "classroom_id",
            "subject_id",
            name="uq_teacher_subject",
        ),
        Index("idx_teacher_subject_teacher", "teacher_id"),
        Index("idx_teacher_subject_class", "classroom_id"),
        Index("idx_teacher_subject_subject", "subject_id"),
    )


# ============================================================
# STUDENT CLASS (Enrollment)
# ============================================================
class StudentClass(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "student_classes"

    id = Column(Integer, primary_key=True, index=True)
    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # Changed from string to Integer (user PK) to enforce true FK
    classroom_id = Column(
        Integer,
        ForeignKey("classroom.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    roll_number = Column(Integer, nullable=False, index=True)
    admission_date = Column(Date, nullable=False)
    status = Column(String(30), nullable=False, default="ACTIVE", index=True)
    roll_number_locked = Column(Boolean, default=False, nullable=False)
    remarks = Column(String(500), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "academic_sessions_id",
            "student_id",
            name="uq_student_session",
        ),
        UniqueConstraint(
            "academic_sessions_id",
            "classroom_id",
            "roll_number",
            name="uq_roll_class",
        ),
        Index("idx_studentclass_student", "student_id"),
        Index("idx_studentclass_roll", "roll_number"),
        Index("idx_studentclass_class", "classroom_id"),
        Index("idx_studentclass_session", "academic_sessions_id"),
        Index("idx_studentclass_status", "status"),
    )

    academic_session = relationship("AcademicSession")
    student = relationship("User", foreign_keys=[student_id])
    classroom = relationship("ClassRoom")


# ============================================================
# PROMOTION HISTORY
# ============================================================
class StudentPromotionHistory(Base, TimestampMixin):
    __tablename__ = "student_promotion_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_session_id = Column(
        Integer,
        ForeignKey("academic_sessions.id"),
        nullable=False,
    )
    to_session_id = Column(Integer, ForeignKey("academic_sessions.id"), nullable=False)
    from_classroom_id = Column(Integer, ForeignKey("classroom.id"), nullable=False)
    to_classroom_id = Column(Integer, ForeignKey("classroom.id"), nullable=False)
    previous_roll_number = Column(Integer, nullable=False)
    new_roll_number = Column(Integer, nullable=False)
    promotion_date = Column(Date, nullable=False)
    promotion_type = Column(String(30), nullable=False, default="PROMOTED")
    remarks = Column(String(500))
    promoted_by_user_id = Column(Integer, ForeignKey("users.id"))

    student = relationship("User", foreign_keys=[student_id])
    from_session = relationship("AcademicSession", foreign_keys=[from_session_id])
    to_session = relationship("AcademicSession", foreign_keys=[to_session_id])
    from_classroom = relationship("ClassRoom", foreign_keys=[from_classroom_id])
    to_classroom = relationship("ClassRoom", foreign_keys=[to_classroom_id])
    promoted_by = relationship("User", foreign_keys=[promoted_by_user_id])

    __table_args__ = (
        Index("idx_student_promotion_student", "student_id"),
        Index("idx_student_promotion_date", "promotion_date"),
    )


# ============================================================
# TIMETABLE
# ============================================================
class WeekDay(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "week_days"
    id = Column(Integer, primary_key=True, autoincrement=True)
    day_code = Column(String(3), nullable=False, unique=True)
    day_name = Column(String(20), nullable=False, unique=True)
    display_order = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("idx_weekday_code", "day_code"),
        Index("idx_weekday_name", "day_name"),
        Index("idx_weekday_order", "display_order"),
        CheckConstraint(
            "display_order >= 1 AND display_order <= 7",
            name="ck_weekday_display_order",
        ),
    )


class TimeSlot(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "time_slots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_code = Column(String(10), unique=True, nullable=False)
    slot_name = Column(String(50), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    display_order = Column(Integer, nullable=False)
    is_break = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_slot_code", "slot_code"),
        Index("idx_slot_order", "display_order"),
        UniqueConstraint("start_time", "end_time", name="uq_slot_time"),
        CheckConstraint("duration_minutes > 0", name="ck_slot_duration"),
    )


class ClassTimeTable(Base, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "class_timetable"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timetable_id = Column(String(30), unique=True, nullable=False, index=True)
    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id"),
        nullable=False,
    )
    classroom_id = Column(Integer, ForeignKey("classroom.id"), nullable=False)
    class_subject_id = Column(Integer, ForeignKey("class_subjects.id"), nullable=False)
    teacher_subject_id = Column(
        Integer,
        ForeignKey("teacher_subjects.id"),
        nullable=False,
    )
    week_day_id = Column(Integer, ForeignKey("week_days.id"), nullable=False)
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"), nullable=False)
    room_number = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)

    academic_session = relationship("AcademicSession")
    classroom = relationship("ClassRoom")
    class_subject = relationship("ClassSubject")
    teacher_subject = relationship("TeacherSubject")
    week_day = relationship("WeekDay")
    time_slot = relationship("TimeSlot")

    __table_args__ = (
        UniqueConstraint(
            "academic_sessions_id",
            "classroom_id",
            "week_day_id",
            "time_slot_id",
            name="uq_class_slot",
        ),
        UniqueConstraint(
            "academic_sessions_id",
            "teacher_subject_id",
            "week_day_id",
            "time_slot_id",
            name="uq_teacher_slot",
        ),
        Index("idx_timetable_session", "academic_sessions_id"),
        Index("idx_timetable_class", "classroom_id"),
        Index("idx_timetable_teacher", "teacher_subject_id"),
        Index("idx_timetable_day", "week_day_id"),
        Index("idx_timetable_slot", "time_slot_id"),
    )


class TeacherAvailability(Base, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "teacher_availability"
    id = Column(Integer, primary_key=True, autoincrement=True)
    availability_id = Column(String(30), unique=True, nullable=False, index=True)
    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id"),
        nullable=False,
    )
    teacher_subject_id = Column(
        Integer,
        ForeignKey("teacher_subjects.id"),
        nullable=False,
    )
    week_day_id = Column(Integer, ForeignKey("week_days.id"), nullable=False)
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"), nullable=False)
    is_available = Column(Boolean, nullable=False, default=True)
    reason = Column(String(255), nullable=True)
    remarks = Column(Text, nullable=True)

    academic_session = relationship("AcademicSession")
    teacher_subject = relationship("TeacherSubject")
    week_day = relationship("WeekDay")
    time_slot = relationship("TimeSlot")

    __table_args__ = (
        UniqueConstraint(
            "academic_sessions_id",
            "teacher_subject_id",
            "week_day_id",
            "time_slot_id",
            name="uq_teacher_availability",
        ),
        Index("idx_teacher_availability_teacher", "teacher_subject_id"),
        Index("idx_teacher_availability_day", "week_day_id"),
        Index("idx_teacher_availability_slot", "time_slot_id"),
        Index("idx_teacher_availability_session", "academic_sessions_id"),
    )


# ============================================================
# DAILY CLASS & ATTENDANCE
# ============================================================
class DailyClass(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "daily_classes"
    id = Column(Integer, primary_key=True)
    daily_class_id = Column(String(30), unique=True, nullable=False, index=True)
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
    timetable_id = Column(Integer, ForeignKey("class_timetable.id"), nullable=True)
    class_date = Column(Date, nullable=False, index=True)
    topic = Column(String(300))
    description = Column(Text)
    homework = Column(Text)
    lecture_status = Column(String(20), default="Scheduled", nullable=False, index=True)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    total_minutes = Column(Integer)
    remarks = Column(Text)

    academic_session = relationship("AcademicSession")
    classroom = relationship("ClassRoom")
    class_subject = relationship("ClassSubject")
    teacher_subject = relationship("TeacherSubject")
    timetable = relationship("ClassTimeTable")

    __table_args__ = (
        UniqueConstraint(
            "teacher_subject_id",
            "class_date",
            "timetable_id",
            name="uq_daily_class",
        ),
        Index("idx_daily_classes_class_date", "classroom_id", "class_date"),
        Index("idx_daily_classes_teacher", "teacher_subject_id", "class_date"),
    )


class DailyClassStudent(Base, TimestampMixin):
    __tablename__ = "daily_class_students"
    id = Column(Integer, primary_key=True)
    daily_class_id = Column(Integer, ForeignKey("daily_classes.id"), nullable=False)
    student_class_id = Column(Integer, ForeignKey("student_classes.id"), nullable=False)
    attendance_status = Column(
        String(20),
        nullable=False,
        default="Present",
        index=True,
    )
    is_late = Column(Boolean, default=False)
    late_minutes = Column(Integer, default=0)
    remarks = Column(Text)
    marked_by = Column(Integer, ForeignKey("users.id"))
    marked_at = Column(DateTime, default=datetime.utcnow)

    daily_class = relationship("DailyClass")
    student_class = relationship("StudentClass")
    marker = relationship("User", foreign_keys=[marked_by])

    __table_args__ = (
        UniqueConstraint("daily_class_id", "student_class_id", name="uq_daily_student"),
        Index("idx_daily_student", "student_class_id", "attendance_status"),
    )


class StudentAttendance(Base, TimestampMixin):
    __tablename__ = "student_attendance"
    id = Column(Integer, primary_key=True)
    student_class_id = Column(
        Integer,
        ForeignKey("student_classes.id"),
        nullable=False,
        unique=True,
    )
    total_classes = Column(Integer, default=0)
    present_classes = Column(Integer, default=0)
    absent_classes = Column(Integer, default=0)
    attendance_percentage = Column(Float, default=0)

    student_class = relationship("StudentClass")

    __table_args__ = (Index("idx_student_attendance", "student_class_id"),)
