import sqlite3
from pathlib import Path

from app import social_publish
from app import create_app
from app.social_publish import (build_manual_package, build_wechat_html,
                                build_x_post_text,
                                summarize_wechat_publish_result,
                                _wechat_content_source_url,
                                _wechat_clamp_text,
                                _wechat_uploadable_image)
from app.uploader import POSTS_DIR, _article_admin_filename, _article_short_code


def sample_context():
    return {
        "title": "一篇很长的 AI 文章标题用于测试发布包",
        "description": "这是一段摘要。",
        "summary": "这是一段摘要。",
        "body": "# 标题\n\n这里是正文。\n\n![图](/assets/images/test_cover.jpg)\n\n<script>alert(1)</script>",
        "plain_body": "这里是正文，包含足够的信息用于生成发布包。",
        "tags": ["AI", "产品", "自动化"],
        "cover": "/assets/images/test_cover.jpg",
        "cover_url": "https://aipd.me/PolaZhenjing/assets/images/test_cover.jpg",
        "public_url": "https://aipd.me/articles/demo.md",
        "pages_url": "https://example.com/demo/",
    }


def test_build_xiaohongshu_package_is_short_and_actionable():
    package = build_manual_package(sample_context(), "xiaohongshu")

    assert package["platform"] == "xiaohongshu"
    assert len(package["title"]) <= 20
    assert "#AI" in package["body"]
    assert package["console_url"].startswith("https://")
    assert package["checklist"]


def test_build_wechat_html_strips_script_and_rewrites_images():
    html = build_wechat_html(
        sample_context(),
        {"/assets/images/test_cover.jpg": "https://mmbiz.qpic.cn/demo.jpg"},
    )

    assert "script" not in html.lower()
    assert "https://mmbiz.qpic.cn/demo.jpg" in html
    assert "<h1" in html


def test_social_publish_schema_is_idempotent(tmp_path, monkeypatch):
    db_path = tmp_path / "wiki.db"
    monkeypatch.setattr(social_publish, "DB_PATH", db_path)

    social_publish.init_schema()
    social_publish.init_schema()

    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        conn.close()
    assert "social_publications" in tables
    assert "social_publication_events" in tables


def test_summarize_wechat_publish_result_extracts_article_url():
    result = summarize_wechat_publish_result({
        "publish_status": 0,
        "article_detail": {
            "item": [
                {"article_url": "https://mp.weixin.qq.com/s/demo"}
            ]
        },
    })

    assert result["status"] == "published"
    assert result["article_url"] == "https://mp.weixin.qq.com/s/demo"


def test_wechat_clamp_text_limits_utf8_bytes():
    text = "中文" * 80
    result = _wechat_clamp_text(text, 54)

    assert len(result.encode("utf-8")) <= 54
    assert result


def test_wechat_uploadable_image_accepts_png(tmp_path):
    path = tmp_path / "cover.png"
    path.write_bytes(b"not-real-but-extension-is-ok")

    upload_path, temporary = _wechat_uploadable_image(path)

    assert upload_path == path
    assert temporary is False


def test_wechat_content_source_url_skips_localhost():
    ctx = {
        "public_url": "http://localhost/articles/demo.md",
        "pages_url": "https://polarisw007.github.io/PolaZhenJing/demo/",
    }

    assert _wechat_content_source_url(ctx) == ctx["pages_url"]


def test_build_x_post_text_keeps_within_limit():
    ctx = sample_context()
    ctx["description"] = "这是一段很长的摘要。" * 80

    text = build_x_post_text(ctx)

    assert len(text) <= 280
    assert ctx["title"] in text
    assert ctx["public_url"] in text


def test_build_x_manual_package_is_copyable_and_limited():
    ctx = sample_context()
    ctx["description"] = "这是一段很长的摘要。" * 80

    package = build_manual_package(ctx, "x")

    assert package["platform"] == "x"
    assert package["platform_name"] == "X"
    assert len(package["body"]) <= 280
    assert package["body"] == build_x_post_text(ctx)
    assert package["console_url"].startswith("https://x.com/")
    assert "手动发布" in " ".join(package["checklist"])


def test_social_publish_x_uses_manual_package_ui():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"

    response = client.get("/admin/social/articles/2026-05-24-yi-ge-ren-you-zheng-zhi-you-jia-20260524.md")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "生成发布包" in body
    assert "https://x.com/compose/post" in body
    assert "X_USER_ACCESS_TOKEN" not in body
    assert "发布到 X" not in body
    assert "/x/post" not in body


