# 发布记录：文章编辑页保存反馈修复

日期：2026-06-19

## 发布目标

将文章编辑页保存状态反馈和真实保存 Harness 覆盖同步到云服务器，修复用户看到“保存没反应”的体验问题。

## 发布范围

- `app/templates/article_edit.html`
- `scripts/upload_edit_playwright_harness.py`
- `tests/test_article_edit_rich_editor.py`
- `docs/pola/project-knowledge/requirements/2026-06-19-article-edit-save-feedback.md`
- `docs/pola/project-knowledge/specs/2026-06-19-article-edit-save-feedback-prd.md`
- `docs/pola/project-knowledge/architecture/2026-06-19-article-edit-save-feedback-sdd.md`
- `docs/pola/project-knowledge/devlogs/2026-06-19-article-edit-save-feedback.md`
- `docs/pola/project-knowledge/test-reports/2026-06-19-article-edit-save-feedback-test.md`

## 不发布范围

- 不覆盖 `_posts/`。
- 不覆盖 `data/`、`.env`、运行时数据库和临时文件。
- 不调整 nginx、systemd 或模型配置。

## 回滚

```bash
ssh pola-server
cd /PolaZhenjing
BACKUP_DIR=/opt/backups/polazj-edit-save-feedback-<timestamp>
tar -xzf "$BACKUP_DIR/app-template.tgz" -C /PolaZhenjing
tar -xzf "$BACKUP_DIR/scripts-tests-docs.tgz" -C /PolaZhenjing
systemctl restart polazj
```

## 执行记录

- 本地验证：
  - `.venv/bin/python -m py_compile app/uploader.py scripts/upload_edit_playwright_harness.py`：Pass。
  - `.venv/bin/python -m pytest tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py tests/test_article_content.py -q`：`19 passed in 0.38s`。
  - `.venv/bin/python -m pytest tests/test_article_content.py tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py tests/test_social_publish.py tests/test_public_article_homepage.py tests/test_article_auto_tagging.py tests/test_article_reader_roles.py tests/test_article_reader_sidebar_like.py -q`：`53 passed in 0.93s`。
  - `.venv/bin/python scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019`：Pass，真实点击保存并验证临时文章写回。
  - `git diff --check`：Pass。
- 本地 commit：`85c7154 fix(editor): show save progress and cover submit path`，已 push 到 `origin/main`。
- 备份目录：`/opt/backups/polazj-edit-save-feedback-20260619170335`。
- 云端同步：
  - `/PolaZhenjing/app/templates/article_edit.html`
  - `/PolaZhenjing/scripts/upload_edit_playwright_harness.py`
  - `/PolaZhenjing/tests/test_article_edit_rich_editor.py`
  - `/PolaZhenjing/docs/pola/project-knowledge/`
- 云端验证：
  - `.venv/bin/python3 -m py_compile app/uploader.py scripts/upload_edit_playwright_harness.py`：Pass。
  - `PYTHONPATH=. .venv/bin/pytest tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py tests/test_article_content.py -q`：`19 passed in 0.98s`。
  - `systemctl is-active polazj`：`active`。
  - 认证态模板 smoke：`/admin/articles/rolling-ai-fde-ai-20260607.md/edit` 返回 200，并命中 `save-status`、`event.submitter`、`articleEditSubmitting`、AI 保存状态文案和隐藏 `save_mode`。
  - 转换 API smoke：Markdown -> 富文本返回 200，`ok=True`。
- 公网 smoke：
  - `https://aipd.me/PolaZhenjing/admin/login`：200。
  - `https://aipd.me/PolaZhenjing/admin/articles/rolling-ai-fde-ai-20260607.md/edit`：未登录 302 到登录页，符合预期。
  - `https://aipd.me/PolaZhenjing/articles/rolling-ai-fde-ai-20260607.md`：200。
