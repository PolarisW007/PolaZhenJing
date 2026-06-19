# Devlog: 文章详情编辑按钮前缀修复

## 目标

用户反馈线上文章详情页 `https://aipd.me/articles/rolling-ai-fde-ai-20260607.md` 中管理员「编辑」按钮点击无反应。截图 hover 显示按钮指向 `https://aipd.me/admin/articles/.../edit`，而线上 Flask 后台实际挂载在 `/PolaZhenjing/admin/*`。

本次为小范围生产 bugfix，目标是让根域公开文章页和 `/PolaZhenjing/articles/*` 文章页中的管理员按钮都稳定指向 `/PolaZhenjing/admin/*`，不改变普通用户可见内容、文章正文、点赞、宽屏阅读和分享卡片逻辑。

## 改动

- `app/uploader.py`
  - 新增 `_polazhenjing_admin_url()`，在无 `SCRIPT_NAME` 的根域公开文章页下把 `/admin/*` 链接规范化为 `/PolaZhenjing/admin/*`。
  - `_render_article()` 统一向模板传入 `admin_edit_url`、`admin_publish_url`、`admin_delete_url`。
- `app/templates/article_view.html`
  - 顶部和管理员工具区的「编辑」「同步发布」「删除」改用后端传入的规范后台 URL。
- `tests/test_article_reader_roles.py`
  - 增加回归测试：管理员登录态访问根路径 `/articles/<file>` 时，管理按钮必须输出 `/PolaZhenjing/admin/*`，不能输出无前缀 `/admin/*`。

## 验证

- `.venv/bin/python -m py_compile app/uploader.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_article_reader_roles.py tests/test_article_reader_sidebar_like.py -q`：6 passed。

## 影响面

- 只影响管理员在文章详情页看到的后台管理链接。
- 普通用户仍不显示编辑、同步发布、删除等后台工具。
- 不修改文章 Markdown 内容、数据库结构、分享 API、微信 JS-SDK 和 nginx 配置。

## 风险与回滚

- 风险：若未来部署前缀不再是 `/PolaZhenjing`，该 helper 需要同步调整。
- 回滚：恢复 `app/uploader.py` 和 `app/templates/article_view.html` 中本次链接生成改动即可。

## 状态

- 本地修复完成，等待云端同步与线上 harness 验证。
- Commit：未提交。
