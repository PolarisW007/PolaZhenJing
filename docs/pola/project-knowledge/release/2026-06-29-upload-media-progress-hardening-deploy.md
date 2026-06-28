# Release Manifest: 2026-06-29 上传媒体与图片展示修复

## 变更摘要

- 修复富文本中缺失 `src`、空 `src`、`blob:` 图片保存后变成坏 Markdown 图片标记的问题。
- 修复富文本图片上传返回路径缺少 `/PolaZhenjing` 前缀导致线上不可稳定展示的问题。
- 上传页文件/PDF 上传增加进度条和处理中反馈。
- 粘贴富文本提交前等待 TinyMCE 图片上传完成,避免未持久化图片进入文章生成流程。
- 文章详情页和分享卡片渲染前清理历史裸图片占位,避免 `![alt]` 直接显示成正文。

## 待发布文件

- `app/article_content.py`
- `app/uploader.py`
- `app/templates/upload.html`
- `tests/test_article_content.py`
- `tests/test_upload_rewrite_rate.py`
- `docs/pola/project-knowledge/requirements/2026-06-28-upload-media-progress-hardening.md`
- `docs/pola/project-knowledge/specs/2026-06-28-upload-media-progress-hardening-prd.md`
- `docs/pola/project-knowledge/architecture/2026-06-28-upload-media-progress-hardening-sdd.md`
- `docs/pola/project-knowledge/delivery/upload-media-progress-hardening/function_test_cases.json`
- `docs/pola/project-knowledge/devlogs/2026-06-28-upload-media-progress-hardening.md`

## 部署面

- Flask 后台应用代码。
- 上传页 Jinja 模板。
- 不涉及数据库 schema、环境变量、secret、队列或后台任务变更。

## 发布前验证

- `.venv/bin/python -m py_compile app/article_content.py app/uploader.py app/__init__.py`
- `PYTHONPATH=. .venv/bin/pytest tests/test_article_content.py tests/test_upload_rewrite_rate.py tests/test_article_edit_rich_editor.py tests/test_social_publish.py::test_public_article_short_link_renders_share_card_metadata -q`
- `.venv/bin/python /Users/wangchang/.agents/skills/pola-test-gate/scripts/validate_function_test_cases.py --prd docs/pola/project-knowledge/requirements/2026-06-28-upload-media-progress-hardening.md --prd docs/pola/project-knowledge/specs/2026-06-28-upload-media-progress-hardening-prd.md --sdd docs/pola/project-knowledge/architecture/2026-06-28-upload-media-progress-hardening-sdd.md --cases docs/pola/project-knowledge/delivery/upload-media-progress-hardening/function_test_cases.json`
- `git diff --check`

## 发布步骤

| 步骤 | 命令/动作 | 风险 | 是否需确认 |
| --- | --- | --- | --- |
| 1 | 备份云服务器目标文件 | 低,只读复制 | 否 |
| 2 | 同步待发布文件到 `/PolaZhenjing` | 中,影响上传/文章渲染 | 用户已要求执行 |
| 3 | 重启 `polazj.service` | 中,短暂影响后台请求 | 用户已要求执行 |
| 4 | 线上健康检查和页面探针 | 低,只读 | 否 |

## 发布后验证

- `systemctl is-active polazj.service`
- `curl -I https://aipd.me/PolaZhenjing/admin/upload`
- `curl -I https://aipd.me/PolaZhenjing/admin/articles/claude-code-cli-60-20260628.md`
- 抽查上传页 HTML 是否包含 `file-upload-progress`、`flushRichEditorImages`。

## 回滚方案

- 使用发布前备份恢复 `app/article_content.py`、`app/uploader.py`、`app/templates/upload.html`。
- 重启 `polazj.service`。
- 回滚后重新执行健康检查和上传页探针。

## 观察项

- 上传页是否能正常进入风格选择。
- 富文本图片上传接口是否返回 `/PolaZhenjing/assets/images/richtext/...`。
- 历史坏图片占位是否不再直接露出为正文。

## 2026-06-29 部署状态

- 本地修复提交: `45c7de5 fix: 修复上传富文本图片和进度反馈`。
- 线上备份已完成: `/opt/backups/polazj-upload-media-45c7de5-20260629003819`。
- 本地待传输包: `/tmp/polazj-upload-media-45c7de5/runtime.tgz`。
- 阻塞点: 当前执行环境到 `42.121.164.11:22` 连续出现 `Operation not permitted`,导致 `scp` 和 `ssh stdin` 传输失败。
- 当前状态: 未覆盖线上文件,未重启服务,线上仍为部署前版本。
