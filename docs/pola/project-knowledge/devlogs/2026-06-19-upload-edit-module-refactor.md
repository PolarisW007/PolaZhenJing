# 开发日志：上传与编辑模块系统性重构

日期：2026-06-19

## 目标

整体重构 `/PolaZhenjing/admin/upload` 和 `/PolaZhenjing/admin/articles/<filename>/edit`，解决富文本/Markdown 切换、预览、保存、AI 修改建议和改写率链路的小问题堆积。

## 当前阶段

- 已确认四个关键决策。
- 已阅读历史文档：
  - 2026-06-02 上传编辑器稳定性。
  - 2026-06-08 编辑页富文本接入。
  - 2026-06-09 413 修复。
  - 2026-06-14 图片本地化。
  - 2026-06-17 上传 AI 改写率。
- 已新增本次 requirement、PRD、SDD、SPEC 和 Harness 计划。

## 初始风险

- 当前工作区已有大量历史未提交文件，本次需要避免提交无关改动。
- `app/uploader.py` 职责过多，抽服务时必须分阶段保留路由兼容。
- AI 和图片链路依赖外部 provider，自动化测试需 monkeypatch。

## 验证计划

见 `docs/pola/project-knowledge/test-reports/2026-06-19-upload-edit-module-refactor-harness.md`。

## 后续记录

编码、测试、回归和部署结果将在本文件继续追加。

## 实现记录

### 新增模块

- `app/article_content.py`
  - 统一 Markdown/HTML 转换。
  - 建立 canonical Markdown 管线。
  - 新增保存等价预览。
  - 不再使用旧 `_clean_markdown_formatting` 剥离用户加粗格式。
- `app/article_repository.py`
  - 抽出 `_posts` 安全路径、front matter 解析、文章加载和原子写入。
- `app/article_ai.py`
  - 抽出 AI 改写率 preset、prompt 合同和 temperature 策略。

### 改动模块

- `app/uploader.py`
  - 保留旧 wrapper，内部改用新服务。
  - 编辑保存顺序改为：当前模式内容 -> canonical Markdown -> 可选 AI 修订 -> 写回。
  - `preview_article_markdown` 改为保存等价预览，不再 rich HTML 原样返回。
  - 新增 `/admin/api/editor/convert` 和 `/admin/api/editor/preview`。
  - 编辑页保存改用 `article_repository.write_post()` 原子写入。
- `app/templates/article_edit.html`
  - 默认 Markdown 模式。
  - 新增编辑页 AI 改写率五档。
  - 模式切换通过后端转换 API，不再硬拷贝字符串。
  - 修复 TinyMCE 尚未初始化完成时切回 Markdown 读取空内容的问题，优先使用已转换的 textarea HTML 兜底。
- `app/templates/upload.html`
  - 粘贴内容 tab 的模式切换接入同一个转换 API。
  - 同步修复 TinyMCE 未就绪时 rich -> Markdown 的空内容回退问题。
- `scripts/upload_edit_playwright_harness.py`
  - 新增本机 Playwright Harness，使用系统 Chrome 测上传/编辑真实页面交互。
  - 测试时临时创建本地管理员账号，真实登录，结束后自动删除。
- `tests/test_article_content.py`
  - 新增正文转换和预览测试。
- `tests/test_article_edit_rich_editor.py`
  - 更新预览语义断言。
  - 新增转换 API 和 AI 修订 canonical Markdown 输入测试。

## 验证记录

- `.venv/bin/python -m py_compile app/uploader.py app/article_content.py app/article_repository.py app/article_ai.py app/__init__.py`：Pass。
- `.venv/bin/python -m pytest tests/test_article_content.py tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py -q`：Pass，19 passed。
- `.venv/bin/python -m pytest tests/test_social_publish.py tests/test_public_article_homepage.py tests/test_article_auto_tagging.py tests/test_article_reader_roles.py -q`：Pass，32 passed。
- `.venv/bin/python -m pytest tests/test_article_edit_413_fix.py tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py -q`：Pass，19 passed。
- `git diff --check`：Pass。
- Flask test client 页面级 Harness：Pass。
- `.venv/bin/python -m pip install playwright`：Pass，本机补齐 Playwright 测试依赖。
- `SECRET_KEY=dev-secret-change-me FLASK_APP='app:create_app' .venv/bin/flask run --host 127.0.0.1 --port 5019`：Pass，本地服务启动成功。
- `.venv/bin/python scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019`：Pass。
  - 覆盖上传页 Markdown -> 富文本、编辑页 Markdown -> 富文本 -> Markdown、保存等价预览、修改建议字段输入。
  - 截图输出：
    - `/Users/wangchang/Desktop/WSYCursorCode/PolaZhenJing/tmp/harness/upload-edit/1781853029-upload-rich-switch.png`
    - `/Users/wangchang/Desktop/WSYCursorCode/PolaZhenJing/tmp/harness/upload-edit/1781853031-edit-markdown-rich-preview.png`

## 残余风险

- 真实 MiniMax 调用未执行，避免外部 API 成本；已用 monkeypatch 覆盖参数和链路。
- Playwright Harness 未点击真实保存按钮，避免污染本地 `_posts`；保存链路由 test client 和单测覆盖。
- 当前工作区存在大量历史未提交文件，git 收尾时必须只纳入本次相关文件。
