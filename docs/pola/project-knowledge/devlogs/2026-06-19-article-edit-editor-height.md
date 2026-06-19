# 开发日志：文章编辑器高度优化

## 时间

2026-06-19 18:05 CST

## 目标

响应用户反馈“编辑器太小了”，提升已有文章编辑页正文编辑区高度，让长文编辑更接近一屏工作台体验。

## 改动

- `app/templates/article_edit.html`
  - Markdown 源码编辑框高度改为 `clamp(680px, 72vh, 980px)`。
  - 窄屏下高度改为 `clamp(560px, 68vh, 820px)`。
  - TinyMCE 富文本编辑器高度改为按窗口高度计算，范围 680-980px，最大可手动调整到 1100px。
  - TinyMCE 内部 iframe 最小编辑区提高到 560px，避免工具栏下面只剩很小正文区域。
- `tests/test_article_edit_rich_editor.py`
  - 增加编辑器工作台高度断言，防止回归成小文本框。

## 验证计划

- 语法检查：`python -m py_compile app/uploader.py`。
- 单测：`python -m pytest tests/test_article_edit_rich_editor.py -q`。
- 线上发布后检查编辑页 HTML 包含新高度策略，服务保持 active。

## 风险

- 页面整体会更长，但正文编辑可读性明显更好；保存、AI 修改开关、预览和上传流程不变。

