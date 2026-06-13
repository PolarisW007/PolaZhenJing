# 调研：Pola 真经 GEO 优化细化

日期：2026-06-13

## 结论摘要

GEO 不应理解为给 AI 单独堆关键词或生成大量变体页。对 Pola 真经这类文章站，最有效、最低风险的方向是：

1. 保持文章内容独特、有明确观点和一手判断。
2. 保证公开页面服务端可抓取，不依赖客户端 JS 后补核心内容。
3. 用 canonical、sitemap、feed、结构化数据把内容关系讲清楚。
4. 给 AI/agent 额外提供 llms.txt、articles.json 这类易解析索引，但不把它们当作 Google 的特殊捷径。
5. 保持分享卡片和摘要稳定，降低微信/即刻/X 抓取失败概率。

## 官方依据

- Google Search Central 的生成式搜索指南指出，生成式搜索仍以核心 Search 索引和质量系统为基础，RAG 和 query fan-out 会从可索引网页中获取信息。
- 同一指南明确：GEO/AEO 对 Google 来说仍是搜索体验优化，重点仍是基础 SEO、可抓取、清晰技术结构、独特且对人有用的内容。
- Google structured data 文档说明，结构化数据能给页面含义提供明确线索，推荐 JSON-LD。
- Google Article structured data 指南建议文章提供 headline、image、datePublished、dateModified、author 等适用字段。
- Google canonical 文档说明 canonical、redirect、sitemap 等信号可叠加，帮助确认首选 URL。
- llms.txt 目前是社区标准化提案，适合作为 LLM/agent 友好入口，但不能替代 sitemap/canonical/HTML。

## Pola 真经现状

已具备：

- 文章 canonical/shortlink。
- 文章 OG/Twitter meta。
- 微信 JS-SDK 分享配置。
- 动态 sitemap.xml。
- 动态 llms.txt。

缺口：

- 微信和通用社交共用一张 300x300 图片，通用卡片展示不够理想。
- 普通用户没有显眼的复制短链按钮。
- 文章详情 JSON-LD 仍是单一 Article，不足以表达站点、作者、网页、面包屑关系。
- 文章列表页缺少 ItemList。
- 缺少动态 RSS/JSON feed。
- robots.txt 只有静态简单版本，缺少 admin 禁止和动态兜底。

## 本轮优化项

| 方向 | 实现 |
| --- | --- |
| 分享卡片 | 生成 wechat 300x300 与 og 1200x630 两张 JPEG |
| 短链使用 | 文章页公开复制短链按钮 |
| 结构化数据 | Article/WebPage/WebSite/Person/Organization/BreadcrumbList `@graph` |
| 列表结构 | `/articles` 输出 ItemList |
| 发现入口 | `/robots.txt`、`/sitemap.xml`、`/feed.xml`、`/articles.json`、`/llms.txt` |
| AI 友好 | llms.txt 增加站点身份、feeds、分享元数据契约、AI agent guidance |
| 验证 | wechat_share_harness、seo_geo_harness、pytest |

## 不做项

- 不批量生成“AI 搜索问题页”或关键词堆叠页。
- 不把短链放进 sitemap 作为主要索引 URL。
- 不用 llms.txt 伪装成 Google AI 搜索特殊入口。
- 不为了平台卡片把页面主要内容隐藏在 JS 中。
