"""
=============================================================================
Module: publish.router
Description: API endpoints for publishing thoughts to the MkDocs static site
             and triggering site builds.
             发布思绪到MkDocs静态站点和触发站点构建的API端点。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi, app.publish.service
=============================================================================
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.common.models import User
from app.database import get_db
from app.publish.service import build_mkdocs, publish_thought

router = APIRouter(prefix="/api/publish", tags=["Publishing"])


class PublishResponse(BaseModel):
    message: str
    file_path: str | None = None


class BuildResponse(BaseModel):
    success: bool
    message: str


@router.post("/{thought_id}", response_model=PublishResponse)
async def publish_single(
    thought_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """
    Publish a thought as a Markdown file in the MkDocs docs/ directory.

    The thought must be in PUBLISHED status.
    """
    path = await publish_thought(db, thought_id)
    return PublishResponse(
        message="Thought published successfully",
        file_path=str(path),
    )


@router.post("/build", response_model=BuildResponse)
async def trigger_build(
    _user: User = Depends(get_current_user),
):
    """Trigger a full MkDocs site build."""
    ok = await build_mkdocs()
    return BuildResponse(
        success=ok,
        message="Build succeeded" if ok else "Build failed – check server logs",
    )
