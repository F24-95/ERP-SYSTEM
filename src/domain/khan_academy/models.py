"""Khan Academy (KA) integration domain.

These tables (Topic, KaStudentActivity, KaSubjectActivity, KaSubjectProgress,
KaTopicProgress) exist only in this project — there is no equivalent in the
legacy FOLDER/ codebase (`mmmmmm`) at all. They were drafted directly against
this project's schema as new tables (under the repo's top-level `model/`
scratch folder) but never wired into `src/domain/` with schemas/crud/
service/router, so there was nothing importable or usable yet. This pass
relocates them into `src/domain/khan_academy/`, the same structure every
other domain in this project uses, and fixes the issues found while doing so
(see below) rather than porting business logic from a legacy source, since
none exists for these tables.

Fixes applied while relocating from the draft `model/topic.py` /
`model/ka_progress.py`:
  - Both files imported from `app.*` (the old sync codebase's package
    layout) instead of `src.*` -- updated throughout.
  - `KaStudentActivity.student_id` / `KaSubjectActivity.student_id` /
    `KaSubjectProgress.student_id` / `KaTopicProgress.student_id` were all
    typed `String(30)` with `ForeignKey("student_profiles.student_id")` --
    but this project's `StudentProfile` (src/domain/users/models.py) has no
    `student_id` string column at all (only `User.student_id` does, and
    that's a different table). That FK would have failed at table-creation
    time. Adapted to `Integer` FKs against `student_profiles.id`, matching
    the same adaptation already made for chat/id_cards/search in this
    migration.
  - Relationships back to `StudentProfile`/`Subject` are one-directional
    here (no `back_populates`) rather than requiring matching collection
    attributes on those already-established models, to keep this change
    additive and avoid touching more of the existing schema than necessary.
    `Subject.topics` and `ClassRoom.topics`/`.zoom_files` and
    `User.created_topics`/`.updated_topics` WERE added, since `Topic`
    explicitly declared those back_populates targets and adding them is a
    small, safe, additive change to those files.
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
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.core.id_generators import generate_topic_id
from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, TimestampMixin

# =============================================================================
# Topic  (Khan Academy curriculum topic, synced from the KA API)
# =============================================================================


class Topic(Base, TimestampMixin, ActiveMixin):
    """One row = one KA topic node (e.g. "Adding within 20").

    `subject_id` links the topic to the ERP Subject the KA course was
    mapped onto. `classroom_id` is an optional denormalised pointer to the
    classroom this topic is currently being taught in.

    Attachments for a topic use the generic polymorphic Attachment table
    (entity_type="topic", entity_id=Topic.id), the same pattern already
    used for assignments and study material, so no direct FK is declared
    here.
    """

    __tablename__ = "ka_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(
        String(30),
        unique=True,
        nullable=False,
        default=generate_topic_id,
        index=True,
    )

    # Raw KA topic id/slug as returned by the KA API
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
