"""
=============================================================================
Module: tags.service
Description: Business logic for tag CRUD operations and usage counting.
             标签 CRUD 操作和使用计数的业务逻辑。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: sqlalchemy, slugify
=============================================================================
"""

import uuid

from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ConflictException, NotFoundException
from app.tags.models import Tag, thought_tags


async def create_tag(db: AsyncSession, name: str, color: str | None = None) -> Tag:
    """
    Create a new tag.

    Business rules:
        - Name is unique; slug is auto-generated.

    Raises:
        ConflictException: If tag name already exists.
    """
    slug = slugify(name)
    existing = await db.execute(select(Tag).where(Tag.slug == slug))
    if existing.scalar_one_or_none():
        raise ConflictException(detail=f"Tag '{name}' already exists")

    tag = Tag(name=name, slug=slug, color=color)
    db.add(tag)
    await db.flush()
    return tag


async def get_tag_by_id(db: AsyncSession, tag_id: uuid.UUID) -> Tag:
    """Fetch a tag by primary key or raise 404."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if tag is None:
        raise NotFoundException(detail="Tag not found")
    return tag


async def list_tags(db: AsyncSession) -> list[Tag]:
    """Return all tags ordered by name."""
    result = await db.execute(select(Tag).order_by(Tag.name))
    return list(result.scalars().all())


async def list_tags_with_count(db: AsyncSession) -> list[dict]:
    """
    Return all tags with a count of how many thoughts use each.

    Performance note: uses a LEFT JOIN + GROUP BY; O(tags * thought_tags).
    """
    stmt = (
        select(Tag, func.count(thought_tags.c.thought_id).label("thought_count"))
        .outerjoin(thought_tags, Tag.id == thought_tags.c.tag_id)
        .group_by(Tag.id)
        .order_by(Tag.name)
    )
    rows = await db.execute(stmt)
    results = []
    for tag, count in rows.all():
        results.append({
            "id": tag.id,
            "name": tag.name,
            "slug": tag.slug,
            "color": tag.color,
            "created_at": tag.created_at,
            "thought_count": count,
        })
    return results


async def update_tag(
    db: AsyncSession, tag_id: uuid.UUID, name: str | None = None, color: str | None = None
) -> Tag:
    """Update a tag's name and/or color."""
    tag = await get_tag_by_id(db, tag_id)
    if name is not None:
        tag.name = name
        tag.slug = slugify(name)
    if color is not None:
        tag.color = color
    await db.flush()
    return tag


async def delete_tag(db: AsyncSession, tag_id: uuid.UUID) -> None:
    """Delete a tag by ID."""
    tag = await get_tag_by_id(db, tag_id)
    await db.delete(tag)
    await db.flush()
