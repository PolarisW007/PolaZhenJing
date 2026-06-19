# SDD: PolaZhenjing 前台文章首页

日期: 2026-06-15

## 当前实现

- `/admin/articles` 由 `app/uploader.py::articles()` 处理:
  - 管理员: 渲染 `articles.html` 后台列表。
  - 非管理员: 调用 `_render_public_articles()`。
- `/articles` 由 public blueprint 渲染同一个 `_render_public_articles()`。
- `_render_public_articles()` 扫描 `_posts`,用 `_post_public_summary()` 生成 `posts`,渲染 `app/templates/public_articles.html`。
- `public_articles.html` 当前是简单卡片列表,缺少前台首页结构、搜索、筛选、排序和知识库导览。

## 设计方案

### 后端数据

继续复用 `_scan_posts()` 和 `_post_public_summary()`。

新增轻量派生数据:

- `featured_post`: 首篇/最新文章。
- `topic_filters`: 按 `section` 聚合文章数量。
- `keyword_filters`: 从 `keywords` 聚合前若干常用关键词。
- `article_stats`: 文章总数、主题数、总阅读时长、总字数。

这些数据只在请求时由 Markdown 元数据派生,不写数据库。

### 模板

改造 `app/templates/public_articles.html`:

- 外层 `.public-home-card` 去掉后台卡片边框和背景,让页面成为独立前台首页。
- 增加:
  - hero 区。
  - 精选文章区。
  - 频道/关键词筛选。
  - 搜索与排序工具条。
  - 文章时间线。
- 使用原生 JS 做无刷新筛选/排序,不引入依赖。

### 权限

权限逻辑保持现状:

- `_is_admin_session()` 为真时 `/admin/articles` 渲染后台管理页。
- 普通用户/游客渲染 `public_articles.html`。

### SEO/GEO

保留并增强:

- canonical: `https://aipd.me/articles`
- RSS: `https://aipd.me/feed.xml`
- JSON feed: `https://aipd.me/articles.json`
- LLMs: `https://aipd.me/llms.txt`
- JSON-LD `ItemList`

### 测试策略

- 新增/扩展 Flask test:
  - `/articles` 包含前台首页结构。
  - 普通用户 `/admin/articles` 不含后台导航,含前台首页结构。
  - 管理员 `/admin/articles` 保持后台列表。
  - 搜索/筛选 DOM 属性存在。
- 更新 `seo_geo_harness.py` 的文章索引断言。
- 浏览器 harness:
  - PC 1280x900。
  - mobile 390x844。
  - 检查无横向溢出、搜索后列表减少/空态可显示、频道按钮有效。

## 风险与回滚

- 风险: 前台首页模板较大,若 JS 出错仍应保留静态文章列表可点击。
- 回滚: 恢复 `app/templates/public_articles.html` 和 `app/uploader.py`;重启 `polazj.service`。
- 不涉及 `.env`、secret、数据库迁移或后台任务。
