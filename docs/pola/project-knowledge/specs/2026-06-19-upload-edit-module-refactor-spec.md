# SPEC：上传与编辑模块重构执行规格

日期：2026-06-19

## 1. Canonical Markdown 规则

- `_posts/*.md` 的正文永远保存为 canonical Markdown。
- HTML 输入只存在于富文本编辑器和转换 API 中。
- AI 改写、修改建议、图片插入、同步发布都以 canonical Markdown 为输入。
- front matter 与正文分离处理，AI 不接触 front matter。

## 2. 后端函数规格

### `article_content.normalize_markdown(markdown: str) -> str`

- 标准化换行。
- 修复常见 HTML entity：`&mdash;` 等。
- 保留 Markdown 图片、链接、表格。
- 不删除用户正文段落。

### `article_content.markdown_to_editor_html(markdown: str) -> str`

- 供富文本编辑器使用。
- Markdown 图片渲染成 `<img>`。
- 段落、标题、列表、引用保持可编辑结构。

### `article_content.html_to_canonical_markdown(html: str) -> str`

- 富文本 HTML 转 Markdown。
- 保留 `img[src]`、`a[href]`、表格、blockquote、列表。
- 清理危险标签和事件属性。
- 输出可读 Markdown，不输出一整坨单行文本。

### `article_content.render_article_preview(content: str, content_format: str) -> PreviewResult`

- 如果 `content_format=rich_html`，先转 Markdown，再走 Markdown render。
- 如果 `content_format=markdown`，先 normalize，再 render。
- 返回 `html`、`canonical_markdown`、`warnings`。

### `article_ai.apply_revision(markdown, title, instruction, rewrite_rate)`

- `instruction` 空：直接返回原 Markdown，不调用 LLM。
- `rewrite_rate=0`：直接返回原 Markdown。
- 其它档位：调用现有 LLM provider，失败时返回原 Markdown + warning。
- prompt 明确“不修改 front matter，不重复结尾，不删除图片语法”。

## 3. 前端规格

共享编辑器状态：

```js
{
  mode: "markdown" | "rich_html",
  dirty: boolean,
  converting: boolean,
  previewing: boolean,
  lastCanonicalMarkdown: string,
  warnings: []
}
```

切换模式：

- 当前内容读取：
  - rich：`tinymce.get(id).getContent()`
  - markdown：`textarea.value`
- 调 `/api/editor/convert`。
- 成功后写入目标编辑器。
- 失败后不切换模式，只显示错误。

提交：

- 提交前把当前模式正文写入隐藏 `body`。
- 写入 `content_format`。
- 编辑页提交时携带 `rewrite_rate` 和 `revision_instruction`。

## 4. 路由接入规格

### 上传页

- 保留 `GET/POST /upload`。
- 表单 body 由共享编辑器同步。
- POST 后保存 draft 时记录：
  - `content`
  - `content_format`
  - `canonical_markdown`
  - `rewrite_rate`
  - `revision_instruction`
- 旧 draft 无字段时使用兼容默认值。

### 编辑页

- GET：
  - 读取文章 Markdown。
  - 默认 `content_format=markdown`。
  - 同时准备富文本转换所需 API URL。
- POST：
  - 读取 `content_format` 和 `body`。
  - 转 canonical Markdown。
  - 如有 `revision_instruction` 且 `rewrite_rate>0`，调用 AI 修订。
  - 写回 `_posts`。
  - 返回文章详情页。

## 5. Harness 规格

### 自动化测试

- `tests/test_article_content.py`
- `tests/test_article_edit_workflow.py`
- `tests/test_upload_workflow.py`
- 保留并更新：
  - `tests/test_article_edit_rich_editor.py`
  - `tests/test_upload_rewrite_rate.py`
  - `tests/test_social_publish.py`

### 浏览器验证

本地：

1. 启动 Flask 测试服务。
2. 运行 `scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019`。
3. Harness 临时创建本地管理员账号，通过真实登录页进入后台，结束后删除账号。
4. 验证 `/admin/upload` 粘贴 tab：Markdown 输入、富文本切换、TinyMCE 加载、标题和图片渲染。
5. 验证 `/admin/articles/2026-04-11-test-article.md/edit`：默认 Markdown、保存等价预览、富文本切换、切回 Markdown、修改建议字段可输入。
6. 检查业务 console error、request failed、HTTP 4xx/5xx；仅忽略浏览器默认 `/favicon.ico` 探测。

线上：

- 部署后访问 aipd.me 同一路径。
- 检查 console error、network 失败、编辑器可输入、预览可渲染。

## 6. 不影响功能使用验证路径

- 旧上传入口仍存在。
- 旧编辑 URL 仍存在。
- 旧文章详情 URL 仍存在。
- `_posts` 旧文章不需要迁移即可打开。
- 分享卡片、短链、多平台同步发布仍读取同一 Markdown。
- 普通用户公开阅读不需要登录后台。
