from app.article_content import (
    canonicalize_editor_content,
    markdown_to_editor_html,
    normalize_markdown,
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


def test_rich_html_drops_unpersistable_images_instead_of_bad_markdown():
    markdown = canonicalize_editor_content(
        '<p>正文前</p>'
        '<p><img alt="缺 src 的图"></p>'
        '<p><img alt="空 src 的图" src=""></p>'
        '<p><img alt="blob 图" src="blob:https://aipd.me/demo"></p>'
        '<p>正文后</p>',
        "rich_html",
    )

    assert "正文前" in markdown
    assert "正文后" in markdown
    assert "![缺 src 的图]" not in markdown
    assert "![空 src 的图]" not in markdown
    assert "blob:https://aipd.me/demo" not in markdown
    assert "![]()" not in markdown


def test_normalize_markdown_drops_bare_image_placeholders_only():
    markdown = normalize_markdown(
        "正文前\n\n![坏图占位]\n\n![空图]()\n\n![好图](/assets/a.png)\n\n正文后"
    )

    assert "正文前" in markdown
    assert "正文后" in markdown
    assert "![坏图占位]" not in markdown
    assert "![空图]()" not in markdown
    assert "![好图](/assets/a.png)" in markdown


def test_preview_uses_canonical_markdown_pipeline_for_rich_html():
    result = render_article_preview(
        '<h1>标题</h1><p><strong>加粗</strong></p><p><img src="/assets/a.png"></p>',
        "rich_html",
    )

    assert result.canonical_markdown
    assert "# 标题" in result.canonical_markdown
    assert "<strong>加粗</strong>" in result.html
    assert '<img' in result.html
