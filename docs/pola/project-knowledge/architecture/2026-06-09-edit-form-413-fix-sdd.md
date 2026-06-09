# SDD:文章编辑页大 body 413 修复

日期:2026-06-09

## 架构影响

本次不改变 Flask blueprint、SQLite jobs 表或模板路由结构,只在现有模块内放宽 / 收敛 form 提交流量:

- `app/__init__.py`
  - 新增 `app.config['MAX_FORM_MEMORY_SIZE'] = 16 * 1024 * 1024`,把 Werkzeug 3.x 默认 500KB 提到 16MB,和 `MAX_CONTENT_LENGTH` 对齐。
- `app/templates/article_edit.html`
  - 提交事件处理中,在 `tinymce.triggerSave()` 之后、设置隐藏 `body` 字段前后,加 `if (markdown) markdown.disabled = true;` 和 `if (rich) rich.disabled = true;`。
  - 目的:避免同篇正文在 form 里出现 3 份(`body` + `content` + `rich_content`),降低 Werkzeug form 解析压力。

## 配置

- `MAX_FORM_MEMORY_SIZE` = `16 * 1024 * 1024` (16MB),在 `app/__init__.py` 创建 Flask 实例后立即设置。
- 与 `MAX_CONTENT_LENGTH` 同样为 16MB,但前者是 Werkzeug form parser 阈值(超限 raise 413),后者是 Werkzeug `max_content_length` 阈值(超限 raise 413);本轮先把 `max_form_memory_size` 抬上来,`max_content_length` 早就是 16MB,不动。
- 无新增环境变量、无 `.env` 改动。

## 数据流(编辑页保存)

```text
[浏览器]                                                [Flask + Werkzeug 3.1.8]
┌──────────────────────────────────┐                    ┌─────────────────────────────┐
│ 1. 用户点保存                        │                    │                             │
│ 2. submit 事件:                     │                    │                             │
│    - tinymce.triggerSave()         │                    │                             │
│    - markdown.disabled = true  ←─┐  │                    │                             │
│    - rich.disabled   = true    │  │  POST /admin/articles/.../edit      │
│    - 写 bodyField(hide)         │  │ ───────────────────────────────→   │
│ 3. form 提交                      │  │  Content-Type: application/        │
│    body=<mode content>           │  │  x-www-form-urlencoded            │
│    (其它小字段: title, date, ...) │  │                                    │
│                                  │  │  ↓ Werkzeug 解析                    │
│                                  │  │  max_form_memory_size = 16MB      │
│                                  │  │  body ~ 23KB markdown (TinyMCE    │
│                                  │  │  富文本模式约 500KB-1MB HTML)     │
│                                  │  │                                    │
│                                  │  │  ↓ Flask 路由                       │
│                                  │  │  edit_article()                    │
│                                  │  │    form.get('body')               │
│                                  │  │    写回 _posts/<file>.md         │
│                                  │  │  ↓                                 │
│                                  │  ← 302 /admin/articles/...          │
└──────────────────────────────────┘                    └─────────────────────────────┘
```

## 接口契约

- 入参:不变。`POST /admin/articles/<filename>/edit` 仍以 `form['body']` 为权威字段(由 JS 在 submit 时设置),`form['content']` / `form['rich_content']` / `form['content_format']` / `form['editor_mode']` 是编辑页内部使用,后端不读。
- 出参:不变。302 跳详情页,或回填 flash 错误。
- 路由函数 `edit_article()`:零改动。
- 路由函数 `preview_article_markdown()`:零改动(由 2026-06-08 段 1 引入 `content_format` 支持)。
- 错误处理:413 仍然可能由以下三层抛出,本轮让 Werkzeug 层(500KB)不再误伤:
  - nginx `client_max_body_size 16m`(已设)
  - Flask `MAX_CONTENT_LENGTH 16MB`(已设)
  - Werkzeug `MAX_FORM_MEMORY_SIZE 16MB`(本次从默认 500KB 提到 16MB)

## 不影响功能策略

- 仅放宽 Werkzeug 单 form 字段阈值,后端路由、Jinja 模板、SQLite 表、`.env` 全部不动。
- 仅在 `submit` 事件中临时 disable 2 个 textarea,JS 执行完成后 `body` 字段已是 canonical 内容,即便其他两份 textarea 重新 enabled 也不会影响后端读取(后端只读 `body`)。
- 不动 nginx、不动 gunicorn、不动 systemd unit。
- `_posts/*.md` 文件和云端 20 个独有 `Add article: ...` commit 不动。

## 验证

- `py_compile` 覆盖 `app/__init__.py`、`app/templates/article_edit.html` 关联模块。
- pytest 覆盖新 `tests/test_article_edit_413_fix.py`(500KB / 1MB / 8MB 都不再 413)和原 `tests/test_article_edit_rich_editor.py`(4 个用例无回归)。
- `git diff --check` 确认 diff 卫生。
- 云端端到端:走 `https://aipd.me/...` + 真 gunicorn 进程,8KB / 100KB / 500KB / 1MB body 全部 302。
