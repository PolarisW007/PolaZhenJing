"""
=============================================================================
Module: tests/test_markdown_gen
Description: Unit tests for the markdown generation module.
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: pytest, app.publish.markdown_gen
=============================================================================
"""

from datetime import datetime, timezone

from app.publish.markdown_gen import thought_to_markdown


def test_basic_markdown_generation():
    """Verify that front matter and content are properly formatted."""
    result = thought_to_markdown(
        title="Test Thought",
        content="This is the body content.",
        summary="A brief summary",
        category="Tech",
        tags=["python", "ai"],
        author="TestUser",
        created_at=datetime(2026, 4, 6, tzinfo=timezone.utc),
        slug="test-thought",
    )

    assert "---" in result
    assert 'title: "Test Thought"' in result
    assert "date: 2026-04-06" in result
    assert 'description: "A brief summary"' in result
    assert "- python" in result
    assert "- ai" in result
    assert "# Test Thought" in result
    assert "This is the body content." in result


def test_markdown_without_optional_fields():
    """Verify generation works with minimal fields."""
    result = thought_to_markdown(
        title="Minimal",
        content="Just content.",
    )

    assert 'title: "Minimal"' in result
    assert "# Minimal" in result
    assert "Just content." in result
    # Should not have tags or description lines
    assert "tags:" not in result
    assert "description:" not in result
