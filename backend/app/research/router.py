"""
=============================================================================
Module: research.router
Description: REST API endpoints for deep research report management,
             including SSE streaming for generation progress.
             深度研究报告管理的REST API端点，含SSE流式生成进度。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi, app.research.service
=============================================================================
"""

import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.common.models import User
from app.database import get_db
from app.research.schemas import (
    OptimizeQueryRequest,
    OptimizeQueryResponse,
    ResearchCreate,
    ResearchListResponse,
    ResearchListItem,
    ResearchResponse,
)
from app.research.service import (
    create_research,
    delete_research,
    generate_research,
    get_research_by_id,
    list_researches,
    optimize_query,
)

router = APIRouter(prefix="/api/research", tags=["Research"])


@router.post("/optimize-query", response_model=OptimizeQueryResponse)
async def optimize_research_query(
    body: OptimizeQueryRequest,
    _user: User = Depends(get_current_user),
):
    """Use AI to optimize and enhance a research question. AI优化研究问题。"""
    try:
        result = await optimize_query(query=body.query, title=body.title)
        return OptimizeQueryResponse(
            optimized_query=result["optimized_query"],
            optimized_title=result.get("optimized_title"),
        )
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={"detail": str(e) or "AI服务不可用，请检查配置"},
        )


@router.post("", response_model=ResearchResponse, status_code=201)
async def create_new_research(
    body: ResearchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new research report. Returns 409 if duplicate active query exists."""
    from fastapi import HTTPException
    try:
        research = await create_research(
            db,
            author_id=current_user.id,
            query=body.query,
            title=body.title,
        )
        return research
    except HTTPException as exc:
        if exc.status_code == 409:
            existing_id = exc.headers.get("X-Existing-Id") if exc.headers else None
            return JSONResponse(
                status_code=409,
                content={
                    "detail": exc.detail,
                    "existing_id": existing_id,
                },
            )
        raise


@router.get("", response_model=ResearchListResponse)
async def get_researches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List research reports for the current user."""
    items, total = await list_researches(
        db, author_id=current_user.id, page=page, page_size=page_size
    )
    return ResearchListResponse(
        items=[ResearchListItem.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{research_id}", response_model=ResearchResponse)
async def get_single_research(
    research_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Fetch a single research report by ID."""
    return await get_research_by_id(db, research_id)


@router.get("/{research_id}/generate")
async def generate_stream(
    research_id: uuid.UUID,
    _user: User = Depends(get_current_user),
):
    """
    SSE endpoint that streams generation progress events.

    NOTE: We do NOT use Depends(get_db) here because FastAPI runs
    dependency cleanup when the handler returns, which closes the DB
    session before StreamingResponse starts iterating the generator.
    Instead, we create a dedicated session inside the generator.
    SSE端点 - 需要在生成器内部管理数据库会话，避免会话提前关闭。
    """
    from app.database import async_session_factory

    async def event_generator():
        async with async_session_factory() as db:
            try:
                async for event in generate_research(db, research_id):
                    yield f"data: {event.model_dump_json()}\n\n"
                await db.commit()
                # Final signal
                yield "data: {\"step\":\"stream_end\",\"status\":\"done\",\"message\":\"Stream ended\",\"progress\":100}\n\n"
            except Exception as e:
                await db.rollback()
                error_msg = str(e).replace('"', '\\"')
                yield f'data: {{"step":"error","status":"error","message":"{error_msg}","progress":0}}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{research_id}/html", response_class=HTMLResponse)
async def get_research_html(
    research_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Serve the rendered HTML report."""
    research = await get_research_by_id(db, research_id)
    if not research.html_content:
        return HTMLResponse(
            content="<h1>Report not yet generated</h1>",
            status_code=404,
        )
    return HTMLResponse(content=research.html_content)


@router.delete("/{research_id}", status_code=204)
async def remove_research(
    research_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Delete a research report."""
    await delete_research(db, research_id)
