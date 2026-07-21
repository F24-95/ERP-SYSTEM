import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_mixin, declared_attr


@declarative_mixin
class UUIDMixin:
    """Provides a public UUID for safe external referencing."""

    @declared_attr
    def public_id(cls):
        # We use a string representation of UUID for wider compatibility, or native UUID if preferred.
        # String(36) is standard for UUID.
        return Column(
            String(36),
            default=lambda: str(uuid.uuid4()),
            unique=True,
            index=True,
            nullable=False,
        )


@declarative_mixin
class TimestampMixin:
    """Provides standard created_at and updated_at timestamps."""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        )


@declarative_mixin
class ActiveMixin:
    """Provides an is_active toggle."""

    @declared_attr
    def is_active(cls):
        return Column(Boolean, default=True, nullable=False)


@declarative_mixin
class SoftDeleteMixin:
    """Provides soft deletion capabilities."""

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False)

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime, nullable=True)

    @declared_attr
    def deleted_by(cls):
        # Integer assuming internal IDs are used for relations
        return Column(Integer, nullable=True)


@declarative_mixin
class AuditMixin:
    """Provides user attribution for creation and updates."""

    @declared_attr
    def created_by(cls):
        return Column(Integer, nullable=True)

    @declared_attr
    def updated_by(cls):
        return Column(Integer, nullable=True)
