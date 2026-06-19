# Harness 计划：上传与编辑模块重构

日期：2026-06-19

## 测试矩阵

| 验收项 | 类型 | 命令/方式 | 必跑 |
| --- | --- | --- | --- |
| A1 文档 | 文档检查 | 检查 requirement/PRD/SDD/SPEC/devlog | 是 |
| A3 转换 | 单测 | `pytest tests/test_article_content.py` | 是 |
| A4 预览 | 单测/API | `pytest tests/test_article_edit_workflow.py` | 是 |
| A5 保存 | 单测/API | 编辑保存 test client | 是 |
| A6 AI 修订 | 单测 | monkeypatch LLM | 是 |
| A7 改写率 | 单测 | `pytest tests/test_upload_rewrite_rate.py` | 是 |
| A8 图片 | 单测/API | 富文本图片/本地图片转换 | 是 |
| A9 兼容 | 回归 | `pytest tests/test_social_publish.py tests/test_public_article_homepage.py` | 是 |
| A10 UI | 浏览器 | upload/edit 本地和线上路径 | 是 |

## 本地命令

```bash
python3 -m py_compile app/uploader.py app/__init__.py app/article_content.py app/article_repository.py app/article_ai.py app/edit_workflow.py app/upload_workflow.py
python3 -m pytest tests/test_article_content.py tests/test_article_edit_workflow.py tests/test_upload_workflow.py tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py tests/test_social_publish.py
python3 scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019
git diff --check
```

## 浏览器 Harness

- `/PolaZhenjing/admin/upload`
  - 富文本输入。
  - Markdown 输入。
  - 模式切换。
  - 预览。
  - 改写率选择。
- `/PolaZhenjing/admin/articles/rolling-ai-fde-ai-20260607.md/edit`
  - 默认 Markdown。
  - 切富文本。
  - 切回 Markdown。
  - 修改建议为空保存。
  - 修改建议非空保存（测试环境 monkeypatch 或 dry-run）。
  - 预览和详情页一致。

## 失败判定

- 编辑器无法输入：Fail。
- 模式切换丢正文：Fail。
- 预览显示 raw `![](...)`：Fail。
- 修改建议导致保存失败：Fail。
- 旧文章打开图片失效：Fail。
- 同步发布测试读取文章失败：Fail。

## 本地执行记录

日期：2026-06-19

### 命令验证

```bash
.venv/bin/python -m py_compile app/uploader.py app/article_content.py app/article_repository.py app/article_ai.py app/__init__.py
```

结果：Pass。

```bash
.venv/bin/python -m pytest tests/test_article_content.py tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py -q
```

结果：Pass，19 passed。

```bash
.venv/bin/python -m pytest tests/test_social_publish.py tests/test_public_article_homepage.py tests/test_article_auto_tagging.py tests/test_article_reader_roles.py -q
```

结果：Pass，32 passed。

```bash
.venv/bin/python -m pytest tests/test_article_edit_413_fix.py tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py -q
```

结果：Pass，19 passed。

```bash
git diff --check
```

结果：Pass。

### 页面级 Harness

第一轮本机未安装 Playwright，先使用 Flask test client 做页面级 Harness：

- `GET /admin/upload`：200。
- 上传页包含 `/admin/api/editor/convert`。
- 上传页仍有 15 个 `rewrite_rate` radio（3 个 tab x 5 档）。
- `GET /admin/articles/2026-04-11-test-article.md/edit`：200。
- 编辑页默认 Markdown 模式。
- 编辑页包含 5 档 `rewrite_rate`。
- `POST /admin/api/editor/convert`：Markdown -> rich HTML 成功，并渲染图片。
- `POST /admin/articles/<filename>/preview`：rich HTML 走 canonical Markdown 预览成功。

结果：Pass。

### Playwright 本机浏览器 Harness

已安装 Python Playwright 包，并使用本机系统 Chrome：

```bash
.venv/bin/python -m pip install playwright
SECRET_KEY=dev-secret-change-me FLASK_APP='app:create_app' .venv/bin/flask run --host 127.0.0.1 --port 5019
.venv/bin/python scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019
```

覆盖范围：

- 自动创建临时本地管理员账号，通过真实登录页进入后台，测试结束自动删除账号。
- `/admin/upload` 粘贴 tab：Markdown 输入 -> 富文本切换 -> TinyMCE 资源加载 -> 图片和标题渲染。
- `/admin/articles/2026-04-11-test-article.md/edit`：默认 Markdown、保存等价预览、Markdown -> 富文本 -> Markdown 双向切换、修改建议字段可输入。
- 检查业务 console error、request failed、HTTP 4xx/5xx；仅忽略浏览器默认 `/favicon.ico` 探测。

结果：Pass。

截图：

- `/Users/wangchang/Desktop/WSYCursorCode/PolaZhenJing/tmp/harness/upload-edit/1781853029-upload-rich-switch.png`
- `/Users/wangchang/Desktop/WSYCursorCode/PolaZhenJing/tmp/harness/upload-edit/1781853031-edit-markdown-rich-preview.png`

## 未覆盖和后续

- 未调用真实 MiniMax：测试使用 monkeypatch 和 prompt/参数断言，避免消耗外部 API 和污染生产内容。
- Playwright Harness 没有点击真实保存按钮，避免污染本地文章内容；保存链路由 Flask test client 和单测覆盖。
