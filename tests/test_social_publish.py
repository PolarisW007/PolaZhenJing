import sqlite3

from app import social_publish
from app.social_publish import (build_manual_package, build_wechat_html,
                                summarize_wechat_publish_result,
                                _wechat_clamp_text)


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
