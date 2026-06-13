# SPEC：分享卡片资产与 GEO v2

日期：2026-06-13

## ShareMeta 数据契约

每篇文章渲染时生成以下字段：

| 字段 | 来源优先级 | 用途 |
| --- | --- | --- |
| `share_title` | `share_title` front matter -> `title` -> 文件名 | 卡片标题、JSON-LD headline |
| `share_description` | `share_summary` -> `description` -> `summary` -> 正文抽取 | 微信 desc、OG description、JSON-LD description |
| `canonical_url` | `/articles/<admin_filename>` | 搜索索引与引用 |
| `short_url` | `/s/<8hex>` | 人类分享与 JS-SDK link |
| `wechat_share_image` | `share_image/image/cover/首图/默认图` -> 300x300 JPEG | 微信聊天和朋友圈 |
| `og_share_image` | 同上 -> 1200x630 JPEG | 即刻、X、通用 OG/Twitter |
| `article_keywords` | `tags` | keywords、article:tag、JSON-LD about |
| `article_section` | 第一个 tag -> layout -> `AI Articles` | JSON-LD articleSection |
| `article_word_count` | 正文清洗后计算 | JSON-LD wordCount |
| `article_read_time_iso` | 阅读时长 | JSON-LD timeRequired |
| `wechat_share_config_url` | 固定公网 `/PolaZhenjing/admin/api/wechat/share-config` | root 短链页获取 JS-SDK 签名 |
| `wechat_share_diagnostics_url` | 固定公网 `/PolaZhenjing/admin/api/wechat/share-diagnostics` | 回传 JS-SDK ready/error 状态 |

## 分享图片生成规则

| 预设 | 文件名后缀 | 尺寸 | 格式 | 质量 |
| --- | --- | --- | --- | --- |
| `wechat` | `-wechat.jpg` | 300x300 | JPEG | 86 |
| `og` | `-og.jpg` | 1200x630 | JPEG | 88 |

- 使用 `ImageOps.exif_transpose` 修正方向。
- 使用 `ImageOps.fit` 居中裁切。
- 输出 progressive JPEG。
- 输出文件若不存在或源图更新，则重新生成。
- 目录：`assets/images/share/`，由 `.gitignore` 忽略。

## HTML 输出规则

### 文章详情页

- `meta description` = `share_description`
- `canonical` = `canonical_url`
- `shortlink` = `short_url`
- `og:url` = `short_url`
- `og:image` = `og_share_image`
- `twitter:image` = `og_share_image`
- `WECHAT_SHARE.imgUrl` = `wechat_share_image`
- `WECHAT_SHARE.link` = `short_url`
- 微信配置接口必须使用 `https://aipd.me/PolaZhenjing/admin/api/wechat/share-config`。
- 微信诊断接口必须使用 `https://aipd.me/PolaZhenjing/admin/api/wechat/share-diagnostics`。
- `wx.ready` 成功后设置 `window.__PZJ_WECHAT_SHARE_READY=true` 并回传 `ready`。
- `wx.error`、签名不可用或 fetch 失败时回传非敏感错误状态，不阻断阅读和复制短链。
- JSON-LD 使用 `@graph`

### 文章列表页

- `canonical=https://aipd.me/articles`
- `og:type=website`
- `ItemList` 中每个 item 指向 canonical article URL。

## 动态资源规则

### `/robots.txt`

- `Allow: /`
- `Disallow: /admin/`
- `Disallow: /PolaZhenjing/admin/`
- `Sitemap: https://aipd.me/sitemap.xml`

### `/sitemap.xml`

- 包含首页、文章列表、Agent、About、feed、articles.json、llms。
- 文章 URL 使用 canonical 长链，不使用短链，避免重复索引。

### `/llms.txt`

- 包含站点身份、入口、feed、文章索引、分享元数据契约、AI agent guidance。
- 明确 canonical 用于引用、shortlink 用于分享。

### `/feed.xml`

- RSS 2.0。
- item 使用 canonical URL，guid 使用 canonical URL。

### `/articles.json`

- JSON Feed 风格。
- 包含 title、summary、canonical url、shortlink、date、tags。

## Harness

- `scripts/wechat_share_harness.py`
  - 验证 OG 横图、微信正方图、短链、复制按钮、公开/管理权限边界、微信公网 API 前缀和诊断钩子。
- `scripts/seo_geo_harness.py`
  - 验证文章页 JSON-LD、文章列表 ItemList、robots、sitemap、llms、feed、articles.json。
- `tests/test_social_publish.py`
  - 覆盖短链、分享 meta、管理/公开按钮边界。
