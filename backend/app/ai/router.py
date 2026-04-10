"""
=============================================================================
Module: ai.router
Description: API endpoints for AI-assisted content operations:
             polish, summarise, suggest tags, expand thought.
             AI辅助内容操作的API端点 - 润色、摘要、标签建议、扩展思绪。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi, app.ai.factory
=============================================================================
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.ai.base_provider import BaseAIProvider
from app.ai.factory import get_ai_provider
from app.auth.dependencies import get_current_user
from app.common.models import User

logger = logging.getLogger("polazj.ai")
router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])


# ── Request / Response Schemas ───────────────────────────────────────────
class PolishRequest(BaseModel):
    text: str = Field(..., min_length=1)
    style: str = Field(default="professional")

class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    max_length: int = Field(default=200, ge=50, le=1000)

class SuggestTagsRequest(BaseModel):
    text: str = Field(..., min_length=1)
    max_tags: int = Field(default=5, ge=1, le=10)

class ExpandRequest(BaseModel):
    text: str = Field(..., min_length=1)
    direction: str = Field(default="elaborate")

class TextResponse(BaseModel):
    result: str

class TagsResponse(BaseModel):
    tags: list[str]


# ── Endpoints ────────────────────────────────────────────────────────────
@router.post("/polish", response_model=TextResponse)
async def polish_text(
    body: PolishRequest,
    _user: User = Depends(get_current_user),
    provider: BaseAIProvider = Depends(get_ai_provider),
):
    """Polish / rewrite text using AI for better clarity and style."""
    try:
        result = await provider.polish_text(body.text, style=body.style)
        return TextResponse(result=result)
    except Exception as e:
        logger.error("AI polish failed: %s", e)
        raise HTTPException(status_code=502, detail="AI service unavailable")


@router.post("/summarize", response_model=TextResponse)
async def summarize_text(
    body: SummarizeRequest,
    _user: User = Depends(get_current_user),
    provider: BaseAIProvider = Depends(get_ai_provider),
):
    """Generate a concise summary of the given text."""
    try:
        result = await provider.generate_summary(body.text, max_length=body.max_length)
        return TextResponse(result=result)
    except Exception as e:
        logger.error("AI summarize failed: %s", e)
        raise HTTPException(status_code=502, detail="AI service unavailable")


@router.post("/suggest-tags", response_model=TagsResponse)
async def suggest_tags(
    body: SuggestTagsRequest,
    _user: User = Depends(get_current_user),
    provider: BaseAIProvider = Depends(get_ai_provider),
):
    """Suggest relevant tags for the given text."""
    try:
        tags = await provider.suggest_tags(body.text, max_tags=body.max_tags)
        return TagsResponse(tags=tags)
    except Exception as e:
        logger.error("AI suggest-tags failed: %s", e)
        raise HTTPException(status_code=502, detail="AI service unavailable")


@router.post("/expand", response_model=TextResponse)
async def expand_thought(
    body: ExpandRequest,
    _user: User = Depends(get_current_user),
    provider: BaseAIProvider = Depends(get_ai_provider),
):
    """Expand a brief thought into a fuller piece of writing."""
    try:
        result = await provider.expand_thought(body.text, direction=body.direction)
        return TextResponse(result=result)
    except Exception as e:
        logger.error("AI expand failed: %s", e)
        raise HTTPException(status_code=502, detail="AI service unavailable")
