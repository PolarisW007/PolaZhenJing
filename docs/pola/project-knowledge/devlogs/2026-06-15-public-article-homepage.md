# Devlog: PolaZhenjing 前台文章首页

日期: 2026-06-15

## 目标

将普通用户访问的文章列表升级为 PolaZhenjing 前台文章首页,支持 Wiki/知识库式浏览、精选文章、主题筛选、搜索和排序;管理员后台列表保持不变。

## 计划改动

- `app/uploader.py`: 为 `_render_public_articles()` 增加首页统计、主题、关键词和精选文章上下文。
- `app/templates/public_articles.html`: 重做前台首页结构与样式,并增加原生 JS 搜索/筛选/排序。
- `tests/test_public_article_homepage.py`: 新增普通/管理员权限和页面结构断言。
- `scripts/seo_geo_harness.py`: 增加文章首页结构断言。

## 实际改动

- 新增 `_public_article_home_context()` 和 `_public_filter_id()`,从现有 Markdown 摘要派生精选文章、主题频道、关键词、阅读时长和字数统计。
- 将 `public_articles.html` 从简单卡片列表升级为 PolaZhenjing 前台文章首页:
  - hero 定位与站点统计。
  - Featured 最新文章。
  - 快速 Wiki 主题/关键词筛选。
  - 搜索、排序和文章时间线。
  - RSS、JSON Feed、LLMs 入口。
- 保持权限分流:
  - 普通用户/游客访问 `/articles` 和 `/admin/articles` 均看到前台首页。
  - 管理员访问 `/admin/articles` 仍看到后台文章管理页。
- 增加 `tests/test_public_article_homepage.py` 和 `seo_geo_harness.py` 首页结构检查。

## 验证记录

- `.venv/bin/python -m py_compile app/uploader.py app/__init__.py app/auth.py`
- `.venv/bin/python -m pytest tests/test_public_article_homepage.py -q`
- `.venv/bin/python -m pytest tests/test_article_reader_roles.py tests/test_social_publish.py::test_geo_discovery_feeds_render -q`
- `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`
- Browser harness:
  - `/articles` desktop: 首页结构、搜索、排序、主题筛选通过。
  - `/admin/articles` anonymous: 渲染前台首页,不暴露后台标题。
  - `/articles` mobile `390x900`: `scrollWidth=390`,无横向溢出。
- 云服务器:
  - 备份: `/opt/backups/polazj-public-article-homepage-20260615-002443/files.tgz`
  - 同步: `app/uploader.py`, `app/templates/public_articles.html`, `tests/test_public_article_homepage.py`, `scripts/seo_geo_harness.py`,本需求文档。
  - 远端测试: 新增首页测试 `4 passed`,读者角色/GEO 相关测试 `4 passed`,`seo_geo_harness.py` 返回 `ok=true`。
  - 服务: `systemctl restart polazj.service`,重启后 `active`。
- 线上:
  - `https://aipd.me/articles`: 首页结构、搜索/排序/文章卡片、RSS/JSON/LLMs、ItemList 均存在。
  - `https://aipd.me/PolaZhenjing/admin/articles`: 匿名访问渲染前台首页,不暴露后台标题和新建文章入口。
  - Browser harness: 搜索空态、排序、主题筛选、移动端无横向溢出均通过。
  - 图片健康: 首页 45 张 featured/timeline 封面加载正常,破图数 0。

## 风险

- 风险等级: P2。
- 公开首页 UI 变更可能影响普通用户主入口和 SEO 首页渲染。
- 回滚: 恢复 `public_articles.html` 与 `app/uploader.py`,重启服务。

## 状态

- 已同步到云服务器并完成线上回归。
- 本次未创建 git commit,因为工作区存在多项前序任务的未提交改动;当前只确认本需求相关文件可独立验收。
