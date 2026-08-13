"""Khan Academy (KA) integration domain (progress snapshots & activity logs).

Topic was moved to src/domain/curriculum/ (Subject & Topic live together
in a dedicated curriculum domain, same pattern as fees/exams). The Topic
class is imported from there for relationship resolution.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.database.connection import Base
from src.domain.common.mixins import TimestampMixin

# =============================================================================
# KaStudentActivity  (daily activity summary per student)
# =============================================================================


class KaStudentActivity(Base, TimestampMixin):
    __tablename__ = "ka_student_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_profile_id = Column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_date = Column(Date, nullable=False, index=True)
    to_date = Column(Date, nullable=False, index=True)

    worked_on = Column(Integer, nullable=True, default=0)
    attempted = Column(Integer, nullable=True, default=0)
    familiar = Column(Integer, nullable=True, default=0)
    proficient = Column(Integer, nullable=True, default=0)
    leveled_to_proficient = Column(Integer, nullable=True, default=0)
    leveled_up = Column(Integer, nullable=True, default=0)
    mastered = Column(Integer, nullable=True, default=0)

    minutes = Column(Integer, nullable=True, default=0)
    minutes_target_status = Column(String(50), nullable=True)

    student = relationship("StudentProfile")

    __table_args__ = (
        UniqueConstraint(
            "student_profile_id",
            "from_date",
            "to_date",
            name="uq_ka_student_activity",
        ),
        CheckConstraint("to_date >= from_date", name="ck_ka_activity_dates"),
        Index("idx_ka_activity_student_date", "student_profile_id", "from_date"),
        Index("idx_ka_activity_date_range", "from_date", "to_date"),
    )


# =============================================================================
# KaSubjectActivity  (per-topic activity log per student per date)
# =============================================================================


class KaSubjectActivity(Base, TimestampMixin):
    __tablename__ = "ka_subject_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_profile_id = Column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    topic_id = Column(
        Integer,
        ForeignKey("ka_topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Optional enrichment link -- set only when a teacher has attached ERP
    # material that covers this topic. Not a replacement for topic_id.
    study_material_id = Column(
        Integer,
        ForeignKey("study_materials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    activity_date = Column(Date, nullable=False, index=True)

    student = relationship("StudentProfile")
    subject = relationship("Subject")
    topic = relationship("Topic", back_populates="ka_subject_activities")
    study_material = relationship("StudyMaterial")

    __table_args__ = (
        Index(
            "idx_ka_subject_activity_student_date",
            "student_profile_id",
            "activity_date",
        ),
        Index("idx_ka_subject_activity_subject", "subject_id", "activity_date"),
        Index("idx_ka_subject_activity_topic", "topic_id", "activity_date"),
    )


# =============================================================================
# KaSubjectProgress  (cumulative points per subject/course snapshot)
# =============================================================================


class KaSubjectProgress(Base, TimestampMixin):
    __tablename__ = "ka_subject_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_profile_id = Column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    point_available = Column(Integer, nullable=True, default=0)
    point_earned = Column(Integer, nullable=True, default=0)
    percentage_earned = Column(Float, nullable=True, default=0.0)

    snapshot_date = Column(Date, nullable=False, index=True)

    student = relationship("StudentProfile")
    subject = relationship("Subject")

    __table_args__ = (
        UniqueConstraint(
            "student_profile_id",
            "subject_id",
            "snapshot_date",
            name="uq_ka_subject_progress",
        ),
        CheckConstraint(
            "point_earned >= 0 AND point_available >= 0",
            name="ck_ka_subject_progress_points",
        ),
        CheckConstraint(
            "percentage_earned >= 0 AND percentage_earned <= 100",
            name="ck_ka_subject_progress_pct",
        ),
        Index("idx_ka_subject_progress_student", "student_profile_id", "snapshot_date"),
        Index("idx_ka_subject_progress_subject", "subject_id", "snapshot_date"),
    )


# =============================================================================
# KaTopicProgress  (cumulative points per topic snapshot)
# =============================================================================


class KaTopicProgress(Base, TimestampMixin):
    __tablename__ = "ka_topic_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_profile_id = Column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    topic_id = Column(
        Integer,
        ForeignKey("ka_topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    study_material_id = Column(
        Integer,
        ForeignKey("study_materials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    point_available = Column(Integer, nullable=True, default=0)
    point_earned = Column(Integer, nullable=True, default=0)
    percentage_earned = Column(Float, nullable=True, default=0.0)

    snapshot_date = Column(Date, nullable=False, index=True)

    student = relationship("StudentProfile")
    subject = relationship("Subject")
    topic = relationship("Topic", back_populates="ka_topic_progress_entries")
    study_material = relationship("StudyMaterial")

    __table_args__ = (
        UniqueConstraint(
            "student_profile_id",
            "topic_id",
            "snapshot_date",
            name="uq_ka_topic_progress",
        ),
        CheckConstraint(
            "point_earned >= 0 AND point_available >= 0",
            name="ck_ka_topic_progress_points",
        ),
        CheckConstraint(
            "percentage_earned >= 0 AND percentage_earned <= 100",
            name="ck_ka_topic_progress_pct",
        ),
        Index("idx_ka_topic_progress_student", "student_profile_id", "snapshot_date"),
        Index("idx_ka_topic_progress_topic", "topic_id", "snapshot_date"),
    )
