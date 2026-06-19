# Devlog: 上传文章 AI 改写率控制

日期: 2026-06-17

## 目标

为 `/PolaZhenjing/admin/upload` 增加 AI 改写率多档选择。0% 完全不改写正文，只继续图片生成/插入；100% 保持完整风格改写；中间档按不同强度润色和重构。

## A2A 阶段

- pola-a2a-usage: 已读取，使用 `pola-agent-delivery-framework` 闭环。
- project-context: 已确认 Flask/Jinja 上传页、draft、jobs 后台任务、MiniMax 文本/图片生成链路。
- requirement: `docs/pola/project-knowledge/requirements/2026-06-17-upload-ai-rewrite-rate.md`
- PRD/SPEC: `docs/pola/project-knowledge/specs/2026-06-17-upload-ai-rewrite-rate-prd.md`
- SDD: `docs/pola/project-knowledge/architecture/2026-06-17-upload-ai-rewrite-rate-sdd.md`

## 计划改动

- `app/templates/upload.html`: 三个上传入口增加 `rewrite_rate` 五档控件。
- `app/uploader.py`: 保存 draft、生成 payload、后台 job、LLM prompt 支持改写率。
- `tests/`: 增加/更新单测覆盖 UI、draft、0%、中间档、prompt。

## 验证记录

- 本地单测: `.venv/bin/python -m pytest tests/test_upload_rewrite_rate.py tests/test_social_publish.py::test_upload_page_uses_local_tinymce_assets tests/test_article_auto_tagging.py::test_upload_generates_tags_when_user_leaves_tags_blank -q`，8 passed。
- 本地关联回归: `.venv/bin/python -m pytest tests/test_upload_rewrite_rate.py tests/test_social_publish.py tests/test_article_auto_tagging.py tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py -q`，41 passed。
- 本地语法检查: `.venv/bin/python -m py_compile app/uploader.py app/__init__.py app/jobs.py`，通过。
- 本地浏览器 harness: `http://127.0.0.1:5033/admin/upload`，确认 3 个上传表单共 15 个 `rewrite_rate` 输入，默认 100%，上传文件入口可切换为 0%。
- 云端备份: `/opt/backups/polazj-upload-rewrite-rate-20260618-000159/files.tgz`。
- 云端验证: `PYTHONPATH=. .venv/bin/python -m pytest tests/test_upload_rewrite_rate.py tests/test_social_publish.py::test_upload_page_uses_local_tinymce_assets tests/test_article_auto_tagging.py::test_upload_generates_tags_when_user_leaves_tags_blank -q`，8 passed；`py_compile` 通过；`polazj.service` restart 后 `active`。
- 线上浏览器 harness: `https://aipd.me/PolaZhenjing/admin/upload?v=rewrite-rate-20260617`，确认 0/25/50/75/100 五档、默认 100%、上传文件入口可切换 0%、requestFailures/consoleErrors 均为空。

## 风险

- AI 中间档强度无法用代码完全保证，只能通过 prompt 约束和任务消息透明化。
- 生产上传主流程改动，发布前必须云端测试和线上 harness。

## 状态

- 已部署到云服务器并通过端到端 harness。
