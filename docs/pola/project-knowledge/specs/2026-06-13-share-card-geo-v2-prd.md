# PRD：分享卡片资产与 GEO v2

日期：2026-06-13

## 背景

Pola 真经文章已经具备短链、微信 JS-SDK、动态 sitemap 和 llms.txt 第一版。但分享卡片仍使用同一张 300x300 图承载所有平台，导致即刻/X 等通用 OG 平台不能获得更适合卡片展示的横图；复制短链入口只在管理员辅助区域出现；GEO 仍缺少 feed、robots 动态兜底、文章列表 ItemList 和更完整的 JSON-LD 图谱。

## 用户价值

- 普通读者看到文章后可以一键复制短链接分享。
- 微信分享更稳定，即刻/X/其他平台卡片图更适合横向摘要卡片。
- 搜索引擎、AI 搜索、浏览器代理和内容抓取器更容易理解站点结构、作者、文章列表、文章摘要和更新时间。

## 功能范围

### 分享卡片资产

| 平台 | 使用字段 | 图片规格 | 说明 |
| --- | --- | --- | --- |
| 微信聊天 | JS-SDK `title/desc/link/imgUrl` | 300x300 JPEG | 使用短链和微信缩略图 |
| 微信朋友圈 | JS-SDK `title/link/imgUrl` | 300x300 JPEG | 朋友圈不保证展示 desc |
| 即刻 | 服务端 OG meta | 1200x630 JPEG | 即刻通常以网页抓取方式读取卡片 |
| X / 通用社交 | OG/Twitter meta | 1200x630 JPEG | 输出 `summary_large_image` |
| 搜索 / AI | JSON-LD + canonical | 1200x630 + 300x300 | 保持 canonical 长链、shortlink 作为 sameAs |

### 分享链接按钮

- 位置：文章标题和摘要区域下方。
- 文案：`复制短链接`。
- 行为：
  - 点击复制 `short_url`。
  - 成功后短暂显示 `已复制`。
  - Clipboard API 不可用时降级为选中文本复制。
- 权限：
  - 普通读者可见。
  - 管理员同时可见发布辅助按钮。

### GEO v2

- 文章详情页：
  - 完整 meta、canonical、shortlink、OG、Twitter、itemprop。
  - JSON-LD `@graph`：Article、WebPage、WebSite、Person、Organization、BreadcrumbList。
  - Article 增加 `wordCount`、`articleSection`、`timeRequired`、`about`。
- 文章列表页：
  - canonical、description、OG/Twitter。
  - ItemList JSON-LD。
- 动态资源：
  - `/sitemap.xml`
  - `/robots.txt`
  - `/llms.txt`
  - `/feed.xml`
  - `/articles.json`

## 用户流程

1. 用户打开文章详情页。
2. 页面展示文章标题、摘要、元信息和“复制短链接”按钮。
3. 用户点击按钮，浏览器复制短链。
4. 用户把短链发到微信/即刻/X。
5. 平台抓取短链页：
   - 微信内打开文章后，使用右上角分享菜单时优先使用 JS-SDK 配置。
   - 直接把 URL 当文本粘贴进微信聊天框时，是否自动转卡片由微信客户端和缓存策略决定，页面无法强制。
   - 即刻/X 使用服务端 OG/Twitter meta。
   - 搜索和 AI 抓取使用 canonical、JSON-LD、sitemap/feed/llms。

## 异常与空态

- 文章没有自定义封面：使用第一张正文图；仍没有则使用默认封面。
- 图片生成失败：回退原始图片 URL，并记录 warning。
- 复制失败：页面降级提示用户手动复制短链。
- 微信 JS-SDK 配置失败：页面不影响阅读，前端把 `config-unavailable`、`fetch-error` 或 `wx.error` 回传到后端日志。
- 文章无 tags：不输出 keywords/tag；JSON-LD about 为空数组。
- 文章无 description/summary：自动从正文生成分享摘要。

## 验收映射

| 验收项 | 页面/接口 | 验证方式 |
| --- | --- | --- |
| A1-A4 | `/s/<code>`、`/articles/<file>` | pytest + wechat harness |
| A5 | 管理/公开 article HTML | pytest + harness |
| A6 | root 动态文件 | seo_geo_harness |
| A7 | article JSON-LD | seo_geo_harness |
| A8 | `/articles` | seo_geo_harness |
| A9 | 本地命令 | 测试报告 |
| A10-A12 | 云端 `/s/<code>` 与微信配置接口 | 线上 curl + harness + 诊断接口 |
