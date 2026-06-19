# SDD: 文章自动归类打标与快速筛选完善

日期: 2026-06-15

## 当前问题

- `upload()` 会根据正文调用 `extract_title()` 自动识别标题。
- 标签字段当前只使用 `request.form.get('tags')`,用户留空时保存空字符串。
- `_run_generate_job()` 直接把草稿 `tags` 写入 front matter,不会兜底生成。
- `public_articles.html` 快速 Wiki 使用文章首个 tag 或 layout 作为 section;大量文章没有 tags 时会退化为 layout,导致截图中 `deep-technical`、`friendly-explainer` 等写作风格成为主筛选。
- 关键词筛选用字符串包含匹配,大小写未统一。

## 方案

### 后端自动标签

在 `app/uploader.py` 增加纯函数:

- `_normalize_article_tag(tag)`
- `_dedupe_article_tags(tags)`
- `_auto_article_tags(title, content, existing_tags='')`

规则:

- 如果 `existing_tags` 非空,只做规范化和去重。
- 如果为空,根据标题+正文关键词打分选择主分类和补充标签。
- 输出 3-6 个英文小写 kebab-case 标签。

接入点:

- `upload()`: 保存 draft 前,以用户标题或自动标题 + content 生成 `resolved_tags`。
- `_run_generate_job()`: 写 front matter 前再兜底调用,防止旧 draft 或其他入口传空标签。

### 批量脚本

新增 `scripts/auto_tag_posts.py`:

- 扫描 `_posts/*.md`。
- 解析 front matter 与正文。
- 使用 `app.uploader._auto_article_tags()` 生成标签。
- 支持 `--dry-run` 输出变更预览。
- 默认执行时只替换 `tags:` 行;缺失则插入到 `date` 后。

### 前台筛选增强

修改 `public_articles.html`:

- `data-keywords` 使用小写标签集合。
- `data-filter-keyword` 使用小写值。
- JS 中 keyword 匹配统一 lower-case。

### 测试

- 新增 `tests/test_article_auto_tagging.py`:
  - 自动标签规则覆盖 Agent/Codex、Data、Video、测试文章。
  - 上传 draft 在用户不填 tags 时会写入自动标签。
  - 用户填 tags 时保留并规范化。
  - `/articles` 快速 Wiki 不应以 layout-only 标签为主。
- 更新/复用 `tests/test_public_article_homepage.py` 和 `seo_geo_harness.py`。
- 浏览器 harness 覆盖 topic/keyword filter。

## 部署与回滚

- 部署前备份云服务器 `_posts`、`app/uploader.py`、`public_articles.html`、脚本和测试。
- 部署后在服务器运行:
  - `python scripts/auto_tag_posts.py --dry-run`
  - `python scripts/auto_tag_posts.py`
  - 单元测试与 GEO harness。
- 回滚:
  - 从备份恢复 `_posts` 和相关代码。
  - 重启 `polazj.service`。
