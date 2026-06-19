"""Tests for the article edit page rich editor integration."""

import json

from app import create_app
from app import uploader


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
    assert "initRichEditor();\nsetEditorMode(initialMode);" not in body
    assert "Markdown 源码模式已就绪" in body
    assert ".tox-tinymce.editor-mode-hidden" in body
    assert "hideRichEditorSurface" in body
    assert "showRichEditorSurface" in body
    # Editor flex layout (prevents iframe collapse) is preserved.
    assert "display: flex !important" in body
    # Save must give immediate feedback and preserve the clicked save mode even
    # when submit buttons are disabled to prevent duplicate submissions.
    assert 'id="save-status"' in body
    assert 'id="enable_ai_revision"' in body
    assert 'id="ai-revision-panel"' in body
    assert 'hidden' in body
    assert 'id="revision_instruction"' in body
    assert 'name="revision_instruction"' in body
    assert 'disabled' in body
    assert "setAiRevisionEnabled(aiRevisionToggle.checked)" in body
    assert "event.submitter" in body
    assert 'input[type="hidden"][name="save_mode"]' in body
    assert "正在保存并按修改建议进行 AI 调整" in body
    assert "articleEditSubmitting" in body


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
    assert payload["format"] == "markdown"
    assert payload["canonical_markdown"]
    assert "<h1" in payload["html"]
    assert "<strong>html</strong>" in payload["html"]


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


