# 开发日志：文章编辑页支持富文本编辑

日期：2026-06-08

## 目标

把 `app/templates/article_edit.html` 从 EasyMDE 升级为 TinyMCE,与 `app/templates/upload.html` 使用同一套本地 TinyMCE vendor,提供「富文本 / Markdown 源码」双模式。

## 改动记录

- `app/templates/article_edit.html`
  - 移除 `cdn.jsdelivr.net/npm/easymde` 的 CSS 引用和 EasyMDE 初始化。
  - 改用上传页同款的本地 TinyMCE 6.8.5 资源:`tinymce.min.js` 走 `/assets/vendor/tinymce`,主脚本 URL 带 `?v=6.8.5-pzj-20260602` 版本参数。
  - 新增 `editor_mode` 单选(rich / markdown)、隐藏字段 `content_format`、富文本 textarea `#rich-content` 和 Markdown 源码 textarea `#content`。
  - TinyMCE 初始化配置、`paste_preprocess`、`images_upload_handler`、剪贴板图片上传 fallback 与上传页保持一致。
  - 保留「修改建议简述」与「保存 / 保存并同步 GitHub」按钮,提交时由前端把当前模式的内容写入隐藏 `body` 字段,后端继续读 `form.get('body')`。
  - 渲染预览面板改为单列、富文本下显示在编辑器下方;Markdown 下走 `python-markdown` 渲染。
- `app/uploader.py`
  - `preview_article_markdown` 新增 `content_format` 入参:`rich_html` 直出,`markdown` 走原有 `python-markdown` 流程,默认仍是 `markdown`。
  - 返回体补充 `format` 字段方便前端调试。
- `tests/test_article_edit_rich_editor.py`(新增)
  - 编辑页 HTML 不再引用 `cdn.jsdelivr.net/npm/easymde`。
  - 编辑页 HTML 包含本地 TinyMCE 主脚本 URL + `cache_suffix`,以及 `editor_mode` 切换相关 DOM。
  - 预览接口在 `content_format=rich_html` 时原样返回 HTML,在 `content_format=markdown` 时渲染 Markdown,缺省时回落到 Markdown。

## 验证记录

- `python3 -m py_compile app/uploader.py app/__init__.py app/auth.py app/jobs.py app/skillhub.py app/agent.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_article_edit_rich_editor.py -q`：4 passed。
- `PYTHONPATH=. .venv/bin/pytest tests -q`：34 passed(原有 30 + 新增 4)。
- `git diff --check`：通过(待提交阶段执行)。

## 风险

- R1 编辑页 body 现在可能保存为 HTML 段,切换 Markdown -> 富文本不会自动把 Markdown 转 HTML,首次切换会按当前源码原样写回。
- R2 TinyMCE 插件列表与 `assets/vendor/tinymce/plugins/` 必须保持同步,后续若在编辑页新增插件,需要同步补充 vendor。
- R3 预览接口对 `rich_html` 不做清洗,直接透传 TinyMCE 产出的 HTML;后续若发现恶意粘贴可补一个 HTML 清洗函数。
- R4 文章编辑页和上传页现在共用 TinyMCE 加载、皮肤、语言包、图片上传接口,后续调整 TinyMCE 配置时需要同步两个页面。

## Commit 状态

待提交:文章编辑页 TinyMCE 富文本编辑器接入、预览接口 content_format 分流、测试与交付文档。
