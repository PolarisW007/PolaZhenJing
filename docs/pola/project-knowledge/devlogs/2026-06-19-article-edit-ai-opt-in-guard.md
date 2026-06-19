# 开发日志：文章编辑 AI 修改显式开关与内容护栏

## 时间

2026-06-19 17:35 CST

## 目标

修复文章编辑保存后正文被 AI 输出污染、格式破坏、图片缺失的问题，并将 AI 修改改为管理员主动启用。

## 已完成

- 线上受影响文章 `rolling-ai-fde-ai-20260607.md` 先从 2026-06-17 备份恢复：
  - 恢复后 585 行、9 个图片/媒体引用、0 个 `<think>`。
  - 污染版本已备份到服务器恢复目录。
- 编辑页新增“启用 AI 修改”开关，默认关闭。
- AI 改写率和修改建议默认隐藏且禁用。
- 后端只有收到 `enable_ai_revision=1` 且修改建议非空时才调用 AI。
- AI 修订输出会剥离 `<think>`、Markdown 围栏，拒绝英文模型自述开头的内容。
- AI 修订后补回原 Markdown 图片和 HTML 媒体引用。
- 更新编辑模块单测和 Playwright harness。

## 验证

- `.venv/bin/python -m py_compile app/uploader.py scripts/upload_edit_playwright_harness.py`：通过。
- `.venv/bin/python -m pytest tests/test_article_edit_rich_editor.py -q`：13 passed。
- `.venv/bin/python -m pytest tests/test_article_content.py tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py tests/test_public_article_homepage.py tests/test_article_reader_roles.py tests/test_article_reader_sidebar_like.py -q`：32 passed。
- `.venv/bin/python scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019`：通过，覆盖上传页、编辑页、AI 面板默认隐藏、开启后可填写、保存写回。

## 影响面

- 影响后台文章编辑保存链路。
- 不影响上传文章生成、文章阅读页、短链接、分享卡片、多平台发布。

## 风险

- AI 启用后的媒体补回可能把遗漏图片追加到“原文媒体”区域，图片位置不保证完全还原；但优先避免图片丢失。
- 仍需线上部署后回归。
