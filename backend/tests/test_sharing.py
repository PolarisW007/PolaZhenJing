"""
=============================================================================
Module: tests/test_sharing
Description: Unit tests for the social sharing service module.
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: pytest, app.sharing.service
=============================================================================
"""

from app.sharing.service import generate_share_data


def test_share_data_structure():
    """Verify that generate_share_data returns all expected fields."""
    data = generate_share_data(
        title="My Thought",
        slug="my-thought",
        summary="A summary",
        tags=["ai", "python"],
    )

    assert "url" in data
    assert "og" in data
    assert "platforms" in data
    assert "share_text" in data

    # Check platform keys
    assert "x" in data["platforms"]
    assert "weibo" in data["platforms"]
    assert "xiaohongshu" in data["platforms"]

    # Check OG tags
    assert data["og"]["og:title"] == "My Thought"
    assert "twitter.com/intent/tweet" in data["platforms"]["x"]
    assert "weibo.com/share" in data["platforms"]["weibo"]


def test_share_data_without_tags():
    """Verify sharing works without tags."""
    data = generate_share_data(
        title="Simple",
        slug="simple",
    )

    assert data["og"]["og:title"] == "Simple"
    assert "url" in data
