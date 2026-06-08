"""Tests for the article edit page rich editor integration."""

from app import create_app


def _admin_client():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"
    return client


def test_article_edit_page_uses_local_tinymce_assets():
    client = _admin_client()
    response = client.get("/admin/articles/2026-04-11-test-article.md/edit")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    # No legacy EasyMDE CDN reference.
    assert "cdn.jsdelivr.net/npm/easymde" not in body
    # Uses the same local TinyMCE runtime as the upload page.
    assert "/assets/vendor/tinymce/tinymce.min.js?v=6.8.5-pzj-20260602" in body
    assert "cache_suffix: TINYMCE_CACHE_SUFFIX" in body
    # Rich / Markdown mode switch and related wiring.
    assert 'name="editor_mode"' in body
    assert 'id="rich-content"' in body
    assert 'id="content"' in body
    assert 'id="content-format"' in body
    assert "TINYMCE_SCRIPT_URL" in body
    assert "language: 'zh-Hans'" in body
    # Editor flex layout (prevents iframe collapse) is preserved.
    assert "display: flex !important" in body


def test_preview_endpoint_returns_html_for_rich_format():
    client = _admin_client()
    html_body = "<h1>Hi</h1><p>raw <strong>html</strong></p>"
    response = client.post(
        "/admin/articles/2026-04-11-test-article.md/preview",
        data={"body": html_body, "content_format": "rich_html"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["format"] == "rich_html"
    assert payload["html"] == html_body


def test_preview_endpoint_renders_markdown_for_markdown_format():
    client = _admin_client()
    response = client.post(
        "/admin/articles/2026-04-11-test-article.md/preview",
        data={"body": "# 标题\n\n**加粗**", "content_format": "markdown"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["format"] == "markdown"
    assert "<h1" in payload["html"]
    assert "加粗</h1>" in payload["html"] or "<strong>加粗</strong>" in payload["html"]


def test_preview_endpoint_defaults_to_markdown_when_format_missing():
    client = _admin_client()
    response = client.post(
        "/admin/articles/2026-04-11-test-article.md/preview",
        data={"body": "## only markdown"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["format"] == "markdown"
    assert "<h2" in payload["html"]
