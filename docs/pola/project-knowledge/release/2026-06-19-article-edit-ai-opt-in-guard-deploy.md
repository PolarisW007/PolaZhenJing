# 发布记录：文章编辑 AI 修改显式开关

## 发布目标

将文章编辑 AI 修改从默认隐式触发改为显式启用，阻止模型思考内容和图片遗漏写入线上文章。

## 发布文件

- `app/uploader.py`
- `app/templates/article_edit.html`
- `tests/test_article_edit_rich_editor.py`
- `scripts/upload_edit_playwright_harness.py`
- `docs/pola/project-knowledge/...`

## 发布前检查

- 代码语法检查：已通过。
- 编辑模块单测：已通过。
- 密钥：不新增或输出任何 secret。
- 回滚：恢复发布前代码备份；受影响文章已有服务器备份和恢复来源。

## 发布后检查计划

- 线上 `systemctl` 服务状态。
- 线上编辑页 `/PolaZhenjing/admin/articles/rolling-ai-fde-ai-20260607.md/edit` 返回 200。
- 页面 HTML 包含 `enable_ai_revision`，AI 面板默认隐藏。
- 线上文章 `rolling-ai-fde-ai-20260607.md` 不包含 `<think>`，图片/媒体引用数量保持 9。

## 发布执行记录

- 本地 commit：`76fd9d1 fix: 文章编辑 AI 修改改为显式启用`。
- 远端：`origin/main` 已推送。
- 服务器备份：`/opt/backups/polazj-edit-ai-opt-in-20260619174439`。
- 同步方式：`rsync -avR` 同步应用代码、模板、测试、文档到 `/PolaZhenjing`。
- 云端测试：
  - `.venv/bin/python3 -m py_compile app/uploader.py scripts/upload_edit_playwright_harness.py`
  - `PYTHONPATH=. .venv/bin/pytest tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py tests/test_article_content.py -q`
  - 结果：22 passed。
- 服务重启：`sudo systemctl restart polazj` 后 `systemctl is-active polazj` 为 active。
- 线上 smoke：
  - 登录态 test client 编辑页 200，包含 AI 修改开关，AI 面板默认隐藏。
  - 文章源文件 585 行、9 个媒体引用、0 个 `<think>`。
  - `https://aipd.me/PolaZhenjing/articles/rolling-ai-fde-ai-20260607.md` 返回 200，页面片段未出现 `<think>`。

## 回滚命令

```bash
cd /PolaZhenjing
tar -xzf /opt/backups/polazj-edit-ai-opt-in-20260619174439/code-before-edit-ai-opt-in.tgz
sudo systemctl restart polazj
```
