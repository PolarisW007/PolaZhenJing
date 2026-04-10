"""
=============================================================================
Module: tags.models
Description: Tag ORM model and the many-to-many association table between
             thoughts and tags.
             标签ORM模型和思绪与标签之间的多对多关联表。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: sqlalchemy, app.database
=============================================================================
"""

import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models import TimestampMixin
from app.database import Base

# ── Association Table (Thought <-> Tag) ──────────────────────────────────
thought_tags = Table(
    "thought_tags",
    Base.metadata,
    Column(
        "thought_id",
        UUID(as_uuid=True),
        ForeignKey("thoughts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ── Tag Model ────────────────────────────────────────────────────────────
class Tag(TimestampMixin, Base):
    """
    A label attached to one or more thoughts for categorisation.

    Business rules:
        - Tag name must be unique (case-insensitive enforced at app level).
        - slug is a URL-safe version of the name.
    """

    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # hex e.g. #3b82f6

    # M2M back-ref populated by Thought.tags
    thoughts: Mapped[list["Thought"]] = relationship(  # noqa: F821
        secondary=thought_tags, back_populates="tags", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"