def test_upload_page_uses_local_tinymce_assets():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"

    response = client.get("/admin/upload")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "cdn.jsdelivr.net/npm/tinymce" not in body
    assert "/assets/vendor/tinymce/tinymce.min.js?v=6.8.5-pzj-20260602" in body
    assert "cache_suffix: TINYMCE_CACHE_SUFFIX" in body
    assert "langs/zh-Hans.js" in body
    assert "language: 'zh-Hans'" in body
    assert "display: flex !important" in body
    assert "min-height: 360px !important" in body
    assert "upload-card" in body
    assert "fonts.googleapis.com/css2" in body
    assert 'rel="preload" as="style"' in body

    asset_response = client.get("/assets/vendor/tinymce/tinymce.min.js")
    assert asset_response.status_code == 200
    assert asset_response.content_length and asset_response.content_length > 100_000

    lang_response = client.get("/assets/vendor/tinymce/langs/zh-Hans.js")
    assert lang_response.status_code == 200
    assert "tinymce.addI18n" in lang_response.get_data(as_text=True)

    manifest_response = client.get("/assets/vendor/tinymce/tinymce-manifest.json")
    assert manifest_response.status_code == 200
    assert manifest_response.get_json()["asset_version"] == "6.8.5-pzj-20260602"


def test_admin_links_respect_script_name_prefix():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"

    response = client.get(
        "/admin/articles",
        headers={"X-Script-Name": "/PolaZhenjing"},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/PolaZhenjing/admin/upload"' in body
    assert 'href="/PolaZhenjing/admin/articles"' in body
    assert 'href="/admin/upload"' not in body
    assert 'href="/admin/articles"' not in body


def _sample_post_filename() -> str:
    posts = sorted(Path(POSTS_DIR).glob("*.md"), reverse=True)
    assert posts
    return posts[0].name


def test_public_article_short_link_renders_share_card_metadata():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    filename = _sample_post_filename()
    admin_filename = _article_admin_filename(filename)
    short_code = _article_short_code(filename)
    short_url = f"https://aipd.me/s/{short_code}"
    canonical_url = f"https://aipd.me/articles/{admin_filename}"

    response = client.get(f"/s/{short_code}", base_url="https://aipd.me")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f'<link rel="canonical" href="{canonical_url}">' in body
    assert f'<meta property="og:url" content="{short_url}">' in body
    assert f'<meta name="twitter:url" content="{short_url}">' in body
    assert '<meta property="og:image:type" content="image/jpeg">' in body
    assert '<meta property="og:image:width" content="1200">' in body
    assert '<meta property="og:image:height" content="630">' in body
    assert "/assets/images/share/" in body
    assert "-og.jpg" in body
    assert "-wechat.jpg" in body
    assert '"mainEntityOfPage": ' in body
    assert '"@graph":' in body
    assert '"BreadcrumbList"' in body
    assert '"wordCount"' in body
    assert 'data-copy-shortlink' in body
    assert "复制短链接" in body
    assert "updateAppMessageShareData" in body
    assert "updateTimelineShareData" in body
    assert "https://aipd.me/PolaZhenjing/admin/api/wechat/share-config" in body
    assert "https://aipd.me/PolaZhenjing/admin/api/wechat/share-diagnostics" in body
    assert "wx.error" in body
    assert "__PZJ_WECHAT_SHARE_READY" in body
    assert "checkJsApi" in body
    assert "showMenuItems" in body
    assert "share-api-registered" in body
    assert "reportWechatShareByImage" in body

    long_response = client.get(f"/articles/{admin_filename}", base_url="https://aipd.me")
    long_body = long_response.get_data(as_text=True)

    assert long_response.status_code == 200
    assert short_url in long_body
    assert canonical_url in long_body


def test_wechat_share_diagnostics_supports_image_probe():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    response = client.get(
        "/admin/api/wechat/share-diagnostics",
        base_url="https://aipd.me",
        query_string={
            "status": "script-start",
            "page_url": "https://aipd.me/s/49c0c4e8",
            "share_url": "https://aipd.me/s/49c0c4e8",
            "err_msg": "image-probe",
        },
    )

    assert response.status_code == 204


def test_public_article_short_link_rejects_unknown_code():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    response = client.get("/s/00000000", base_url="https://aipd.me")

    assert response.status_code == 404


def test_geo_discovery_feeds_render():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    filename = _sample_post_filename()
    admin_filename = _article_admin_filename(filename)
    short_code = _article_short_code(filename)
    canonical_url = f"https://aipd.me/articles/{admin_filename}"
    short_url = f"https://aipd.me/s/{short_code}"

    robots = client.get("/robots.txt", base_url="https://aipd.me")
    assert robots.status_code == 200
    robots_body = robots.get_data(as_text=True)
    assert "Disallow: /admin/" in robots_body
    assert "Sitemap: https://aipd.me/sitemap.xml" in robots_body

    feed = client.get("/feed.xml", base_url="https://aipd.me")
    assert feed.status_code == 200
    feed_body = feed.get_data(as_text=True)
    assert "<rss version=\"2.0\">" in feed_body
    assert canonical_url in feed_body

    articles_json = client.get("/articles.json", base_url="https://aipd.me")
    assert articles_json.status_code == 200
    data = articles_json.get_json()
    assert data["feed_url"] == "https://aipd.me/articles.json"
    assert any(
        item["url"] == canonical_url and item["external_url"] == short_url
        for item in data["items"]
    )

    index = client.get("/articles", base_url="https://aipd.me")
    assert index.status_code == 200
    index_body = index.get_data(as_text=True)
    assert '"@type": "ItemList"' in index_body
    assert canonical_url in index_body
