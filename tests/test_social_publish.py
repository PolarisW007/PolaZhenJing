import sqlite3

from app import social_publish
from app import create_app
from app.social_publish import (build_manual_package, build_wechat_html,
                                build_x_post_text,
                                summarize_wechat_publish_result,
                                _wechat_content_source_url,
                                _wechat_clamp_text,
                                _wechat_uploadable_image,
                                _x_config_status)


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


def test_x_config_status_reads_env(monkeypatch):
    monkeypatch.setenv("X_USER_ACCESS_TOKEN", "x-user-token-demo")

    status = _x_config_status()

    assert status["configured"] is True
    assert status["token_tail"] == "n-demo"


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
    assert "/assets/vendor/tinymce/tinymce.min.js" in body
    assert "langs/zh-Hans.js" in body
    assert "language: 'zh-Hans'" in body
    assert "upload-card" in body
    assert "fonts.googleapis.com/css2" in body
    assert 'rel="preload" as="style"' in body

    asset_response = client.get("/assets/vendor/tinymce/tinymce.min.js")
    assert asset_response.status_code == 200
    assert asset_response.content_length and asset_response.content_length > 100_000

    lang_response = client.get("/assets/vendor/tinymce/langs/zh-Hans.js")
    assert lang_response.status_code == 200
    assert "tinymce.addI18n" in lang_response.get_data(as_text=True)
