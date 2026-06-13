# 需求记录：分享卡片与 GEO 强化

日期：2026-06-12

## 原始需求

用户连续确认：

1. 多平台发布是否已经实现。
2. 微信朋友圈和聊天仍然只显示链接，需要真正支持摘要卡片。
3. 生成链接仍然看着很长，需要短链接便于搜索引擎检索和人使用。
4. 整个 Pola 真经需要做 GEO，优化生成式搜索和 AI 引擎可读性。
5. 按 `pola-a2a-usage` 规范执行，并提供过程 harness。

## 现状确认

- 多平台发布：已有微信公众号官方 API 草稿/发布、X 手动发布包、小红书手动发布包；用户已明确不实现小红书自动 API。
- 短链：已有 `/s/<code>`，示例文章短链为 `https://aipd.me/s/49c0c4e8`。
- 微信卡片：HTML/JS-SDK 已有，但线上封面 URL 为 `.png`，实际文件内容是 JPEG，nginx 返回 `image/png`，且图片 1280x720、约 488KB，微信可能退化为裸链接。
- GEO：已有静态 `llms.txt`、`sitemap.xml`、OG/Twitter/JSON-LD 基础，但 sitemap 未列具体文章，`llms.txt` 不随服务器 `_posts` 自动更新。

## 目标

- 为微信/朋友圈分享提供真实 JPEG、300x300、较小体积的分享缩略图。
- 保留短链，页面显式输出 `rel=shortlink`。
- 动态生成文章级 sitemap 和 llms.txt，覆盖服务器现有 `_posts`。
- 保持旧长链和后台链接兼容。
- 用 harness 证明页面、短链、微信配置、GEO 文件都满足要求。

## 非目标

- 不保证用户手动把 URL 粘贴进微信文本框一定转卡片；微信客户端可能只在“网页内分享菜单”或平台抓取成功时生成卡片。
- 不接入小红书/即刻官方自动发布 API。
- 不做短链点击统计。
- 不做外部搜索引擎提交。

## 验收标准

- A1 文档：需求、PRD、SDD、开发日志、发布记录、测试报告更新。
- A2 多平台现状：发布中心能力清单和限制被记录，避免误以为全平台自动 API 已完成。
- A3 微信卡片图：`og:image` 和微信 `imgUrl` 指向 `.jpg`，响应 `Content-Type: image/jpeg`，尺寸 300x300。
- A4 短链：示例文章短链继续 200，页面包含 `rel=shortlink`。
- A5 微信 JS-SDK：云端 share-config 对短链返回 `configured=true`。
- A6 GEO：`/sitemap.xml` 动态列出具体文章 canonical URL；`/llms.txt` 动态列出站点说明、关键入口和最近文章。
- A7 结构化数据：文章 HTML 包含 robots、canonical、shortlink、OG、Twitter、itemprop、Article JSON-LD 日期/关键词。
- A8 Harness：`scripts/wechat_share_harness.py`、`scripts/seo_geo_harness.py`、pytest、py_compile 通过。
- A9 部署：nginx 将 `/sitemap.xml` 和 `/llms.txt` 代理给 Flask 动态路由，发布后 curl 验证。
