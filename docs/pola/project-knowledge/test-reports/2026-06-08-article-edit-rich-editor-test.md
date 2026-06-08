# 测试报告：文章编辑页支持富文本编辑

日期：2026-06-08

## 自动化

- `python3 -m py_compile app/uploader.py app/__init__.py app/auth.py app/jobs.py app/skillhub.py app/agent.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_article_edit_rich_editor.py -q`：4 passed。
- `PYTHONPATH=. .venv/bin/pytest tests -q`：34 passed。

## 新增单测

`tests/test_article_edit_rich_editor.py`

- `test_article_edit_page_uses_local_tinymce_assets`
  - 断言编辑页 HTML 不再引用 `cdn.jsdelivr.net/npm/easymde`。
  - 断言主脚本 URL 带 `?v=6.8.5-pzj-20260602`、`cache_suffix: TINYMCE_CACHE_SUFFIX`。
  - 断言 `editor_mode` 单选、`#rich-content`、`#content`、`#content-format` 都在 DOM 中。
  - 断言 `display: flex !important` 等防止 iframe 塌陷的 CSS 已就位。
- `test_preview_endpoint_returns_html_for_rich_format`
  - 提交 `content_format=rich_html`,断言返回原 HTML,且 `format` 字段为 `rich_html`。
- `test_preview_endpoint_renders_markdown_for_markdown_format`
  - 提交 `content_format=markdown`,断言返回体含 `<h1` 与 `<strong>加粗</strong>`。
- `test_preview_endpoint_defaults_to_markdown_when_format_missing`
  - 缺省 `content_format` 时回落到 Markdown 渲染,返回体含 `<h2`。

## 浏览器 smoke(本地)

待部署到云端后,使用临时 admin session 打开 `/PolaZhenjing/admin/articles/2026-04-11-test-article.md/edit`,确认:

- 编辑页有 TinyMCE 工具栏,主脚本来自本地 vendor,无 jsDelivr / unpkg 请求。
- 默认进入 Markdown 源码模式(因 body 是 Markdown)。
- 切换到「富文本编辑」后,TinyMCE 编辑器出现,工具栏中文,粘贴一段富文本能正常显示图片与样式。
- 「渲染预览」面板随模式变化实时刷新,富文本下显示 HTML,Markdown 下显示渲染结果。
- TinyMCE 加载失败时,显示红色提示并自动切回 Markdown 源码 textarea,内容保留。
- 点击「保存」,后端把 `body` 写回 `_posts/2026-04-11-test-article.md`,文件可被 Jekyll 渲染。
