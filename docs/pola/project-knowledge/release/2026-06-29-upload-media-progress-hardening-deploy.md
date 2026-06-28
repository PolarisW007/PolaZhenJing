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

## 2026-06-29 部署完成记录

- 原因确认: 用户本机普通终端可登录云服务器,而 Codex 旧会话中 `nc`/`ssh` 对公网 IP 返回 `Operation not permitted`;当前权限恢复后 `nc 42.121.164.11 22` 成功,判定为 Codex 执行环境网络沙箱限制。
- GitHub: `main` 已推送到 `83526b4`。
- 云服务器: `/PolaZhenjing` 已 `git fetch origin main`,`origin/main=83526b4`。
- 线上备份: `/opt/backups/polazj-upload-media-83526b4-20260629074333`。
- 部署方式: 从 `origin/main` 精确 checkout `app/article_content.py`、`app/uploader.py`、`app/templates/upload.html`,未执行全量 `git pull`,未覆盖文章和运行数据。
- 云端测试:
  - `py_compile`: 通过。
  - 相关 pytest: `24 passed in 1.19s`。
  - `polazj.service`: 重启后 `active`。
  - Flask test-client 上传页: 200,含进度条与图片 flush 逻辑。
  - Flask test-client 问题文章: 200,裸图片占位不再露出。
  - 公网 smoke: login 200,upload 未登录 302,问题文章 200。

## Git 部署恢复信息

- 连接账号: `root@42.121.164.11`;密码仅由操作者临时提供,不落库、不入文档。
- Git bundle: `/tmp/polazj-upload-media-45c7de5/polazj-upload-media-ed7bfcf.bundle`。
- bundle 内容: `origin/main` 之后的 `45c7de5`、`ed7bfcf`。
- 服务器恢复部署命令草案:
  1. 上传 bundle 到 `/tmp/polazj-upload-media-ed7bfcf.bundle`。
  2. `cd /PolaZhenjing && git fetch /tmp/polazj-upload-media-ed7bfcf.bundle HEAD:refs/tmp/upload-media-ed7bfcf`
  3. `cd /PolaZhenjing && git checkout refs/tmp/upload-media-ed7bfcf -- app/article_content.py app/uploader.py app/templates/upload.html`
  4. `cd /PolaZhenjing && .venv/bin/python3 -m py_compile app/article_content.py app/uploader.py app/__init__.py`
  5. `systemctl restart polazj.service && systemctl is-active polazj.service`
  6. 执行发布后验证中的 curl/HTML 探针。
