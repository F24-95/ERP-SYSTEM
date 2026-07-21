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
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from src.core.enums import Gender, UserRole
from src.database.connection import Base
from src.domain.common.mixins import (
    ActiveMixin,
    AuditMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDMixin,
)


class User(Base, UUIDMixin, TimestampMixin, ActiveMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Business IDs (Internal identifiers for legacy/school systems)
    admin_id = Column(String(50), unique=True, nullable=True, index=True)
    teacher_id = Column(String(50), unique=True, nullable=True, index=True)
    student_id = Column(String(50), unique=True, nullable=True, index=True)

    # Login credentials
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, index=True)
    # Was missing entirely -- core/email.py already has send_otp_email /
    # send_verification_email fully implemented, and core/security.py
    # already has generate_otp(), but there was no column anywhere to
    # record whether a user had actually completed verification, so that
    # infrastructure was dead code with nothing to write its result to.
    is_verified = Column(Boolean, default=False, nullable=False)

    # Session / Device info
    last_seen = Column(DateTime, nullable=True)
    device_token = Column(String(255), nullable=True)

    # Security metrics
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    failed_login_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("idx_user_role_active", "role", "is_active"),
        Index("idx_user_email_active", "email", "is_active"),
    )

    # Relationships
    student_profile = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    teacher_profile = relationship(
        "TeacherProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    admin_profile = relationship(
        "AdminProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    created_topics = relationship(
        "Topic",
        foreign_keys="Topic.created_by",
        back_populates="creator",
    )
    updated_topics = relationship(
        "Topic",
        foreign_keys="Topic.updated_by",
        back_populates="updater",
    )


class StudentProfile(Base, UUIDMixin, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Core Details
    admission_number = Column(String(30), unique=True, nullable=True, index=True)

    # Search-friendly business identifier, distinct from admission_number.
    # Auto-generated at profile-creation time (see RegistrationNumberService).
    # Nullable only to allow a one-time backfill window on existing data;
    # new rows always get one. Ported back — was missing from this model
    # during the async migration (legacy column: student_profiles.registration_number).
    registration_number = Column(String(30), unique=True, nullable=True, index=True)

    student_name = Column(String(255), nullable=False)
    gender = Column(SAEnum(Gender), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    blood_group = Column(String(10), nullable=True)

    # Contact
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)

    # Parent/Guardian
    parent_name = Column(String(255), nullable=True)
    parent_phone = Column(String(20), nullable=True)

    # External Integrations (e.g. Khan Academy, NS)
    ka_student_id = Column(String(100), nullable=True, unique=True, index=True)

    user = relationship("User", back_populates="student_profile")


class TeacherProfile(Base, UUIDMixin, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "teacher_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    teacher_name = Column(String(255), nullable=False)
    gender = Column(SAEnum(Gender), nullable=True)
    employee_code = Column(String(30), unique=True, nullable=True, index=True)
    designation = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    experience_years = Column(Float, default=0, nullable=True)

    user = relationship("User", back_populates="teacher_profile")


class AdminProfile(Base, UUIDMixin, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "admin_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    admin_name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    # Was referenced by src/api/dependencies.py::require_super_admin, which
    # raised NotImplementedError because there was nowhere to read this
    # from. Column added so that dependency can actually be implemented
    # instead of being permanently broken dead code.
    is_super_admin = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="admin_profile")
