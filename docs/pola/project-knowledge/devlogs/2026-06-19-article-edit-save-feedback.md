# 开发日志：文章编辑页保存按钮无反馈修复

日期：2026-06-19

## 目标

修复线上文章编辑页填写“修改建议简述”后点击保存看起来没有反应的问题，并补齐真实保存按钮 Harness。

## 改动

- `app/templates/article_edit.html`
  - 新增 `#save-status`。
  - 提交时显示保存中/AI 调整中状态。
  - 禁用提交按钮并防止重复提交。
  - 用隐藏 `save_mode` 保留点击按钮语义。
- `scripts/upload_edit_playwright_harness.py`
  - 新增临时文章创建和清理。
  - 新增真实点击保存并验证文件写回。
  - 将页面等待从 `networkidle` 调整为 `domcontentloaded`，避免 favicon/字体噪声造成误报。
- `tests/test_article_edit_rich_editor.py`
  - 增加保存状态、`event.submitter`、隐藏 `save_mode` 和重复提交保护断言。

## 验证

- `.venv/bin/python -m py_compile app/uploader.py scripts/upload_edit_playwright_harness.py`
- `.venv/bin/python -m pytest tests/test_article_edit_rich_editor.py -q`
- `SECRET_KEY=dev-secret-change-me FLASK_APP='app:create_app' .venv/bin/flask run --host 127.0.0.1 --port 5019`
- `.venv/bin/python scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019`

结果：

- 单测：`10 passed`。
- Playwright：通过，生成三张截图，包含真实保存提交后的页面。

## 风险

- 本次不改 AI 改写同步等待模型的架构，只补可见状态和真实保存覆盖。
- 如果线上模型接口耗时较长，用户仍需等待，但页面会明确显示正在处理。
