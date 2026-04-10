"""
=============================================================================
Module: publish.service
Description: Orchestrates publishing – writes Markdown files to the MkDocs
             docs directory and triggers MkDocs builds.
             发布编排服务 - 将Markdown文件写入MkDocs文档目录并触发MkDocs构建。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: app.publish.markdown_gen, app.thoughts.service, pathlib
Major changes:
    2026-04-06 – Initial implementation
=============================================================================
"""

import asyncio
import logging
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequestException, NotFoundException
from app.config import settings
from app.publish.markdown_gen import thought_to_markdown
from app.thoughts.models import ThoughtStatus
from app.thoughts.service import get_thought_by_id

logger = logging.getLogger("polazj.publish")


def _posts_dir() -> Path:
    """Return the MkDocs docs/posts directory, creating it if needed."""
    posts = Path(settings.SITE_DIR) / "docs" / "posts"
    posts.mkdir(parents=True, exist_ok=True)
    return posts


async def publish_thought(db: AsyncSession, thought_id: uuid.UUID) -> Path:
    """
    Publish a single thought as a Markdown file for MkDocs.

    Business rules:
        - Thought must exist and be in PUBLISHED status.
        - File is written to site/docs/posts/{slug}.md.

    Args:
        db: Database session.
        thought_id: UUID of the thought to publish.

    Returns:
        Path to the generated Markdown file.

    Raises:
        BadRequestException: If thought is not in PUBLISHED status.
    """
    thought = await get_thought_by_id(db, thought_id)

    if thought.status != ThoughtStatus.PUBLISHED:
        raise BadRequestException(
            detail="Only published thoughts can be exported to the site"
        )

    tag_names = [t.name for t in thought.tags]
    author_name = thought.author.display_name or thought.author.username

    md_content = thought_to_markdown(
        title=thought.title,
        content=thought.content,
        summary=thought.summary,
        category=thought.category,
        tags=tag_names,
        author=author_name,
        created_at=thought.created_at,
        slug=thought.slug,
    )

    file_path = _posts_dir() / f"{thought.slug}.md"
    file_path.write_text(md_content, encoding="utf-8")
    logger.info("Published thought '%s' to %s", thought.title, file_path)
    return file_path


async def build_mkdocs() -> bool:
    """
    Trigger a MkDocs build (site/mkdocs.yml -> site/site/).

    Returns:
        True if the build succeeded, False otherwise.

    Performance note:
        Spawns `mkdocs build` as a subprocess; typically completes in <5 s
        for small sites.
    """
    site_dir = Path(settings.SITE_DIR)
    try:
        proc = await asyncio.create_subprocess_exec(
            "mkdocs", "build",
            cwd=str(site_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error("MkDocs build failed: %s", stderr.decode())
            return False
        logger.info("MkDocs build succeeded")
        return True
    except FileNotFoundError:
        logger.error("mkdocs command not found – is it installed?")
        return False
