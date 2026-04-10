"""
=============================================================================
Module: common.models
Description: Shared ORM models used across multiple modules.
             - TimestampMixin: adds created_at / updated_at to any model
             - User: application user (auth target)
             跨模块共享ORM模型 - TimestampMixin: 时间戳混入；User: 应用用户模型。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: sqlalchemy, app.database
=============================================================================
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ── Mixin ────────────────────────────────────────────────────────────────
class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── User Model ───────────────────────────────────────────────────────────
class User(TimestampMixin, Base):
    """
    Application user.

    Business rules:
        - Email must be unique.
        - Username must be unique.
        - is_active defaults to True; set to False to soft-delete.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships (back-populated by Thought model)
    thoughts: Mapped[list["Thought"]] = relationship(  # noqa: F821
        back_populates="author", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
