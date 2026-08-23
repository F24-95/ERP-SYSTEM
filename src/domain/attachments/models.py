"""model/attachments/models.py - Generic Attachment Table

A generic, polymorphic attachment store that lets any entity (assignments,
study material, exams, chat messages, etc.) attach one or more files
without needing a dedicated table.

entity_type + entity_id identify the owning row, e.g.
    entity_type="assignment", entity_id=42

Ported verbatim (same columns, same semantics) from the legacy
`app/model/attachment.py`.
"""

from sqlalchemy import Column, Index, Integer, LargeBinary, String
from sqlalchemy.orm import deferred

from src.database.connection import Base
from src.domain.common.mixins import ActiveMixin, AuditMixin, TimestampMixin


class Attachment(Base, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    attachment_code = Column(String(30), unique=True, nullable=False, index=True)

    entity_type = Column(String(30), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)

    file_data = deferred(Column(LargeBinary, nullable=False))

    __table_args__ = (Index("idx_attachment_entity", "entity_type", "entity_id"),)
