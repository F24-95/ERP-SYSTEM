from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, AuditMixin, TimestampMixin


class StudentIDCard(Base, TimestampMixin, ActiveMixin, AuditMixin):
    """Stores the generated artifacts for a student's ID card (front side only).

    NOTE on the student FK: legacy `StudentIDCard.student_id` is a String(30)
    FK to `student_profiles.student_id` (a business-ID string column that
    doesn't exist on this project's `StudentProfile` — see Phase 2f notes on
    similar adaptations for TeacherSubject/StudentClass). The equivalent
    here is `student_profile_id -> student_profiles.id`. The legacy
    business-ID string is preserved separately as `student_id_business`,
    exactly as legacy already did for the *content* of the card (it snapshots
    the same value legacy did, just sourced from `registration_number`/
    `admission_number` instead of a `student_id` column).
    """

    __tablename__ = "student_id_cards"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    student_profile_id = Column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Snapshot of student/session details for PDF rendering
    student_name = Column(String(120), nullable=False)
    parent_name = Column(String(120), nullable=True)
    class_display_name = Column(String(150), nullable=True)

    institute_name = Column(String(255), nullable=False)
    institute_contact_number = Column(String(30), nullable=False)
    academic_session_label = Column(String(120), nullable=True)

    date_of_joining = Column(Date, nullable=True)
    valid_till = Column(Date, nullable=True)

    # File paths under /uploads
    institute_logo_path = Column(String(500), nullable=True)
    student_photo_path = Column(String(500), nullable=True)

    qr_code_path = Column(String(500), nullable=True)
    pdf_path = Column(String(500), nullable=True)

    # Business identifier snapshot (registration_number, falling back to
    # admission_number -- see StudentIDCardService._business_id_for).
    student_id_business = Column(String(30), nullable=False)

    student_profile = relationship("StudentProfile")

    __table_args__ = (
        UniqueConstraint(
            "student_profile_id",
            "academic_sessions_id",
            name="uq_student_idcard_student_session",
        ),
        Index("idx_student_id_cards_student", "student_profile_id"),
        Index("idx_student_id_cards_session", "academic_sessions_id"),
    )
