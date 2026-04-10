"""
=============================================================================
Module: publish.markdown_gen
Description: Converts a Thought ORM object into a well-formatted Markdown
             file with YAML front matter suitable for MkDocs Material.
             将思绪ORM对象转换为带YAML前置元数据的Markdown文件，适用于MkDocs Material。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: (none – pure Python)
=============================================================================
"""

from datetime import datetime


def thought_to_markdown(
    title: str,
    content: str,
    summary: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    author: str | None = None,
    created_at: datetime | None = None,
    slug: str | None = None,
) -> str:
    """
    Build a complete Markdown document with YAML front matter.

    The front matter includes metadata consumed by MkDocs Material for
    search indexing, SEO meta tags, and navigation.

    Args:
        title: Article title.
        content: Markdown body.
        summary: Short description used for meta description / OG tags.
        category: Optional category string.
        tags: List of tag names.
        author: Display name of the author.
        created_at: Publication timestamp.
        slug: URL slug (informational, used in file naming).

    Returns:
        Full Markdown string ready to write to disk.
    """
    lines: list[str] = ["---"]

    # Title
    lines.append(f'title: "{_escape_yaml(title)}"')

    # Date
    if created_at:
        lines.append(f"date: {created_at.strftime('%Y-%m-%d')}")

    # Description / summary
    if summary:
        lines.append(f'description: "{_escape_yaml(summary)}"')

    # Author
    if author:
        lines.append(f'author: "{_escape_yaml(author)}"')

    # Category
    if category:
        lines.append(f'category: "{_escape_yaml(category)}"')

    # Tags
    if tags:
        lines.append("tags:")
        for tag in tags:
            lines.append(f"  - {tag}")

    # Slug (for reference)
    if slug:
        lines.append(f"slug: {slug}")

    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(content)
    lines.append("")

    return "\n".join(lines)


def _escape_yaml(value: str) -> str:
    """Escape double quotes inside YAML string values."""
    return value.replace('"', '\\"')
