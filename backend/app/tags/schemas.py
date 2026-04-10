"""
=============================================================================
Module: tags.schemas
Description: Pydantic schemas for Tag CRUD endpoints.
             标签 CRUD 端点的 Pydantic 模式。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: pydantic
=============================================================================
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────────────
class TagCreate(BaseModel):
    """Schema for creating a new tag."""
    name: str = Field(..., min_length=1, max_length=64)
    color: str | None = Field(None, pattern="^#[0-9a-fA-F]{6}$")


class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""
    name: str | None = Field(None, min_length=1, max_length=64)
    color: str | None = Field(None, pattern="^#[0-9a-fA-F]{6}$")


# ── Response Schemas ─────────────────────────────────────────────────────
class TagResponse(BaseModel):
    """Tag data returned by API."""
    id: uuid.UUID
    name: str
    slug: str
    color: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TagWithCountResponse(TagResponse):
    """Tag data with usage count."""
    thought_count: int = 0
