from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, TimestampMixin


class Fee(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "fees"

    id = Column(Integer, primary_key=True)
    fee_id = Column(String(30), unique=True, index=True, nullable=False)
    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id"),
        index=True,
        nullable=False,
    )
    student_class_id = Column(
        Integer,
        ForeignKey("student_classes.id"),
        index=True,
        nullable=False,
    )
    fee_month = Column(Integer, nullable=False)
    fee_year = Column(Integer, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    fine_amount = Column(Numeric(10, 2), default=0)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)
    status = Column(String(20), default="PENDING", index=True)
    remarks = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    academic_session = relationship("AcademicSession")
    student_class = relationship("StudentClass")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])

    __table_args__ = (
        UniqueConstraint(
            "student_class_id",
            "fee_month",
            "fee_year",
            name="uq_student_fee",
        ),
        CheckConstraint("fee_month>=1 AND fee_month<=12", name="ck_fee_month"),
        CheckConstraint("paid_amount>=0", name="ck_paid_amount"),
        CheckConstraint("discount_amount>=0", name="ck_discount_amount"),
        CheckConstraint("fine_amount>=0", name="ck_fine_amount"),
        Index("idx_fee_student", "student_class_id", "status"),
        Index("idx_fee_due", "due_date", "status"),
    )
