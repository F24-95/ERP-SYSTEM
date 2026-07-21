from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from src.core.enums import MaterialType
from src.core.id_generators import generate_material_id
from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, TimestampMixin


class StudyMaterial(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "study_materials"

    id = Column(Integer, primary_key=True)
    material_id = Column(
        String(30),
        unique=True,
        nullable=False,
        default=generate_material_id,
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
    material_type = Column(SAEnum(MaterialType), nullable=False)

    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    download_count = Column(Integer, default=0)

    # NOTE: legacy StudyMaterial has no `updated_by`/`deleted_by` columns
    # (unlike Assignment/Exam) — do not add them, the legacy service itself
    # only ever guards a `hasattr(material, "deleted_by")` check that always
    # evaluates False. Preserved as-is.
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    academic_sessions = relationship("AcademicSession")
    classroom = relationship("ClassRoom")
    class_subject = relationship("ClassSubject")
    teacher_subject = relationship("TeacherSubject")
    uploader = relationship("User")

    __table_args__ = (
        Index("idx_material_class", "classroom_id", "class_subject_id"),
        Index("idx_material_teacher", "teacher_subject_id"),
        UniqueConstraint("class_subject_id", "title", name="uq_material_title"),
    )
