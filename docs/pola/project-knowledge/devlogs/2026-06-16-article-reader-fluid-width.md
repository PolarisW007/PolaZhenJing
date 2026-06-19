# 开发日志：文章阅读页自适应宽度优化

## 目标

用户反馈 `https://aipd.me/PolaZhenjing/articles/fde-databricks-snowflake-20260610.md` 在宽屏下中间阅读区域过窄、两边空白过多。要求：

- 1 号主文章区域随屏幕宽度自适应展开。
- 2 号右侧导航区域保持当前宽度。
- 手机屏幕宽度下，2 号区域下沉到 1 号正文底部。

## 改动

- `app/templates/article_view.html`
  - 覆盖文章页 `.card-full` 最大宽度为 `min(1840px, calc(100vw - 64px))`。
  - `.article-reader-shell` 改为 `minmax(0, 1fr) 300px`，让主文章列吃掉剩余空间。
  - `.article-side-panel` 固定宽度 `300px`。
  - 标题、摘要、管理员工具、正文、作者 footer 的最大宽度统一放宽到 `min(1180px, 100%)`。
  - 响应式断点调整为 `980px`，小屏下单列排列，右侧导航自然落到正文后。

## 验证

- 本地：
  - `.venv/bin/python -m py_compile app/uploader.py app/__init__.py`：通过。
  - `.venv/bin/python -m pytest tests/test_article_reader_sidebar_like.py tests/test_article_reader_roles.py -q`：`5 passed`。
  - `git diff --check -- app/templates/article_view.html docs/pola/project-knowledge/devlogs/2026-06-16-article-reader-fluid-width.md`：通过。
  - Chrome harness：
    - 桌面 `2048x1229`：`.card-full=1840px`，主文章列 `1438px`，右侧栏 `300px`，正文 `1180px`，右侧栏位于主列右侧。
    - 手机 `390x900`：主文章列 `284px`，右侧栏 `284px`，右侧栏位于正文下方。
- 云端：
  - `.venv/bin/python -m py_compile app/uploader.py app/__init__.py`：通过。
  - `.venv/bin/python -m pytest tests/test_article_reader_sidebar_like.py tests/test_article_reader_roles.py -q`：`5 passed`。
  - 线上 Chrome harness：
    - URL：`https://aipd.me/PolaZhenjing/articles/fde-databricks-snowflake-20260610.md`
    - 桌面 `2048x1229`：`.card-full=1840px`，主文章列 `1438px`，右侧栏 `300px`，正文 `1180px`。
    - 手机 `390x900`：主文章列 `284px`，右侧栏 `284px`，右侧栏位于正文下方。
    - 控制台错误：无。

## 发布

- 备份：`/opt/backups/polazj-article-fluid-width-20260616-114445/files.tgz`。
- 部署：精确同步 `app/templates/article_view.html` 和本开发日志到 `/PolaZhenjing`。
- 修正记录：首次 rsync 误传到 `/PolaZhenJing-does-not-exist`，已立即删除该误目录；随后同步到正确 `/PolaZhenjing`。
- 服务：`systemctl restart polazj.service` 后 `active`。
