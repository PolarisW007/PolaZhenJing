# Devlog: 文章浏览页权限与导航优化

日期: 2026-06-14

## 目标

优化文章浏览页,让普通用户看到干净阅读页,管理员看到集中管理工具;同时增加上一篇/下一篇和快速文章切换。

## 实际改动

- `app/templates/article_view.html`: 去重标题下方摘要/分享区,保留单一摘要卡片;将编辑、同步发布、查看、删除、复制卡片链接、阅读短链、微信/朋友圈、即刻、Twitter、LinkedIn、图文卡片复制/下载集中到管理员工具区;正文后增加上一篇/下一篇和快速 Wiki。
- `app/templates/base.html`: 增加普通用户轻导航,登录普通用户显示文章列表、织梦空间、PolaUUH 用户中心、设置、退出,不显示管理后台导航。
- `app/templates/account.html`: 将账号页标题统一为 `PolaUUH 统一用户中心`。
- `app/uploader.py`: 增加 `_article_navigation_context()` 与 `_article_nav_item()`,在 `_render_article()` 中传入文章导航上下文。
- `tests/test_article_reader_roles.py`: 新增公开用户、普通登录用户、管理员三种角色的文章页权限/UI 断言。
- `tests/test_social_publish.py`: 更新公开短链页预期,公开页保留微信 JS-SDK 原生分享配置但不显示管理员复制/海报控件;管理员页保留这些工具。

## 验证记录

- `.venv/bin/python -m py_compile app/uploader.py app/auth.py app/__init__.py`: 通过。
- `.venv/bin/python -m pytest tests/test_article_reader_roles.py tests/test_social_publish.py::test_public_article_short_link_renders_share_card_metadata tests/test_social_publish.py::test_public_article_card_link_is_lightweight_for_social_crawlers -q`: 5 passed。
- `.venv/bin/python -m pytest tests/test_social_publish.py tests/test_article_edit_rich_editor.py tests/test_article_reader_roles.py tests/test_polauuh_auth.py -q`: 29 passed。
- `.venv/bin/python -m pytest tests -q`: 48 passed。
- `.venv/bin/python -m pytest -q`: 因 `referene/TencentDB-Agent-Memory/...` 外部参考测试缺少 `agent` 包在 collection 阶段失败,非本项目 `tests/` 范围。
- Chrome/Playwright 本地 harness:
  - public `/articles/yi-ge-ren-you-zheng-zhi-you-jia-20260524.md`: `summaryCount=1`, `quickWikiCount=1`, `copyCardControls=0`, `wechatCardControls=0`, `prevNextCards=2`, `hasAdminNav=false`。
  - normal-user: `hasPolauuh=true`, `hasAdminNav=false`, `adminToolsCount=0`, `summaryCount=1`, `quickWikiCount=1`。
  - admin `/admin/articles/yi-ge-ren-you-zheng-zhi-you-jia-20260524.md`: `hasAdminNav=true`, `adminToolsCount=1`, `copyCardControls=1`, `wechatCardControls=1`, `summaryCount=1`, `quickWikiCount=1`。
  - 本地目标文章 `fde-databricks-snowflake-20260610.md` 不存在,线上部署后需用真实线上文件补一次 harness。
- 云端部署:
  - 备份目录: `/opt/backups/polazj-article-reader-admin-split-20260614225747`。
  - 精确同步 `app/uploader.py`、文章/基础/账号模板、share card 模板、测试、GEO/微信 harness 和交付文档到 `/PolaZhenjing`。
  - 云端 `.venv/bin/python -m py_compile app/uploader.py app/auth.py app/__init__.py`: 通过。
  - 云端相关测试: `11 passed in 1.06s`。
  - 云端 `tests/` 全集: `45 passed in 1.36s`。
  - `systemctl restart polazj.service`: 服务 `active`,新 master PID `727538`。
- 线上验证:
  - `curl https://aipd.me/articles/fde-databricks-snowflake-20260610.md`: `200`,下载 60803 bytes。
  - 目标文章公开页: `summary=1`, `quickWiki=true`, `public_copy=false`, `public_admin_nav=false`。
  - 目标文章管理员 test-client: `admin_tools=true`, `data-copy-cardlink=true`, `data-copy-wechat-card=true`。
  - 云端 `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`: `ok=true`, `error_count=0`。
  - 云端 `.venv/bin/python scripts/wechat_share_harness.py`: `wechat_share_harness: ok`,目标文章 `fde-databricks-snowflake-20260610.md`,卡片 URL `https://aipd.me/c/49c0c4e8`。
  - 线上 Chrome PC DOM: `summaryCount=1`, `quickWikiCount=1`, `prevNextCards=2`, `copyCardControls=0`, `wechatCardControls=0`,`hasAdminNav=false`。
  - 线上 Chrome mobile DOM: `summaryCount=1`, `quickWikiCount=1`, `prevNextCards=2`, `copyCardControls=0`, `wechatCardControls=0`,`bodyWidth=390`。

## 风险

- 风险等级: P2。
- 管理员工具入口若误隐藏会影响发布/编辑效率;普通用户若误显示会造成权限心智混乱。
- 回滚: 恢复模板和 `app/uploader.py` 备份后重启服务。

## 不影响功能使用的验证路径

- 公开文章列表 `/articles`: 未改变数据源与路由。
- 公开文章详情 `/articles/<file>`: 保留 SEO/OG/Twitter/JSON-LD/微信 JS-SDK 分享配置,仅移除公开可见的管理员按钮。
- 管理员文章详情 `/admin/articles/<file>`: 编辑、同步发布、查看、删除和分享工具仍可见。
- 账号与设置: 普通用户通过 PolaUUH 用户中心和设置进入;管理员后台仍保留用户/密码入口。
- 文章编辑保存、富文本图片本地化、社交发布相关测试保持通过。
