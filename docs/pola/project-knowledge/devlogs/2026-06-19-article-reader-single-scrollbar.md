# 开发日志：文章阅读页右侧单滚动条优化

## 时间

2026-06-19 CST

## 目标

用户反馈文章阅读页右侧出现两个滚动条，交互割裂。目标是移除右侧阅读导航区域的内部滚动，只保留浏览器最右侧页面滚动条，同时保持桌面端右侧导航吸顶和移动端响应式折叠。

## 改动

- `app/templates/article_view.html`
  - 移除 `.article-side-panel` 的 `max-height: calc(100vh - 2rem)`。
  - 移除侧栏内部滚动设置，改为 `overflow: visible`。
  - 桌面端仍保持 `position: sticky` 和右侧固定宽度。
  - 980px 以下仍切换为普通文档流，侧栏放到正文下方。
- `tests/test_article_reader_sidebar_like.py`
  - 增加断言，确保文章页模板不再输出侧栏内部滚动相关样式。

## 验证

- `.venv/bin/python -m pytest tests/test_article_reader_sidebar_like.py -q`：2 passed。

## 影响面

- 只影响文章阅读页的右侧阅读导航交互。
- 不改变文章正文、点赞、宽屏、管理员工具、分享按钮和编辑保存逻辑。

## 风险

- 如果右侧导航内容特别长，页面会整体变长；这是预期行为，用浏览器主滚动条统一控制。
