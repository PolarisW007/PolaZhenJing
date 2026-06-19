#!/usr/bin/env python3
"""Validate article share metadata for WeChat and social card crawlers."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.uploader import _article_short_code, _resolve_post_filename  # noqa: E402


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


def _asset_regression_filename(default: str) -> str:
    target = ROOT / "_posts" / "2026-05-24-yi-ge-ren-you-zheng-zhi-you-jia-20260524.md"
    if target.exists():
        return "yi-ge-ren-you-zheng-zhi-you-jia-20260524.md"
    return default


def _content(html: str, name: str, attr: str = "property") -> str:
    pattern = rf'<meta\s+{attr}="{re.escape(name)}"\s+content="([^"]*)"'
    match = re.search(pattern, html)
    if not match:
        raise AssertionError(f"Missing meta {attr}={name}")
    return match.group(1)


def _wechat_img_url(html: str) -> str:
    match = re.search(r"imgUrl:\s*\"([^\"]+)\"", html)
    if not match:
        raise AssertionError("Missing WECHAT_SHARE imgUrl")
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
    wechat_image = _wechat_img_url(html)
    twitter_card = _content(html, "twitter:card", attr="name")
    itemprop_image = _content(html, "image", attr="itemprop")

    assert og_title.strip(), "og:title is empty"
    assert 20 <= len(og_description) <= 190, f"bad description length: {len(og_description)}"
    assert re.match(r"^https://aipd\.me/c/[0-9a-f]{8}$", og_url), og_url
    assert og_image.startswith("https://aipd.me/"), og_image
    assert "/assets/images/share/" in og_image, f"OG share image should use generated share asset: {og_image}"
    assert og_image.endswith("-og.jpg"), f"OG share image should be large-card JPEG: {og_image}"
    assert wechat_image.startswith("https://aipd.me/"), wechat_image
    assert wechat_image.endswith("-wechat.jpg"), f"WeChat image should be square JPEG: {wechat_image}"
    assert '<meta property="og:image:width" content="1200">' in html
    assert '<meta property="og:image:height" content="630">' in html
    assert '<meta name="thumbnail" content="' in html
    assert itemprop_image == og_image, "itemprop image should match og:image"
    assert twitter_card == "summary_large_image", twitter_card
    assert "updateAppMessageShareData" in html, "WeChat app-message share hook missing"
    assert "updateTimelineShareData" in html, "WeChat timeline share hook missing"
    assert "WECHAT_SHARE" in html, "WeChat share payload missing"
    assert "https://aipd.me/PolaZhenjing/admin/api/wechat/share-config" in html, "WeChat config endpoint should use public app prefix"
    assert "https://aipd.me/PolaZhenjing/admin/api/wechat/share-diagnostics" in html, "WeChat diagnostics endpoint missing"
    assert "wx.error" in html, "WeChat JS-SDK error diagnostics missing"
    assert "__PZJ_WECHAT_SHARE_READY" in html, "WeChat readiness flag missing"
    assert "checkJsApi" in html, "WeChat JS API availability diagnostics missing"
    assert "showMenuItems" in html, "WeChat share menu visibility hook missing"
    assert "share-api-registered" in html, "WeChat share API registration diagnostics missing"
    assert "reportWechatShareByImage" in html, "WeChat image beacon diagnostics fallback missing"
    assert "TL;DR" not in html, "Public article should not show TL;DR label"
    assert "Twitter" not in html, "Public article should not show admin Twitter share button"
    assert "LinkedIn" not in html, "Public article should not show admin LinkedIn share button"
    assert "copy-link-btn" not in html, "Public article should not show admin copy share button"
    assert "data-copy-cardlink" not in html, "Public article should not show card-link copy button"
    assert "data-copy-wechat-card" not in html, "Public article should not show WeChat image card button"
    assert "复制卡片链接" not in html, "Public article card-link copy label should be admin-only"
    assert "微信图文卡片" not in html, "WeChat image card fallback label should be admin-only"

    asset_filename = _asset_regression_filename(filename)
    public_resp = client.get(
        f"/articles/{asset_filename}",
        base_url="https://aipd.me",
    )
    assert public_resp.status_code == 200, public_resp.status_code
    public_html = public_resp.get_data(as_text=True)
    public_og_image = _content(public_html, "og:image")
    public_twitter_image = _content(public_html, "twitter:image", attr="name")
    assert public_og_image.startswith("https://aipd.me/PolaZhenjing/assets/"), public_og_image
    assert public_og_image.endswith("-og.jpg"), public_og_image
    assert public_twitter_image == public_og_image, "Root public twitter image should match og:image"
    assert "/PolaZhenjing/assets/images/" in public_html, "Public article media should use app asset prefix"
    assert 'href="/PolaZhenjing/assets/css/main.css"' in public_html, "Public article CSS should use app asset prefix"
    assert 'src="/assets/images/generated/' not in public_html, "Root public article should not render root generated asset URLs"
    assert 'src="/assets/images/uploads/' not in public_html, "Root public article should not render root uploaded asset URLs"
    assert 'href="/assets/css/' not in public_html, "Root public article should not render root CSS asset URLs"

    actual_filename = _resolve_post_filename(asset_filename)
    assert actual_filename, asset_filename
    short_code = _article_short_code(actual_filename)
    short_resp = client.get(
        f"/s/{short_code}",
        base_url="https://aipd.me",
    )
    assert short_resp.status_code == 200, short_resp.status_code
    short_html = short_resp.get_data(as_text=True)
    assert f'https://aipd.me/s/{short_code}' in short_html, "Short-link page should expose short share URL"
    assert f'https://aipd.me/c/{short_code}' in short_html, "Short-link page should expose social card URL"
    assert f'https://aipd.me/articles/{asset_filename}' in short_html, "Short-link page should expose canonical URL"
    assert "https://aipd.me/PolaZhenjing/admin/api/wechat/share-config" in short_html, "Short-link page should call prefixed WeChat API"

    card_resp = client.get(
        f"/c/{short_code}",
        base_url="https://aipd.me",
    )
    assert card_resp.status_code == 200, card_resp.status_code
    card_html = card_resp.get_data(as_text=True)
    assert f'<link rel="canonical" href="https://aipd.me/articles/{asset_filename}">' in card_html
    assert f'<link rel="shortlink" href="https://aipd.me/s/{short_code}">' in card_html
    assert f'<meta property="og:url" content="https://aipd.me/c/{short_code}">' in card_html
    assert '<meta property="og:image:width" content="1200">' in card_html
    assert '<meta name="twitter:card" content="summary_large_image">' in card_html
    assert "jweixin" not in card_html.lower(), "Card page should remain lightweight"

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
    assert "复制卡片链接" in admin_html, "Admin card-link copy helper missing"
    assert "阅读短链" in admin_html, "Admin read-link copy helper missing"
    assert "微信图文卡片" in admin_html, "Admin WeChat image-card helper missing"
    assert "即刻" in admin_html, "Jike share helper missing"
    assert "TL;DR" not in admin_html, "Admin article should not show TL;DR label"

    config_resp = client.get(
        "/admin/api/wechat/share-config?url=https%3A%2F%2Faipd.me%2FPolaZhenjing%2Farticles%2Fdemo.md",
        base_url="https://aipd.me",
        headers={"X-Script-Name": "/PolaZhenjing"},
    )
    assert config_resp.status_code in {200, 502}, config_resp.status_code
    data = config_resp.get_json()
    assert data, data
    if data.get("configured") is True:
        for key in ["appId", "timestamp", "nonceStr", "signature"]:
            assert data.get(key), data
    else:
        assert data.get("configured") is False, data
        assert data.get("reason") in {
            "missing-wechat-app-id",
            "missing-wechat-ticket",
            "wechat-api-error",
        }, data

    diag_resp = client.get(
        "/admin/api/wechat/share-diagnostics",
        base_url="https://aipd.me",
        query_string={
            "status": "script-start",
            "page_url": "https://aipd.me/s/49c0c4e8",
            "share_url": "https://aipd.me/s/49c0c4e8",
            "err_msg": "image-probe",
        },
    )
    assert diag_resp.status_code == 204, diag_resp.status_code

    print("wechat_share_harness: ok")
    print(f"article={filename}")
    print(f"og_url={og_url}")
    print(f"og_image={og_image}")
    print(f"wechat_image={wechat_image}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
