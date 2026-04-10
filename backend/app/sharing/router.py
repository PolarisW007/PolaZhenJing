"""
=============================================================================
Module: sharing.router
Description: API endpoint for generating social share links for a thought.
             生成思绪社交分享链接的API端点。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi, app.sharing.service
=============================================================================
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.common.models import User
from app.database import get_db
from app.sharing.service import generate_share_data
from app.thoughts.service import get_thought_by_id

router = APIRouter(prefix="/api/share", tags=["Sharing"])


@router.get("/{thought_id}")
async def share_thought(
    thought_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """
    Generate share URLs and Open Graph metadata for the given thought.

    Returns platform-specific share links (X, Weibo, Xiaohongshu),
    Open Graph tags, and a pre-formatted share text for clipboard.
    """
    thought = await get_thought_by_id(db, thought_id)
    tag_names = [t.name for t in thought.tags]

    return generate_share_data(
        title=thought.title,
        slug=thought.slug,
        summary=thought.summary,
        tags=tag_names,
    )
