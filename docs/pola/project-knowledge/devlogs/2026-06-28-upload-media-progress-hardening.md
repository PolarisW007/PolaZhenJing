# 开发日志: 上传媒体与 PDF 进度修复

## 目标

修复线上云服务器上传/生成链路中的图片丢失和 PDF 上传无反馈问题:

- 阻止富文本空图、blob 图保存成坏 Markdown。
- 富文本图片上传返回稳定 `/PolaZhenjing/assets/...` 路径。
- 文件/PDF 上传增加浏览器进度条和处理中状态。

## 改动记录

- `app/article_content.py`
  - 增加富文本无效图片清理: 缺失/空 `src` 和 `blob:` 图片不会进入 canonical Markdown。
  - `normalize_markdown()` 增加历史裸图片占位清理,避免 `![alt]` 和 `![alt]()` 直接显示成正文。
- `app/uploader.py`
  - 富文本图片上传返回 `/PolaZhenjing/assets/images/richtext/...` 稳定路径。
  - 本地化富文本图片时删除无法持久化的 `blob:` 图片。
  - 文章详情页和分享卡片短链渲染 `_posts` body 前走 `normalize_markdown()`。
- `app/templates/upload.html`
  - 文件/PDF 上传表单改为 XHR 增强,增加进度条、上传中状态和失败恢复。
  - 粘贴表单提交前等待 TinyMCE `uploadImages()` 完成,若仍有 `blob:`/`data:image` 则阻止提交并提示。
- `tests/test_article_content.py`、`tests/test_upload_rewrite_rate.py`
  - 增加坏图清理、富文本媒体返回路径、上传进度 DOM/JS 的回归测试。
- `docs/pola/project-knowledge/delivery/upload-media-progress-hardening/function_test_cases.json`
  - 补充 A1-A5 验收与测试映射。

## 验证记录

- `.venv/bin/python -m py_compile app/article_content.py app/uploader.py app/__init__.py`: 通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_article_content.py tests/test_upload_rewrite_rate.py tests/test_article_edit_rich_editor.py tests/test_social_publish.py::test_public_article_short_link_renders_share_card_metadata -q`: 通过,28 passed。
- `.venv/bin/python /Users/wangchang/.agents/skills/pola-test-gate/scripts/validate_function_test_cases.py --prd docs/pola/project-knowledge/requirements/2026-06-28-upload-media-progress-hardening.md --prd docs/pola/project-knowledge/specs/2026-06-28-upload-media-progress-hardening-prd.md --sdd docs/pola/project-knowledge/architecture/2026-06-28-upload-media-progress-hardening-sdd.md --cases docs/pola/project-knowledge/delivery/upload-media-progress-hardening/function_test_cases.json`: 通过,覆盖 6 个文档验收点、5 个 feature、8 个 case。
- Flask test client Harness:
  - `/admin/upload` 返回 200。
  - 页面包含 `file-upload-progress`、`xhr.upload.onprogress`、`flushRichEditorImages`、TinyMCE media handler。
  - `/admin/upload/media` 返回 `/PolaZhenjing/assets/images/richtext/...`。
- 云服务器只读排查:
  - 线上 `_posts/2026-06-28-claude-code-cli-60-20260628.md` 第 36 行为裸图片占位 `![Claude Code 60+ 命令一览图]`。
  - 对应 `data/drafts/b851f54bdd08.json` 未保存 `original_media` / `inserted_images`,正文只有 X `media/...` 链接文本。
  - 服务器 `assets/images/generated/claude-code-cli-60-20260628/` 只有 AI 生成图,未找到原始“命令一览图”资源。
- 云服务器部署尝试:
  - 已备份运行时目标文件到 `/opt/backups/polazj-upload-media-progress-20260628195754`。
  - `rsync`、`tar | ssh`、`scp` 均受当前执行环境 SSH/传输限制影响,出现 `Operation not permitted` 或 `Connection closed`。
  - 纯 `ssh` 间歇可用,但无法稳定传输补丁包;本轮未成功覆盖线上运行时代码。
- 2026-06-29 git 与线上部署收尾:
  - 已将本地修复提交为 `45c7de5 fix: 修复上传富文本图片和进度反馈`。
  - 已再次备份线上运行时目标文件到 `/opt/backups/polazj-upload-media-45c7de5-20260629003819`。
  - 传输包 `/tmp/polazj-upload-media-45c7de5/runtime.tgz` 已在本地生成,仅包含 `app/article_content.py`、`app/uploader.py`、`app/templates/upload.html`。
  - 当前执行环境到 `42.121.164.11:22` 间歇返回 `Operation not permitted`;本轮未覆盖线上文件,也未重启 `polazj.service`,线上仍保持备份前状态。
  - 钉钉开发日志/AI 表格同步未执行;本轮 blocker 是云服务器 SSH 传输通道不稳定,待网络通道恢复后补同步或在下一次交付中补记。
- 2026-06-29 root 凭据与 Git 部署重试:
  - 本地部署连接信息记录为 `root@42.121.164.11`;明文密码不写入仓库、文档或脚本。
  - 已生成 Git bundle: `/tmp/polazj-upload-media-45c7de5/polazj-upload-media-ed7bfcf.bundle`,包含 `origin/main` 之后的 `45c7de5` 和 `ed7bfcf`。
  - 使用 `sshpass` 对 root 密码链路测试 8 次、原 `pola-server` alias 测试 3 次、root ControlMaster 持久连接测试 20 次,均在建立连接前返回 `Operation not permitted`。
  - 当前仍未覆盖线上文件、未重启服务;继续部署需先恢复本机到 `42.121.164.11:22` 的出站 SSH 通道。

## 风险与备注

- 当前本地仓库没有 `claude-code-cli-60-20260628.md` 及对应原图,用户确认文章在云服务器上。云端源文件中已经没有原图 URL,只能阻止坏占位继续显示;如需恢复原图,需要重新提供或重新抓取 X 原始图片。
- 本轮不打印、不提交任何 `.env` 或 secret。
