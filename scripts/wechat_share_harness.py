#!/usr/bin/env python3
"""Validate article share metadata for WeChat and social card crawlers."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402


def _first_admin_filename() -> str:
    posts = sorted((ROOT / "_posts").glob("*.md"), reverse=True)
    if not posts:
        raise AssertionError("No markdown posts found")
    for post in posts:
        text = post.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"^summary:\s*.+", text, re.M):
            name = post.name
            match = re.match(r"^\d{4}-\d{2}-\d{2}-(.+\.md)$", name)
            return match.group(1) if match else name
    name = posts[0].name
    match = re.match(r"^\d{4}-\d{2}-\d{2}-(.+\.md)$", name)
    return match.group(1) if match else name


def _content(html: str, name: str, attr: str = "property") -> str:
    pattern = rf'<meta\s+{attr}="{re.escape(name)}"\s+content="([^"]*)"'
    match = re.search(pattern, html)
    if not match:
        raise AssertionError(f"Missing meta {attr}={name}")
    return match.group(1)


def main() -> int:
    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY="wechat-share-harness")
    client = app.test_client()
    filename = _first_admin_filename()
    response = client.get(
        f"/admin/articles/{filename}",
        base_url="https://aipd.me",
        headers={"X-Script-Name": "/PolaZhenjing"},
    )
    assert response.status_code == 200, response.status_code
    html = response.get_data(as_text=True)

    og_title = _content(html, "og:title")
    og_description = _content(html, "og:description")
    og_url = _content(html, "og:url")
    og_image = _content(html, "og:image")
    twitter_card = _content(html, "twitter:card", attr="name")
    itemprop_image = _content(html, "image", attr="itemprop")

    assert og_title.strip(), "og:title is empty"
    assert 20 <= len(og_description) <= 190, f"bad description length: {len(og_description)}"
    assert og_url.startswith("https://aipd.me/PolaZhenjing/articles/"), og_url
    assert og_image.startswith("https://aipd.me/"), og_image
    assert itemprop_image == og_image, "itemprop image should match og:image"
    assert twitter_card == "summary_large_image", twitter_card
    assert "updateAppMessageShareData" in html, "WeChat app-message share hook missing"
    assert "updateTimelineShareData" in html, "WeChat timeline share hook missing"
    assert "TL;DR" not in html, "Public article should not show TL;DR label"
    assert "Twitter" not in html, "Public article should not show admin Twitter share button"
    assert "LinkedIn" not in html, "Public article should not show admin LinkedIn share button"
    assert "copy-link-btn" not in html, "Public article should not show admin copy share button"

    admin_client = app.test_client()
    with admin_client.session_transaction(base_url="https://aipd.me") as session:
        session.update({"user_id": 1, "role": "admin"})
    admin_response = admin_client.get(
        f"/admin/articles/{filename}",
        base_url="https://aipd.me",
        headers={"X-Script-Name": "/PolaZhenjing"},
    )
    assert admin_response.status_code == 200, admin_response.status_code
    admin_html = admin_response.get_data(as_text=True)
    assert "Twitter" in admin_html, "Admin article should show Twitter share button"
    assert "LinkedIn" in admin_html, "Admin article should show LinkedIn share button"
    assert "TL;DR" not in admin_html, "Admin article should not show TL;DR label"

    config_resp = client.get(
        "/admin/api/wechat/share-config?url=https%3A%2F%2Faipd.me%2FPolaZhenjing%2Farticles%2Fdemo.md",
        base_url="https://aipd.me",
        headers={"X-Script-Name": "/PolaZhenjing"},
    )
    assert config_resp.status_code == 200, config_resp.status_code
    data = config_resp.get_json()
    assert data and data.get("configured") is False, data

    print("wechat_share_harness: ok")
    print(f"article={filename}")
    print(f"og_url={og_url}")
    print(f"og_image={og_image}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
