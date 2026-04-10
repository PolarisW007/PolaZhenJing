"""
=============================================================================
Module: sharing.service
Description: Generate social-media share URLs and Open Graph metadata for
             thoughts. Supports X/Twitter, Weibo, Xiaohongshu, and generic
             clipboard sharing.
             生成社交媒体分享URL和Open Graph元数据。支持X/Twitter、微博、小红书和剪贴板分享。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: urllib
=============================================================================
"""

from urllib.parse import quote

from app.config import settings


def _post_url(slug: str) -> str:
    """Build the public URL for a published thought."""
    base = settings.SITE_BASE_URL.rstrip("/")
    return f"{base}/posts/{slug}/"


def generate_share_data(
    title: str,
    slug: str,
    summary: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """
    Generate a complete set of sharing links and metadata for a thought.

    Returns a dict with:
        - url: public page URL
        - og: Open Graph metadata dict
        - platforms: dict of platform -> share URL
        - share_text: pre-formatted text for copy-paste

    Args:
        title: Thought title.
        slug: URL slug.
        summary: Optional description.
        tags: Optional list of tag names.
    """
    url = _post_url(slug)
    description = summary or title
    hashtags = " ".join(f"#{t}" for t in (tags or []))
    share_text = f"{title}\n\n{description}\n\n{hashtags}\n{url}"

    platforms = {
        "x": _twitter_share_url(url, title, tags),
        "weibo": _weibo_share_url(url, title),
        "xiaohongshu": _xiaohongshu_share_text(title, description, tags, url),
    }

    og_meta = {
        "og:title": title,
        "og:description": description,
        "og:url": url,
        "og:type": "article",
        "og:site_name": settings.APP_NAME,
        "twitter:card": "summary",
        "twitter:title": title,
        "twitter:description": description,
    }

    return {
        "url": url,
        "og": og_meta,
        "platforms": platforms,
        "share_text": share_text,
    }


# ── Platform-specific helpers ────────────────────────────────────────────

def _twitter_share_url(url: str, text: str, tags: list[str] | None = None) -> str:
    """Build an X/Twitter intent URL."""
    hashtag_str = ",".join(tags) if tags else ""
    base = "https://twitter.com/intent/tweet"
    params = f"?text={quote(text)}&url={quote(url)}"
    if hashtag_str:
        params += f"&hashtags={quote(hashtag_str)}"
    return base + params


def _weibo_share_url(url: str, title: str) -> str:
    """Build a Weibo share URL."""
    base = "https://service.weibo.com/share/share.php"
    return f"{base}?url={quote(url)}&title={quote(title)}"


def _xiaohongshu_share_text(
    title: str, description: str, tags: list[str] | None, url: str
) -> str:
    """
    Xiaohongshu does not have a web share intent, so we return
    pre-formatted text the user can paste into the app.
    """
    hashtags = " ".join(f"#{t}" for t in (tags or []))
    return f"{title}\n\n{description}\n\n{hashtags}\n\n{url}"
