"""
=============================================================================
Module: tags.router
Description: REST API endpoints for tag management.
             标签管理的 REST API 端点。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi, app.tags.service
=============================================================================
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.common.models import User
from app.database import get_db
from app.tags.schemas import TagCreate, TagResponse, TagUpdate, TagWithCountResponse
from app.tags.service import (
    create_tag,
    delete_tag,
    get_tag_by_id,
    list_tags_with_count,
    update_tag,
)

router = APIRouter(prefix="/api/tags", tags=["Tags"])


@router.get("", response_model=list[TagWithCountResponse])
async def get_tags(db: AsyncSession = Depends(get_db)):
    """List all tags with their usage count."""
    return await list_tags_with_count(db)


@router.post("", response_model=TagResponse, status_code=201)
async def create_new_tag(
    body: TagCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Create a new tag (requires authentication)."""
    return await create_tag(db, name=body.name, color=body.color)


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Fetch a single tag by ID."""
    return await get_tag_by_id(db, tag_id)


@router.patch("/{tag_id}", response_model=TagResponse)
async def patch_tag(
    tag_id: uuid.UUID,
    body: TagUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Update a tag's name or color."""
    return await update_tag(db, tag_id, name=body.name, color=body.color)


@router.delete("/{tag_id}", status_code=204)
async def remove_tag(
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Delete a tag."""
    await delete_tag(db, tag_id)
