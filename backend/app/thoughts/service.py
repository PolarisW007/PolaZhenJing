"""
=============================================================================
Module: thoughts.service
Description: Business logic for Thought CRUD – create, read, update, delete
             with pagination, search, and tag/category filtering.
             思绪 CRUD 业务逻辑 - 创建、读取、更新、删除，支持分页、搜索和标签/分类筛选。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: sqlalchemy, slugify
=============================================================================
"""

import uuid

from slugify import slugify
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sqlalchemy import insert as sa_insert

from app.common.exceptions import ConflictException, NotFoundException
from app.tags.models import Tag, thought_tags
from app.thoughts.models import Thought, ThoughtStatus


async def create_thought(
    db: AsyncSession,
    author_id: uuid.UUID,
    title: str,
    content: str = "",
    summary: str | None = None,
    category: str | None = None,
    status: str = "draft",
    tag_ids: list[uuid.UUID] | None = None,
) -> Thought:
    """
    Create a new thought.

    Business rules:
        - Slug is auto-generated from title; must be unique.
        - Tags are resolved from tag_ids and attached.
    """
    slug = slugify(title)
    # Ensure unique slug
    existing = await db.execute(select(Thought).where(Thought.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{uuid.uuid4().hex[:8]}"

    thought = Thought(
        title=title,
        slug=slug,
        content=content,
        summary=summary,
        category=category,
        status=ThoughtStatus(status),
        author_id=author_id,
    )
    db.add(thought)
    await db.flush()

    # Attach tags via the association table to avoid lazy-load issues
    if tag_ids:
        for tid in tag_ids:
            await db.execute(
                sa_insert(thought_tags).values(thought_id=thought.id, tag_id=tid)
            )

    # Re-fetch with eager loading so relationships are available for serialization
    result = await db.execute(
        select(Thought)
        .options(selectinload(Thought.tags))
        .where(Thought.id == thought.id)
    )
    return result.scalar_one()


async def get_thought_by_id(db: AsyncSession, thought_id: uuid.UUID) -> Thought:
    """Fetch a single thought by ID with tags eagerly loaded."""
    stmt = (
        select(Thought)
        .options(selectinload(Thought.tags))
        .where(Thought.id == thought_id)
    )
    result = await db.execute(stmt)
    thought = result.scalar_one_or_none()
    if thought is None:
        raise NotFoundException(detail="Thought not found")
    return thought


async def list_thoughts(
    db: AsyncSession,
    author_id: uuid.UUID | None = None,
    category: str | None = None,
    tag_slug: str | None = None,
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Thought], int]:
    """
    List thoughts with optional filters and pagination.

    Args:
        author_id: Filter by author.
        category: Filter by category name.
        tag_slug: Filter by tag slug.
        search: Full-text search on title and content.
        status: Filter by publication status.
        page: Page number (1-based).
        page_size: Items per page.

    Returns:
        Tuple of (thought_list, total_count).
    """
    stmt = select(Thought).options(selectinload(Thought.tags))

    if author_id:
        stmt = stmt.where(Thought.author_id == author_id)
    if category:
        stmt = stmt.where(Thought.category == category)
    if status:
        stmt = stmt.where(Thought.status == ThoughtStatus(status))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(Thought.title.ilike(pattern), Thought.content.ilike(pattern))
        )
    if tag_slug:
        stmt = stmt.join(Thought.tags).where(Tag.slug == tag_slug)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Apply pagination and ordering
    stmt = stmt.order_by(Thought.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    items = list(result.scalars().unique().all())

    return items, total


async def update_thought(
    db: AsyncSession,
    thought_id: uuid.UUID,
    **kwargs,
) -> Thought:
    """
    Update fields on an existing thought.

    Supported kwargs: title, content, summary, category, status, tag_ids.
    """
    thought = await get_thought_by_id(db, thought_id)

    if "title" in kwargs and kwargs["title"] is not None:
        thought.title = kwargs["title"]
        thought.slug = slugify(kwargs["title"])
    if "content" in kwargs and kwargs["content"] is not None:
        thought.content = kwargs["content"]
    if "summary" in kwargs and kwargs["summary"] is not None:
        thought.summary = kwargs["summary"]
    if "category" in kwargs:
        thought.category = kwargs["category"]
    if "status" in kwargs and kwargs["status"] is not None:
        thought.status = ThoughtStatus(kwargs["status"])
    if "tag_ids" in kwargs and kwargs["tag_ids"] is not None:
        # Clear existing tags and re-attach via association table
        await db.execute(
            thought_tags.delete().where(thought_tags.c.thought_id == thought_id)
        )
        for tid in kwargs["tag_ids"]:
            await db.execute(
                sa_insert(thought_tags).values(thought_id=thought_id, tag_id=tid)
            )

    await db.flush()
    # Re-fetch with eager loading
    result = await db.execute(
        select(Thought)
        .options(selectinload(Thought.tags))
        .where(Thought.id == thought_id)
    )
    return result.scalar_one()


async def delete_thought(db: AsyncSession, thought_id: uuid.UUID) -> None:
    """Delete a thought by ID."""
    thought = await get_thought_by_id(db, thought_id)
    await db.delete(thought)
    await db.flush()
