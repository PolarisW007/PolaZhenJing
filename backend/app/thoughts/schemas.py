"""
=============================================================================
Module: thoughts.schemas
Description: Pydantic schemas for Thought CRUD endpoints.
             思绪 CRUD 端点的 Pydantic 模式。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: pydantic
=============================================================================
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.tags.schemas import TagResponse


# ── Request Schemas ──────────────────────────────────────────────────────
class ThoughtCreate(BaseModel):
    """Schema for creating a new thought."""
    title: str = Field(..., min_length=1, max_length=256)
    content: str = Field(default="")
    summary: str | None = None
    category: str | None = Field(None, max_length=64)
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


class ThoughtUpdate(BaseModel):
    """Schema for updating an existing thought (all fields optional)."""
    title: str | None = Field(None, min_length=1, max_length=256)
    content: str | None = None
    summary: str | None = None
    category: str | None = None
    status: str | None = Field(None, pattern="^(draft|published|archived)$")
    tag_ids: list[uuid.UUID] | None = None


# ── Response Schemas ─────────────────────────────────────────────────────
class ThoughtResponse(BaseModel):
    """Full thought response with tags and author info."""
    id: uuid.UUID
    title: str
    slug: str
    content: str
    summary: str | None
    category: str | None
    status: str
    author_id: uuid.UUID
    tags: list[TagResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ThoughtListResponse(BaseModel):
    """Paginated list of thoughts."""
    items: list[ThoughtResponse]
    total: int
    page: int
    page_size: int
