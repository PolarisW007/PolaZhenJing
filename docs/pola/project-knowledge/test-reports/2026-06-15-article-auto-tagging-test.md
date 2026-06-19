# Test Report: 文章自动归类打标与快速筛选完善

日期: 2026-06-15

## 测试矩阵

| 验收项 | 类型 | 方式 | 状态 |
| --- | --- | --- | --- |
| A2 批量打标 | 脚本 | `scripts/auto_tag_posts.py --dry-run` / 执行 | 通过 |
| A3 上传自动标签 | 单元 | Flask client + draft 检查 | 通过 |
| A4 前台筛选 | 单元/浏览器 | HTML 断言 + Playwright | 通过 |
| A5 旧功能回归 | 单元 | 上传/首页/GEO 相关测试 | 通过 |
| A6 线上验证 | 集成 | 云服务器脚本、测试、浏览器 | 通过 |

## 命令记录

- 本地:
  - `.venv/bin/python -m py_compile app/uploader.py scripts/auto_tag_posts.py`
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py --dry-run`: `post_count=40`, `changed_count=40`, `ok=true`
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py`: `post_count=40`, `changed_count=40`, `ok=true`
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py --check`: `post_count=40`, `changed_count=0`, `ok=true`
  - `.venv/bin/python -m pytest tests/test_article_auto_tagging.py -q`: `6 passed`
  - `.venv/bin/python -m pytest tests/test_public_article_homepage.py tests/test_article_reader_roles.py tests/test_social_publish.py::test_geo_discovery_feeds_render -q`: `8 passed`
  - `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`: `ok=true`
- 本地 Browser harness:
  - `/articles` 显示业务主题: `coding-tools 11`, `industry-analysis 6`, `ai-engineering 5`, `agent-systems 4` 等。
  - 主题筛选后可见文章 `11/40`,关键词 `openai` 筛选后 `19/40`,二次点击关键词恢复 `40/40`。
- 云服务器:
  - 备份: `/opt/backups/polazj-article-auto-tagging-20260615-081201/files.tgz`
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py --dry-run`: `post_count=63`, `changed_count=63`, `ok=true`
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py`: `post_count=63`, `changed_count=63`, `ok=true`
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py --check`: `post_count=63`, `changed_count=0`, `ok=true`
  - `.venv/bin/python -m pytest tests/test_article_auto_tagging.py -q`: `6 passed`
  - `.venv/bin/python -m pytest tests/test_public_article_homepage.py tests/test_article_reader_roles.py tests/test_social_publish.py::test_geo_discovery_feeds_render -q`: `8 passed`
  - `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`: `ok=true`
  - `systemctl restart polazj.service`: 重启后 `active`
- 线上 Browser harness:
  - `https://aipd.me/articles`: `cardCount=63`
  - 主题列表: `coding-tools 20`, `industry-analysis 12`, `agent-systems 7`, `model-research 7`, `ai-engineering 6`, `testing-harness 4`, `media-generation 3`, `data-infrastructure 2`, `product-design 2`
  - `hasStyleTopic=false`,说明 `deep-technical` 等写作风格不再作为快速 Wiki 主主题。
  - 点击第一主题后 `topicVisible=20`;点击关键词 `claude` 后 `keywordVisible=30`;再次点击恢复 `63/63`。
  - 移动端 `390x900`: `scrollWidth=390`,无横向溢出。

## 残余风险

- 自动打标为规则分类,对部分叙事类文章可能仍需要人工微调。
- 线上 `_posts` 已批量改动,回滚可使用备份 `/opt/backups/polazj-article-auto-tagging-20260615-081201/files.tgz`。
