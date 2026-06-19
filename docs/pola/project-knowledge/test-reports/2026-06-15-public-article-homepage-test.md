# Test Report: PolaZhenjing 前台文章首页

日期: 2026-06-15

## 测试矩阵

| 验收项 | 类型 | 方式 | 状态 |
| --- | --- | --- | --- |
| A2 `/articles` 前台首页 | 集成 | Flask test client HTML 断言 | 通过 |
| A3 普通用户 `/admin/articles` 前台首页 | 集成 | session role=user HTML 断言 | 通过 |
| A4 管理员 `/admin/articles` 后台列表 | 集成 | session role=admin HTML 断言 | 通过 |
| A5 首页模块完整 | 集成 | hero/featured/topics/tools/timeline 断言 | 通过 |
| A6 搜索/筛选/排序 | 浏览器 | Chrome/Playwright DOM 操作 | 通过 |
| A7 SEO/GEO | harness | `seo_geo_harness.py` | 通过 |
| A8 移动端无横向溢出 | 浏览器 | Chrome/Playwright mobile viewport | 通过 |

## 命令记录

- `.venv/bin/python -m py_compile app/uploader.py app/__init__.py app/auth.py`
- `.venv/bin/python -m pytest tests/test_public_article_homepage.py -q`
- `.venv/bin/python -m pytest tests/test_article_reader_roles.py tests/test_social_publish.py::test_geo_discovery_feeds_render -q`
- `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`
- Browser harness:
  - desktop `1440x1100`: `/articles` 结构、搜索空态、排序、主题筛选通过。
  - anonymous `/admin/articles`: 渲染前台首页,不出现后台标题。
  - mobile `390x900`: `scrollWidth=390`,无横向溢出。
- 云服务器:
  - `ssh pola-server 'cd /PolaZhenjing; .venv/bin/python -m py_compile app/uploader.py app/__init__.py app/auth.py'`
  - `ssh pola-server 'cd /PolaZhenjing; .venv/bin/python -m pytest tests/test_public_article_homepage.py -q'`: `4 passed`
  - `ssh pola-server 'cd /PolaZhenjing; .venv/bin/python -m pytest tests/test_article_reader_roles.py tests/test_social_publish.py::test_geo_discovery_feeds_render -q'`: `4 passed`
  - `ssh pola-server 'cd /PolaZhenjing; PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py'`: `ok=true`
- 线上:
  - `https://aipd.me/articles`: 首页结构、RSS/JSON/LLMs、ItemList 均存在,不出现后台标题。
  - `https://aipd.me/PolaZhenjing/admin/articles`: 匿名访问渲染前台首页,不出现后台标题和新建文章入口。
  - Browser harness: 搜索空态、排序、主题筛选、移动端无横向溢出均通过。
  - 图片健康: 首页 45 张 featured/timeline 封面加载正常,破图数 0。

## 残余风险

- 页面由 Markdown 文件实时扫描派生数据,文章量继续增大时可能需要缓存首页摘要。
- 管理员后台列表不在本次重做范围,仍保持原体验。
