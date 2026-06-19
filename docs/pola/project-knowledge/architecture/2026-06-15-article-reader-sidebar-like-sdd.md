# SDD：文章阅读页右侧辅助导航与点赞

## 现状

- 文章详情由 `app/uploader.py::_render_article` 渲染 `app/templates/article_view.html`。
- 上一篇、下一篇和快速 Wiki 由 `_article_navigation_context` 生成，当前在模板底部渲染。
- 项目数据库通过 `app/__init__.py::get_db()` 使用 SQLite `data/wiki.db`。
- 管理员工具通过 `can_manage` 控制，普通用户不可见。

## 架构选型

| 方案 | 说明 | 结论 |
| --- | --- | --- |
| A 仅用前端静态计数 | 不落库，无法刷新保持 | 拒绝 |
| B 现有 Flask + SQLite 增加轻量计数 | 与项目现有模式一致，部署简单 | 采用 |
| C 引入用户点赞关系表和登录强绑定 | 更完整但超出“简单点赞” | 暂不采用 |

## 数据设计

新增表：

```sql
CREATE TABLE IF NOT EXISTS article_likes (
  article_id TEXT PRIMARY KEY,
  like_count INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

`article_id` 使用短管理文件名，例如 `fde-databricks-snowflake-20260610.md`。

## 接口设计

- `GET /articles/<filename>/like`
  - 返回当前文章点赞数。
- `POST /articles/<filename>/like`
  - 请求体：`{"liked": true}` 或 `{"liked": false}`。
  - `liked=true` 增加 1；`liked=false` 减少 1，最低为 0。

浏览器端使用 `localStorage` 记录当前浏览器是否已经点赞该文章，避免同一浏览器反复累加。

## 前端设计

- 在文章模板增加 `.article-reader-shell` 两栏布局。
- 主栏保留文章正文和管理员工具。
- 侧栏 `.article-side-panel` 使用 `position: sticky; top: 1rem;`。
- `is-wide` 状态隐藏侧栏并扩大正文内容宽度。
- 宽屏状态写入 `localStorage`，同一浏览器下保持阅读偏好。

## 文件影响

- `app/__init__.py`：初始化点赞表。
- `app/uploader.py`：新增点赞 helper、API 路由、模板变量。
- `app/templates/article_view.html`：调整布局、增加点赞和宽屏交互。
- `tests/test_article_reader_sidebar_like.py`：覆盖模板和 API。
- `docs/pola/project-knowledge/*`：记录需求、方案、验证和开发日志。

## 测试策略

- Python 语法检查：`python -m py_compile app/__init__.py app/uploader.py`
- 单元/集成：文章模板、点赞 API、公开文章首页和角色显示相关测试。
- 浏览器 harness：本地打开目标文章，验证侧栏、宽屏切换、点赞按钮和控制台错误。
- 线上回归：部署后访问目标 URL 验证同一路径。

## 部署与回滚

- 部署需要同步 Python、模板、测试和文档文件，并重启 Flask 服务以初始化表。
- 回滚可恢复 `app/__init__.py`、`app/uploader.py`、`app/templates/article_view.html` 到上一版本；保留空表不影响旧页面。
