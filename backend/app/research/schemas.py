"""
=============================================================================
Module: research.schemas
Description: Pydantic schemas for the Deep Research endpoints.
             深度研究端点的 Pydantic 模式。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: pydantic
=============================================================================
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────────────
class ResearchCreate(BaseModel):
    """Schema for creating a new research report."""
    query: str = Field(..., min_length=1, max_length=4000)
    title: str | None = Field(None, max_length=512)


class OptimizeQueryRequest(BaseModel):
    """Schema for optimizing a research query via AI. AI优化研究问题请求。"""
    query: str = Field(..., min_length=1, max_length=4000)
    title: str | None = Field(None, max_length=512)


class OptimizeQueryResponse(BaseModel):
    """Response containing the optimized query. AI优化后的研究问题响应。"""
    optimized_query: str
    optimized_title: str | None = None


# ── Response Schemas ─────────────────────────────────────────────────────
class ResearchResponse(BaseModel):
    """Full research response."""
    id: uuid.UUID
    title: str
    query: str
    outline: str | None = None
    content: str | None = None
    html_content: str | None = None
    summary: str | None = None
    status: str
    author_id: uuid.UUID
    source_urls: str | None = None
    metadata_json: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResearchListItem(BaseModel):
    """Lightweight research item for list views."""
    id: uuid.UUID
    title: str
    query: str
    summary: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResearchListResponse(BaseModel):
    """Paginated list of research reports."""
    items: list[ResearchListItem]
    total: int
    page: int
    page_size: int


# ── SSE Event Schema ────────────────────────────────────────────────────
class ResearchGenerateEvent(BaseModel):
    """Server-Sent Event payload for research generation progress."""
    step: str
    status: str  # "running" | "done" | "error"
    message: str
    progress: int = Field(ge=0, le=100)
    data: dict | None = None  # optional extra data per step