def _isolated_article_client(tmp_path, monkeypatch):
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir()
    post_path = posts_dir / "2026-06-14-editor-image-test.md"
    post_path.write_text(
        "---\nlayout: deep-technical\ntitle: old title\ndate: 2026-06-14\n---\n\nseed\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("app.uploader.POSTS_DIR", str(posts_dir), raising=False)
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"
    return client, post_path


def test_edit_save_rich_html_sanitizes_clipboard_metadata_and_localizes_images(tmp_path, monkeypatch):
    client, post_path = _isolated_article_client(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "app.uploader._download_remote_image_to_richtext",
        lambda url: "/assets/images/richtext/2026-06/localized.jpg",
    )
    rich_body = """
    <article class="4ever-article" data-clipboard-cangjie="huge-internal-payload">
      <p style="font-size: 18px" data-block="x">第一段正文</p>
      <p><img src="https://alidocs.dingtalk.com/core/api/resources/img/demo.png?tmpCode=abc"
              data-src="https://fallback.example.com/image.jpg"
              style="width: 100px" class="doc-image"></p>
    </article>
    """

    response = client.post(
        "/admin/articles/editor-image-test.md/edit",
        data={
            "layout": "deep-technical",
            "theme": "claude",
            "title": "新标题",
            "date": "2026-06-14",
            "summary": "摘要",
            "body": rich_body,
            "content_format": "rich_html",
            "save_mode": "save",
        },
        follow_redirects=False,
    )
    saved = post_path.read_text(encoding="utf-8")

    assert response.status_code == 302
    assert "data-clipboard-cangjie" not in saved
    assert "style=" not in saved
    assert "<article" not in saved
    assert "https://alidocs.dingtalk.com" not in saved
    assert "/assets/images/richtext/2026-06/localized.jpg" in saved
    assert "第一段正文" in saved


def test_edit_save_markdown_keeps_markdown_images(tmp_path, monkeypatch):
    client, post_path = _isolated_article_client(tmp_path, monkeypatch)
    markdown_body = "# 标题\n\n![本地图](/assets/images/test_cover.jpg)\n\n正文"

    response = client.post(
        "/admin/articles/editor-image-test.md/edit",
        data={
            "layout": "deep-technical",
            "theme": "claude",
            "title": "Markdown 标题",
            "date": "2026-06-14",
            "body": markdown_body,
            "content_format": "markdown",
            "save_mode": "save",
        },
        follow_redirects=False,
    )
    saved = post_path.read_text(encoding="utf-8")

    assert response.status_code == 302
    assert "![本地图](/assets/images/test_cover.jpg)" in saved
    assert "正文" in saved


def test_edit_save_uses_rich_content_when_body_field_missing(tmp_path, monkeypatch):
    client, post_path = _isolated_article_client(tmp_path, monkeypatch)
    rich_body = "<p>只从 rich_content 提交的新正文</p>"

    response = client.post(
        "/admin/articles/editor-image-test.md/edit",
        data={
            "layout": "deep-technical",
            "theme": "claude",
            "title": "富文本兜底",
            "date": "2026-06-14",
            "rich_content": rich_body,
            "content_format": "rich_html",
            "save_mode": "save",
        },
        follow_redirects=False,
    )
    saved = post_path.read_text(encoding="utf-8")

    assert response.status_code == 302
    assert "只从 rich_content 提交的新正文" in saved
    assert "seed" not in saved


def test_edit_save_uses_markdown_content_when_body_field_missing(tmp_path, monkeypatch):
    client, post_path = _isolated_article_client(tmp_path, monkeypatch)
    markdown_body = "## 只从 content 提交的新正文\n\n正文第二段"

    response = client.post(
        "/admin/articles/editor-image-test.md/edit",
        data={
            "layout": "deep-technical",
            "theme": "claude",
            "title": "Markdown 兜底",
            "date": "2026-06-14",
            "content": markdown_body,
            "content_format": "markdown",
            "save_mode": "save",
        },
        follow_redirects=False,
    )
    saved = post_path.read_text(encoding="utf-8")

    assert response.status_code == 302
    assert "## 只从 content 提交的新正文" in saved
    assert "正文第二段" in saved
    assert "seed" not in saved


def test_editor_convert_api_markdown_to_rich_html():
    client = _admin_client()
    response = client.post(
        "/admin/api/editor/convert",
        json={
            "source_format": "markdown",
            "target_format": "rich_html",
            "content": "# 标题\n\n![图](/assets/a.png)\n\n正文",
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["format"] == "rich_html"
    assert "<h1" in payload["content"]
    assert '<img' in payload["content"]


def test_edit_save_revision_uses_canonical_markdown_before_llm(tmp_path, monkeypatch):
    client, post_path = _isolated_article_client(tmp_path, monkeypatch)
    seen = {}

    def fake_revision(content, title, revision_instruction, style="", rewrite_rate=50):
        seen["content"] = content
        seen["rewrite_rate"] = rewrite_rate
        return content + "\n\n补充一句。"

    monkeypatch.setattr("app.uploader._apply_revision_instruction", fake_revision)
    rich_body = "<h1>正文标题</h1><p>第一段</p><p><img src=\"/assets/images/test_cover.jpg\"></p>"

    response = client.post(
        "/admin/articles/editor-image-test.md/edit",
        data={
            "layout": "deep-technical",
            "theme": "claude",
            "title": "修订标题",
            "date": "2026-06-14",
            "body": rich_body,
            "content_format": "rich_html",
            "enable_ai_revision": "1",
            "rewrite_rate": "75",
            "revision_instruction": "补充一句",
            "save_mode": "save",
        },
        follow_redirects=False,
    )
    saved = post_path.read_text(encoding="utf-8")

    assert response.status_code == 302
    assert seen["rewrite_rate"] == 75
    assert "# 正文标题" in seen["content"]
    assert "<h1>" not in seen["content"]
    assert "补充一句。" in saved


def test_edit_save_ignores_revision_instruction_when_ai_disabled(tmp_path, monkeypatch):
    client, post_path = _isolated_article_client(tmp_path, monkeypatch)

    def fail_revision(*args, **kwargs):
        raise AssertionError("AI revision should not run unless explicitly enabled")

    monkeypatch.setattr("app.uploader._apply_revision_instruction", fail_revision)
    markdown_body = "# 原文标题\n\n![图](/assets/images/test_cover.jpg)\n\n原文正文"

    response = client.post(
        "/admin/articles/editor-image-test.md/edit",
        data={
            "layout": "deep-technical",
            "theme": "claude",
            "title": "不启用 AI",
            "date": "2026-06-14",
            "body": markdown_body,
            "content_format": "markdown",
            "rewrite_rate": "100",
            "revision_instruction": "删除所有图片并改写",
            "save_mode": "save",
        },
        follow_redirects=False,
    )
    saved = post_path.read_text(encoding="utf-8")

    assert response.status_code == 302
    assert "# 原文标题" in saved
    assert "![图](/assets/images/test_cover.jpg)" in saved
    assert "删除所有图片并改写" not in saved


def test_llm_revision_output_strips_thinking_and_preserves_media(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            payload = {
                "choices": [
                    {
                        "message": {
                            "content": "<think>I should explain this first.</think>\n\n# 新正文\n\n这里是改写后正文。"
                        }
                    }
                ]
            }
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr("app.uploader._get_minimax_api_key", lambda: "fake-key")
    monkeypatch.setattr("app.uploader.urlopen", lambda *args, **kwargs: FakeResponse())
    original = "# 原文\n\n![封面](/assets/images/cover.png)\n\n正文\n\n<img src=\"/assets/a.png\">"

    revised = uploader._apply_revision_instruction(
        original,
        "标题",
        "重写开头",
        "deep-technical",
        rewrite_rate=75,
    )

    assert revised is not None
    assert "<think>" not in revised
    assert "I should explain" not in revised
    assert "# 新正文" in revised
    assert "![封面](/assets/images/cover.png)" in revised
    assert '<img src="/assets/a.png">' in revised


def test_llm_revision_output_rejects_model_commentary():
    cleaned = uploader._clean_llm_revision_output(
        "The user wants me to delete duplicate paragraphs before writing the article."
    )

    assert cleaned == ""
