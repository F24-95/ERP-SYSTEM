"""Student report generation domain.

Like khan_academy and zoom, none of these tables exist in the legacy
`mmmmmm` codebase -- drafted fresh against this project's schema in the
top-level `model/student_report.py` scratch file, relocated here with the
same `student_profiles.student_id` -> `student_profiles.id` FK fix applied
in khan_academy/models.py (same root cause: the draft assumed a
`StudentProfile.student_id` string column that doesn't exist on this
project's actual `StudentProfile`).
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.database.connection import Base
from src.domain.common.mixins import TimestampMixin

# =============================================================================
# StudentReport  (master record for a generated progress report)
# =============================================================================


class StudentReport(Base, TimestampMixin):
    """One row = one report generated for one student covering a date
    window (data_start_date -> data_end_date). Document columns are
    nullable since a report may be generated incrementally (HTML first,
    PDF later).
    """

    __tablename__ = "student_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_profile_id = Column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    report_date = Column(Date, nullable=False, index=True)
    data_start_date = Column(Date, nullable=False)
    data_end_date = Column(Date, nullable=False)

    pdf_document = Column(LargeBinary, nullable=True)
    html_document = Column(LargeBinary, nullable=True)
    png_document = Column(LargeBinary, nullable=True)

    student = relationship("StudentProfile")

    activity_report = relationship(
        "StudentActivityReport",
        back_populates="student_report",
        uselist=False,
        cascade="all, delete-orphan",
    )
    zoom_duration_report = relationship(
        "ZoomDurationReport",
        back_populates="student_report",
        uselist=False,
        cascade="all, delete-orphan",
    )
    zoom_interaction_report = relationship(
        "ZoomInteractionReport",
        back_populates="student_report",
        uselist=False,
        cascade="all, delete-orphan",
    )
    subject_progress_items = relationship(
        "StudentSubjectProgressReport",
        back_populates="student_report",
        cascade="all, delete-orphan",
    )
    topic_progress_items = relationship(
        "StudentTopicProgressReport",
        back_populates="student_report",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "student_profile_id",
            "data_start_date",
            "data_end_date",
            name="uq_student_report_period",
        ),
        CheckConstraint(
            "data_end_date >= data_start_date",
            name="ck_student_report_dates",
        ),
        Index("idx_student_report_student", "student_profile_id"),
        Index("idx_student_report_report_date", "report_date"),
    )


class StudentActivityReport(Base, TimestampMixin):
    """Aggregated KA activity metrics for a StudentReport period (1-to-1)."""

    __tablename__ = "student_activity_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(
        Integer,
        ForeignKey("student_reports.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    mean_duration_minutes = Column(Integer, nullable=True)
    total_duration_minutes = Column(Integer, nullable=True)
    total_worked_hours = Column(Integer, nullable=True)

    total_attempted = Column(Integer, nullable=True)
    total_familiar = Column(Integer, nullable=True)
    total_proficient = Column(Integer, nullable=True)
    total_leveled_up = Column(Integer, nullable=True)
    total_mastered = Column(Integer, nullable=True)

    student_report = relationship("StudentReport", back_populates="activity_report")

    __table_args__ = (Index("idx_student_activity_report_report", "report_id"),)


class StudentSubjectProgressReport(Base, TimestampMixin):
    """Links a StudentReport to the KaSubjectProgress snapshot used in it (1-to-many)."""

    __tablename__ = "student_subject_progress_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(
        Integer,
        ForeignKey("student_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subject_progress_id = Column(
        Integer,
        ForeignKey("ka_subject_progress.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    student_report = relationship(
        "StudentReport",
        back_populates="subject_progress_items",
    )
    subject = relationship("Subject")
    subject_progress = relationship("KaSubjectProgress")

    __table_args__ = (
        UniqueConstraint(
            "report_id",
            "subject_id",
            name="uq_student_subject_progress_report",
        ),
        Index("idx_student_subject_progress_report_report", "report_id"),
        Index("idx_student_subject_progress_report_subject", "subject_id"),
    )


class StudentTopicProgressReport(Base, TimestampMixin):
    """Links a StudentReport to the KaTopicProgress snapshot used in it (1-to-many)."""

    __tablename__ = "student_topic_progress_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(
        Integer,
        ForeignKey("student_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_id = Column(
        Integer,
        ForeignKey("ka_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    study_material_id = Column(
        Integer,
        ForeignKey("study_materials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    topic_progress_id = Column(
        Integer,
        ForeignKey("ka_topic_progress.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    student_report = relationship(
        "StudentReport",
        back_populates="topic_progress_items",
    )
    topic = relationship("Topic", back_populates="report_links")
    study_material = relationship("StudyMaterial")
    topic_progress = relationship("KaTopicProgress")

    __table_args__ = (
        UniqueConstraint(
            "report_id",
            "topic_id",
            name="uq_student_topic_progress_report",
        ),
        Index("idx_student_topic_progress_report_report", "report_id"),
        Index("idx_student_topic_progress_report_topic", "topic_id"),
    )


class ZoomDurationReport(Base, TimestampMixin):
    """Zoom session duration statistics for a StudentReport period (1-to-1)."""

    __tablename__ = "zoom_duration_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(
        Integer,
        ForeignKey("student_reports.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    mean_duration_minutes = Column(Integer, nullable=True)
    min_duration_minutes = Column(Integer, nullable=True)
    max_duration_minutes = Column(Integer, nullable=True)

    student_report = relationship(
        "StudentReport",
        back_populates="zoom_duration_report",
    )

    __table_args__ = (Index("idx_zoom_duration_report_report", "report_id"),)


class ZoomInteractionReport(Base, TimestampMixin):
    """Zoom student interaction statistics for a StudentReport period (1-to-1)."""

    __tablename__ = "zoom_interaction_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(
        Integer,
        ForeignKey("student_reports.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    mean_interaction_count = Column(Integer, nullable=True)
    min_interaction_count = Column(Integer, nullable=True)
    max_interaction_count = Column(Integer, nullable=True)

    student_report = relationship(
        "StudentReport",
        back_populates="zoom_interaction_report",
    )

    __table_args__ = (Index("idx_zoom_interaction_report_report", "report_id"),)
