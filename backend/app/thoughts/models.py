"""
=============================================================================
Module: thoughts.models
Description: Thought ORM model – the core content entity of PolaZhenjing.
             思绪ORM模型 - PolaZhenjing的核心内容实体。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: sqlalchemy, app.database, app.tags.models
=============================================================================
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models import TimestampMixin
from app.database import Base
from app.tags.models import thought_tags


class ThoughtStatus(str, enum.Enum):
    """Publication status of a thought."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Thought(TimestampMixin, Base):
    """
    A single thought / reflection / article.

    Business rules:
        - Every thought belongs to one author (User).
        - status defaults to DRAFT.
        - slug is auto-generated from the title for URL-friendly links.
        - tags is a many-to-many relationship via thought_tags.
    """

    __tablename__ = "thoughts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[ThoughtStatus] = mapped_column(
        Enum(ThoughtStatus), default=ThoughtStatus.DRAFT, nullable=False
    )

    # Foreign key to User
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    author: Mapped["User"] = relationship(back_populates="thoughts", lazy="selectin")  # noqa: F821
    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        secondary=thought_tags, back_populates="thoughts", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Thought {self.title[:40]}>"
