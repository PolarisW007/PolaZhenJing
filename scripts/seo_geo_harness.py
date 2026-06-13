#!/usr/bin/env python3
"""SEO/GEO metadata harness for Jekyll posts and portal static pages."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app import create_app
from app.uploader import POSTS_DIR, _article_admin_filename, _article_short_code


ROOT = Path(__file__).resolve().parents[1]


def check_jekyll_posts() -> list[str]:
    errors: list[str] = []
    head_path = ROOT / "_includes" / "head.html"
    if not head_path.exists():
        return errors
    # Legacy Jekyll rendering is no longer the online source of truth.
    # Flask rendering derives summaries/images and emits current metadata, so
    # this harness keeps legacy Jekyll checks non-blocking.
    return errors


def check_static_portal() -> list[str]:
    errors: list[str] = []
    for rel in ["portal/index.html", "portal/about.html", "portal/agent.html"]:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token in ["canonical", "og:image", "twitter:card", "application/ld+json"]:
            if token not in text:
                errors.append(f"{rel} missing {token}")
    return errors


def check_legacy_post_front_matter() -> list[str]:
    errors: list[str] = []
    for post in (ROOT / "_posts").glob("*.md"):
        raw = post.read_text(encoding="utf-8", errors="ignore")
        if not raw.startswith("---"):
            errors.append(f"{post.name} missing front matter")
            continue
        front = raw.split("---", 2)[1]
        for key in ["title", "date"]:
            if not re.search(rf"^{key}:", front, re.M):
                errors.append(f"{post.name} missing {key}")
    return errors


def _first_post_filename() -> str | None:
    posts = sorted(Path(POSTS_DIR).glob("*.md"), reverse=True)
    return posts[0].name if posts else None


def check_flask_geo_routes() -> list[str]:
    errors: list[str] = []
    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY="seo-geo-harness")
    client = app.test_client()

    filename = _first_post_filename()
    if not filename:
        return ["no markdown posts found for Flask GEO route checks"]
    admin_filename = _article_admin_filename(filename)
    short_code = _article_short_code(filename)
    short_url = f"https://aipd.me/s/{short_code}"
    canonical_url = f"https://aipd.me/articles/{admin_filename}"

    article_resp = client.get(f"/articles/{admin_filename}", base_url="https://aipd.me")
    if article_resp.status_code != 200:
        errors.append(f"article route status {article_resp.status_code}")
        article_html = ""
    else:
        article_html = article_resp.get_data(as_text=True)

    for token in [
        '<meta name="robots" content="index,follow,max-image-preview:large">',
        f'<link rel="canonical" href="{canonical_url}">',
        f'<link rel="shortlink" href="{short_url}">',
        f'<meta property="og:url" content="{short_url}">',
        '<meta property="og:image:type" content="image/jpeg">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="thumbnail" content="',
        'data-copy-shortlink',
        '<script type="application/ld+json">',
        '"@graph"',
        '"Article"',
        '"WebPage"',
        '"BreadcrumbList"',
        '"dateModified"',
        '"keywords"',
        '"wordCount"',
        '"articleSection"',
    ]:
        if token not in article_html:
            errors.append(f"article HTML missing {token}")
    image_match = re.search(r'<meta property="og:image" content="([^"]+)"', article_html)
    if not image_match:
        errors.append("article HTML missing og:image")
    elif "/assets/images/share/" not in image_match.group(1) or not image_match.group(1).endswith("-og.jpg"):
        errors.append(f"og:image is not generated OG JPEG share asset: {image_match.group(1)}")
    if "-wechat.jpg" not in article_html:
        errors.append("article HTML missing generated WeChat share image")

    short_resp = client.get(f"/s/{short_code}", base_url="https://aipd.me")
    if short_resp.status_code != 200:
        errors.append(f"short route status {short_resp.status_code}")

    index_resp = client.get("/articles", base_url="https://aipd.me")
    index_html = index_resp.get_data(as_text=True)
    if index_resp.status_code != 200:
        errors.append(f"article index status {index_resp.status_code}")
    for token in ['"@type": "ItemList"', canonical_url, "https://aipd.me/feed.xml", "https://aipd.me/articles.json"]:
        if token not in index_html:
            errors.append(f"article index missing {token}")

    sitemap_resp = client.get("/sitemap.xml", base_url="https://aipd.me")
    sitemap = sitemap_resp.get_data(as_text=True)
    if sitemap_resp.status_code != 200:
        errors.append(f"sitemap status {sitemap_resp.status_code}")
    for token in [canonical_url, "https://aipd.me/articles", "https://aipd.me/feed.xml", "https://aipd.me/articles.json", "<urlset"]:
        if token not in sitemap:
            errors.append(f"sitemap missing {token}")

    robots_resp = client.get("/robots.txt", base_url="https://aipd.me")
    robots = robots_resp.get_data(as_text=True)
    if robots_resp.status_code != 200:
        errors.append(f"robots status {robots_resp.status_code}")
    for token in ["User-agent: *", "Disallow: /admin/", "Disallow: /PolaZhenjing/admin/", "Sitemap: https://aipd.me/sitemap.xml"]:
        if token not in robots:
            errors.append(f"robots.txt missing {token}")

    llms_resp = client.get("/llms.txt", base_url="https://aipd.me")
    llms = llms_resp.get_data(as_text=True)
    if llms_resp.status_code != 200:
        errors.append(f"llms status {llms_resp.status_code}")
    for token in [
        "# 织梦空间 / PolaZhenJing",
        "## Site Identity",
        "## Share Metadata Contract",
        "## Article Index",
        canonical_url,
        short_url,
        "JSON Feed",
    ]:
        if token not in llms:
            errors.append(f"llms.txt missing {token}")

    feed_resp = client.get("/feed.xml", base_url="https://aipd.me")
    feed = feed_resp.get_data(as_text=True)
    if feed_resp.status_code != 200:
        errors.append(f"feed status {feed_resp.status_code}")
    for token in ["<rss version=\"2.0\">", canonical_url, "<channel>"]:
        if token not in feed:
            errors.append(f"feed.xml missing {token}")

    json_resp = client.get("/articles.json", base_url="https://aipd.me")
    data = json_resp.get_json(silent=True) or {}
    if json_resp.status_code != 200:
        errors.append(f"articles.json status {json_resp.status_code}")
    if data.get("feed_url") != "https://aipd.me/articles.json":
        errors.append("articles.json feed_url mismatch")
    if not any(item.get("url") == canonical_url and item.get("external_url") == short_url for item in data.get("items", [])):
        errors.append("articles.json missing sample canonical/shortlink item")

    return errors


def main() -> int:
    errors = (
        check_jekyll_posts()
        + check_static_portal()
        + check_legacy_post_front_matter()
        + check_flask_geo_routes()
    )
    print(json.dumps({"ok": not errors, "error_count": len(errors), "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
