# 需求：分享卡片资产与 GEO v2

日期：2026-06-13

## 用户原始需求

1. 需要分享卡片功能，按照建议写 PRD、SDD、SPEC，并使用 Pola A2A 规范实现功能，需要自我校验和报告。
2. 文章详情页需要增加分享链接按钮，点击后复制文章生成的短链接，支持用户点进来看。
3. GEO 还有很大提升空间，需要详细研究、细化并实现。
4. 完成后更新开发日志，并提供 harness 过程。
5. 用户补充要求由 agent 自主完成云服务器版本，让手机端和 PC 端可通过线上短链获得可抓取分享卡片。

## 目标

- 将文章分享卡片从单一图片升级为平台化分享资产：
  - 微信聊天/朋友圈使用小体积 300x300 JPEG。
  - 即刻、X、通用网页抓取使用 1200x630 JPEG OG 图。
- 文章详情页为所有读者提供复制短链按钮，复制的是 `/s/<code>` 稳定短链接。
- 强化 Pola 真经的 GEO/SEO 基础：
  - 服务端 HTML 中输出完整可抓取 meta、JSON-LD、canonical/shortlink。
  - 动态输出 sitemap、robots、llms、RSS/JSON feed。
  - 文章列表输出 ItemList 结构化数据。
- 增加 harness，验证分享卡片、短链按钮、GEO 文件和结构化数据。

## 非目标

- 不接入微信、即刻、小红书、今日头条的官方发帖新 API。
- 不保证微信、即刻客户端一定立刻刷新旧缓存；本轮保证服务端输出和资源符合抓取要求。
- 不重写文章正文，不为了 GEO 批量生成低价值变体内容。
- 不承诺微信把“直接粘贴 URL 文本”强制转换为卡片；服务端保证短链页元数据正确，微信内通过右上角分享使用 JS-SDK 卡片配置。

## 验收标准

- A1：任一文章短链页 `/s/<code>` 返回 200，并输出 canonical 长链与 shortlink 短链。
- A2：`og:image` 指向 1200x630 的 `/assets/images/share/*-og.jpg`，并输出 `og:image:type=image/jpeg`、宽高 meta。
- A3：微信 JS-SDK 分享 payload 使用 `/assets/images/share/*-wechat.jpg`，尺寸 300x300。
- A4：文章详情页公开可见“复制短链接”按钮，点击复制 `https://aipd.me/s/<code>`。
- A5：管理员仍可看到微信/朋友圈、即刻、X、LinkedIn 辅助入口，普通读者不可见管理发布入口。
- A6：动态 `/sitemap.xml`、`/robots.txt`、`/llms.txt`、`/feed.xml`、`/articles.json` 可用。
- A7：文章页 JSON-LD 使用 `@graph`，包含 Article、WebPage、WebSite、Person、Organization、BreadcrumbList。
- A8：文章列表页输出 ItemList JSON-LD。
- A9：`scripts/wechat_share_harness.py`、`scripts/seo_geo_harness.py`、相关 pytest 通过。
- A10：短链页的微信 JS-SDK 配置接口必须使用公网 `/PolaZhenjing/admin/api/...` 前缀，避免 root `/s/<code>` 页面请求不存在的 `/admin/api/...`。
- A11：线上记录 `wx.ready`/`wx.error` 的非敏感诊断日志，便于区分签名失败、域名未授权、客户端缓存和用户操作路径问题。
- A12：云服务器部署后运行公网 harness，确认 meta、图片资源、微信签名配置、feed/robots/json 都可从 `https://aipd.me` 访问。

## 风险等级

P2。涉及公开文章主流程、分享卡片、搜索/AI 抓取入口和运行时图片缓存，但不改鉴权、数据库 schema 或生产密钥。

## 稳定性与安全边界

- 分享图片生成必须缓存到 `assets/images/share/`，避免每次请求重复处理。
- 生成失败时回退到原图 URL，不影响文章阅读。
- 不写入任何 token、cookie、secret。
- 不覆盖服务器 `_posts`。
- 生产部署已由用户明确授权；部署时不得覆盖服务器 `_posts`、运行时图片和密钥文件。
