# Devlog: 文章自动归类打标与快速筛选完善

日期: 2026-06-15

## 目标

阅读并归类所有文章,批量补齐业务标签;确认上传页标题/标签自动生成机制;完善前台快速 Wiki 标签筛选。

## 计划改动

- `app/uploader.py`: 增加自动标签规则,并接入上传 draft 和生成 front matter 兜底。
- `scripts/auto_tag_posts.py`: 新增批量打标脚本。
- `_posts/*.md`: 批量更新 tags。
- `app/templates/public_articles.html`: 增强关键词筛选大小写稳定性。
- `tests/test_article_auto_tagging.py`: 新增自动标签和上传机制测试。
- 项目文档: 需求、PRD、SDD、测试报告、开发日志。

## 验证记录

- 机制检查:
  - 标题: 上传文件、Markdown、富文本、URL 导入均已有 `extract_title()` 自动识别;用户手填标题优先。
  - 标签: 原实现只保存 `request.form.get('tags')`,用户留空会生成空 tags;本次已补自动生成。
- 本地:
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py --dry-run`: 40 篇待改,无错误。
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py`: 40 篇已打标。
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py --check`: `ok=true`。
  - `.venv/bin/python -m pytest tests/test_article_auto_tagging.py -q`: `6 passed`。
  - `.venv/bin/python -m pytest tests/test_public_article_homepage.py tests/test_article_reader_roles.py tests/test_social_publish.py::test_geo_discovery_feeds_render -q`: `8 passed`。
  - `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`: `ok=true`。
  - Browser harness: 主题/关键词筛选、二次取消、移动端无溢出通过。
- 云服务器:
  - 备份: `/opt/backups/polazj-article-auto-tagging-20260615-081201/files.tgz`。
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py --dry-run`: 63 篇待改,无错误。
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py`: 63 篇已打标。
  - `PYTHONPATH=. .venv/bin/python scripts/auto_tag_posts.py --check`: `post_count=63`, `changed_count=0`, `ok=true`。
  - 自动标签测试 `6 passed`,首页/读者/GEO 回归 `8 passed`,`seo_geo_harness.py` `ok=true`。
  - `systemctl restart polazj.service`,重启后 `active`。
- 线上:
  - `https://aipd.me/articles` 文章卡片数 `63`。
  - 快速 Wiki 主分类: `coding-tools 20`, `industry-analysis 12`, `agent-systems 7`, `model-research 7`, `ai-engineering 6`, `testing-harness 4`, `media-generation 3`, `data-infrastructure 2`, `product-design 2`。
  - 不再出现 `deep-technical`、`friendly-explainer` 等写作风格作为主主题。
  - 主题筛选、关键词筛选、关键词二次取消、移动端无横向溢出通过。

## 风险

- 风险等级: P2。
- 批量修改文章 front matter,需要备份和 dry-run。
- 线上文章数多于本地,部署后必须在服务器对线上 `_posts` 执行脚本。

## 状态

- 已完成本地和线上批量打标。
- 已部署上传自动标签机制。
- 已验证截图中的快速筛选功能完整可用。
- 本次未创建 git commit,因为工作区存在多项前序任务未提交改动;当前只确认本需求相关文件和线上变更可独立验收。
