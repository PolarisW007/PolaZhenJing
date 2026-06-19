from app.article_content import (
    canonicalize_editor_content,
    markdown_to_editor_html,
    render_article_preview,
)


def test_markdown_to_editor_html_renders_images_and_headings():
    html = markdown_to_editor_html("# 标题\n\n![图](/assets/a.png)\n\n正文")

    assert "<h1" in html
    assert '<img' in html
    assert "/assets/a.png" in html
    assert "![" not in html


def test_rich_html_to_canonical_markdown_keeps_semantic_content():
    markdown = canonicalize_editor_content(
        '<article data-x="1"><p style="color:red">第一段</p>'
        '<p><img src="/assets/a.png" class="x"></p>'
        '<script>alert(1)</script></article>',
        "rich_html",
    )

    assert "第一段" in markdown
    assert "![|](/assets/a.png)" in markdown or "![](/assets/a.png)" in markdown
    assert "script" not in markdown.lower()
    assert "style=" not in markdown
    assert "data-x" not in markdown


def test_preview_uses_canonical_markdown_pipeline_for_rich_html():
    result = render_article_preview(
        '<h1>标题</h1><p><strong>加粗</strong></p><p><img src="/assets/a.png"></p>',
        "rich_html",
    )

    assert result.canonical_markdown
    assert "# 标题" in result.canonical_markdown
    assert "<strong>加粗</strong>" in result.html
    assert '<img' in result.html
