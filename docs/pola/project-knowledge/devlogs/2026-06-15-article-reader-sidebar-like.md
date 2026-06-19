# 开发日志：文章阅读页右侧导航与点赞

## 目标

将文章详情页底部重复的上一篇/下一篇/快速 Wiki 移到右侧 sticky 区域，增加宽窄屏切换，并为文章增加简单点赞功能。

## 风险与门禁

- 风险等级：P2。
- 涉及数据库表初始化和公开 API，需要本地测试、线上部署后回归。
- 不涉及 secret、后台任务、大文件处理或外部 API。

## 改动记录

- `app/__init__.py`
  - 新增 `article_likes` 表初始化，用于保存文章点赞计数。
- `app/uploader.py`
  - 引入 `get_db`。
  - 新增 `_article_like_count`。
  - 新增 `GET/POST /articles/<filename>/like` 公开点赞 API。
  - `_render_article` 向模板传入 `article_like_count` 和 `article_like_url`。
- `app/templates/article_view.html`
  - 增加 `.article-reader-shell` 主文 + 右侧栏布局。
  - 将上一篇、下一篇、快速 Wiki 从正文底部移动到右侧 sticky 面板。
  - 增加宽屏/窄屏切换，宽屏时隐藏右侧面板并扩大正文宽度。
  - 增加文章点赞按钮和前端交互。
- `tests/test_article_reader_sidebar_like.py`
  - 覆盖阅读侧栏模板标记和点赞 API 增减计数。
- `docs/pola/project-knowledge/*`
  - 新增本次需求、PRD、SDD、测试报告和开发日志。

## 验证记录

- 本地：
  - `.venv/bin/python -m py_compile app/__init__.py app/uploader.py`：通过。
  - `.venv/bin/python -m pytest tests/test_article_reader_sidebar_like.py tests/test_article_reader_roles.py tests/test_public_article_homepage.py -q`：`9 passed`。
  - `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`：`ok=true`。
  - `git diff --check`：通过。
  - Chrome harness：侧栏 sticky、宽屏隐藏/恢复、点赞 `0 -> 1 -> 0`。
- 云端：
  - `.venv/bin/python -m py_compile app/__init__.py app/uploader.py`：通过。
  - `.venv/bin/python -m pytest tests/test_article_reader_sidebar_like.py tests/test_article_reader_roles.py tests/test_public_article_homepage.py -q`：`9 passed`。
  - `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`：`ok=true`。
  - `https://aipd.me/PolaZhenjing/articles/fde-databricks-snowflake-20260610.md`：`200 OK`，核心 DOM 标记存在。
  - 线上 Chrome harness：右侧栏可见且 sticky，快速 Wiki 8 条，宽屏隐藏/恢复，点赞 `0 -> 1 -> 0`，控制台无错误。

## 发布记录

- 备份：`/opt/backups/polazj-reader-sidebar-like-20260615-091807/files.tgz`。
- 部署方式：精确 rsync 同步本次相关 `app/`、`tests/`、`docs/` 文件；未同步 `_posts`。
- 修正记录：首次 rsync 少了 `--relative`，误放到远端项目根目录的副本已删除，随后使用 `rsync -avR` 重新同步到正确路径。
- 服务：`systemctl restart polazj.service` 后状态 `active`。
- 回滚：从备份恢复 `app/__init__.py`、`app/uploader.py`、`app/templates/article_view.html` 并重启 `polazj.service`；空的 `article_likes` 表可保留，不影响旧页面。
