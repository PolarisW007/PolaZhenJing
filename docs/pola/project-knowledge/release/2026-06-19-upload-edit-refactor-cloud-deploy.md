# 发布记录：上传与编辑模块重构云端同步

日期：2026-06-19

## 发布目标

- 将上传页和文章编辑页的 canonical Markdown 管线、富文本/Markdown 双向转换、保存等价预览、AI 改写率和 Playwright Harness 同步到云服务器。
- 修复 TinyMCE 尚未初始化完成时切回 Markdown 可能读空内容的问题。
- 保持文章内容、运行时数据库、密钥和服务器 `.env` 不被覆盖。

## 发布范围

- 后端：`app/uploader.py`、`app/article_content.py`、`app/article_repository.py`、`app/article_ai.py`、`app/__init__.py`。
- 模板：`app/templates/article_edit.html`、`app/templates/upload.html`、以及当前服务已依赖的文章阅读/分享相关模板。
- Harness：`scripts/upload_edit_playwright_harness.py`、`scripts/wechat_share_harness.py`、`scripts/seo_geo_harness.py`。
- 测试：文章编辑、上传改写率、分享发布、公开文章页等相关测试。
- 文档：`docs/pola/project-knowledge/` 中本次及此前未归档的需求、PRD、SDD、测试和开发日志。

## 不发布范围

- 不覆盖 `_posts/` 文章内容。
- 不覆盖 `data/`、`.env`、运行时数据库、临时文件和缓存。
- 不覆盖服务器运行时生成的分享图、富文本图和上传图。
- 不调整 nginx、systemd、云资源和密钥。

## 发布前本机验证

```bash
.venv/bin/python -m py_compile app/uploader.py app/article_content.py app/article_repository.py app/article_ai.py scripts/upload_edit_playwright_harness.py
.venv/bin/python -m pytest tests/test_article_content.py tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py -q
.venv/bin/python -m pytest tests -q
.venv/bin/python scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019
git diff --check
```

结果：

- py_compile：Pass。
- 相关 pytest：53 passed。
- 全量 pytest：74 passed。
- Playwright 本机 Harness：Pass。
- `git diff --check`：Pass。

## 云端发布计划

1. 本地创建 git commit 并 push 到 `origin/main`。
2. SSH 到 `root@42.121.164.11`，在 `/PolaZhenjing` 备份本次覆盖文件。
3. 精确 rsync 本次代码、模板、测试、脚本和文档到 `/PolaZhenjing`，排除 `_posts`、`data`、`.env`、`tmp`。
4. 云端运行 py_compile 和相关 pytest。
5. 重启 `polazj.service`。
6. 公网 smoke 验证：
   - `https://aipd.me/PolaZhenjing/admin/login`
   - `https://aipd.me/PolaZhenjing/admin/upload`
   - `https://aipd.me/PolaZhenjing/articles/2026-04-11-test-article.md`

## 回滚方案

```bash
ssh root@42.121.164.11
cd /PolaZhenjing
BACKUP_DIR=/opt/backups/polazj-upload-edit-refactor-<timestamp>
tar -xzf "$BACKUP_DIR/app.tgz" -C /PolaZhenjing
tar -xzf "$BACKUP_DIR/scripts-tests-docs-portal.tgz" -C /PolaZhenjing
tar -xzf "$BACKUP_DIR/var-www-portal.tgz" -C /var/www/html
systemctl restart polazj.service
systemctl is-active polazj.service
```

## 执行记录

- 本地 commit：`9bff536 feat(editor): refactor upload edit article workflows`，已 push 到 `origin/main`。
- 备份目录：`/opt/backups/polazj-upload-edit-refactor-20260619161952`。
- 云端同步：
  - `/PolaZhenjing/app/`
  - `/PolaZhenjing/scripts/`
  - `/PolaZhenjing/tests/`
  - `/PolaZhenjing/docs/pola/project-knowledge/`
  - `/PolaZhenjing/portal/`
  - `/var/www/html/`
- 云端 py_compile：Pass。
- 云端 pytest：`53 passed in 2.37s`。
- 服务状态：`polazj.service` 已重启，`systemctl is-active polazj` 返回 `active`。
- 认证态模板 smoke：
  - `/admin/upload`：200，命中 `AI 改写率`、`rich-content`、`convertEditorContent`、`content_format`。
  - `/admin/articles/rolling-ai-fde-ai-20260607.md/edit`：200，命中 `AI 改写率`、`rich-content`、`convertEditorContent`、`修改建议简述`、`渲染预览`。
  - `/admin/api/editor/convert`：Markdown -> 富文本 200，富文本 -> Markdown 200。
- 公网 smoke：
  - `https://aipd.me/`：200。
  - `https://aipd.me/PolaZhenjing/admin/login`：200。
  - `https://aipd.me/PolaZhenjing/admin/upload`：302 到登录页，符合未登录保护预期。
  - `https://aipd.me/PolaZhenjing/articles/fde-databricks-snowflake-20260610.md`：200。
  - `https://aipd.me/PolaZhenjing/admin/articles/rolling-ai-fde-ai-20260607.md/edit`：302 到登录页，符合未登录保护预期。

## 风险

- `app/uploader.py` 承载多条历史功能链路，本次同步采用当前已通过测试的服务状态；不做单独的历史回滚切片。
- Playwright Harness 不点击真实保存按钮，避免污染文章；保存链路由 Flask test client 和单测覆盖。
- 云端如存在未提交运行时改动，精确 rsync 会覆盖发布范围内文件，因此发布前必须备份。
- 线上 `journalctl` 中仍可看到历史微信 JS-SDK `permission denied` 诊断日志，属于微信分享权限链路历史观测，不影响本次上传/编辑模块发布。
