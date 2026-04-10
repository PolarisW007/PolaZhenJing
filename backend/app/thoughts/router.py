"""
=============================================================================
Module: thoughts.router
Description: REST API endpoints for thought management (CRUD).
             思绪管理的 REST API 端点（CRUD）。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi, app.thoughts.service
=============================================================================
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.common.models import User
from app.database import get_db
from app.thoughts.schemas import (
    ThoughtCreate,
    ThoughtListResponse,
    ThoughtResponse,
    ThoughtUpdate,
)
from app.thoughts.service import (
    create_thought,
    delete_thought,
    get_thought_by_id,
    list_thoughts,
    update_thought,
)

router = APIRouter(prefix="/api/thoughts", tags=["Thoughts"])


@router.get("", response_model=ThoughtListResponse)
async def get_thoughts(
    category: str | None = Query(None),
    tag: str | None = Query(None, description="Filter by tag slug"),
    search: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List thoughts for the current user with optional filters.

    Supports filtering by category, tag, status, and full-text search.
    """
    items, total = await list_thoughts(
        db,
        author_id=current_user.id,
        category=category,
        tag_slug=tag,
        search=search,
        status=status,
        page=page,
        page_size=page_size,
    )
    return ThoughtListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ThoughtResponse, status_code=201)
async def create_new_thought(
    body: ThoughtCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new thought."""
    return await create_thought(
        db,
        author_id=current_user.id,
        title=body.title,
        content=body.content,
        summary=body.summary,
        category=body.category,
        status=body.status,
        tag_ids=body.tag_ids,
    )


@router.get("/{thought_id}", response_model=ThoughtResponse)
async def get_single_thought(
    thought_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Fetch a single thought by ID."""
    return await get_thought_by_id(db, thought_id)


@router.patch("/{thought_id}", response_model=ThoughtResponse)
async def patch_thought(
    thought_id: uuid.UUID,
    body: ThoughtUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Update a thought's fields."""
    return await update_thought(
        db, thought_id, **body.model_dump(exclude_unset=True)
    )


@router.delete("/{thought_id}", status_code=204)
async def remove_thought(
    thought_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Delete a thought."""
    await delete_thought(db, thought_id)
