# 测试报告：文章阅读页右侧导航与点赞

## 测试状态

通过。

## 本地验证

- `.venv/bin/python -m py_compile app/__init__.py app/uploader.py`：通过。
- `.venv/bin/python -m pytest tests/test_article_reader_sidebar_like.py tests/test_article_reader_roles.py tests/test_public_article_homepage.py -q`：`9 passed`。
- `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`：`ok=true`。
- `git diff --check`：通过。
- 本地 Chrome harness：
  - URL：`http://127.0.0.1:5018/articles/yi-ge-ren-you-zheng-zhi-you-jia-20260524.md`
  - 右侧栏：可见，`position=sticky`。
  - 宽屏：点击后 `.article-reader-shell.is-wide=true`，右侧栏 `display=none`。
  - 恢复：再次点击恢复窄屏。
  - 点赞：`0 -> 1 -> 0`。
  - 备注：本地文章存在若干历史资源 404，不是本次脚本错误；线上目标页无控制台错误。

## 云端验证

- 备份：`/opt/backups/polazj-reader-sidebar-like-20260615-091807/files.tgz`。
- 云端测试：
  - `.venv/bin/python -m py_compile app/__init__.py app/uploader.py`：通过。
  - `.venv/bin/python -m pytest tests/test_article_reader_sidebar_like.py tests/test_article_reader_roles.py tests/test_public_article_homepage.py -q`：`9 passed`。
  - `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`：`ok=true`。
- 服务：`systemctl restart polazj.service` 后 `active`。
- curl：
  - `https://aipd.me/PolaZhenjing/articles/fde-databricks-snowflake-20260610.md`：`200 OK`，包含 `data-reader-shell`、`data-reader-sidebar`、`article-reader-nav-side`、`data-like-button`、`data-reader-width-toggle`。
  - `https://aipd.me/PolaZhenjing/articles/fde-databricks-snowflake-20260610.md/like`：返回 `{"ok": true, "article_id": "fde-databricks-snowflake-20260610.md", "like_count": 0}`。
- 线上 Chrome harness：
  - URL：`https://aipd.me/PolaZhenjing/articles/fde-databricks-snowflake-20260610.md`
  - 标题：`谈到FDE，浅析下DataBricks和Snowflake 的前世今生`。
  - 右侧栏：可见，`position=sticky`。
  - 快速 Wiki：8 条。
  - 宽屏：点击后隐藏右侧栏，再次点击恢复。
  - 点赞：`0 -> 1 -> 0`。
  - 控制台错误：无。

## 未覆盖项

- 未做多用户真实去重；本次需求为简单点赞，采用浏览器本地状态控制同浏览器重复点赞。
