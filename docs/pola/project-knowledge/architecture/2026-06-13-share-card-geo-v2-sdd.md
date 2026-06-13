# SDD：分享卡片资产与 GEO v2

日期：2026-06-13

## 架构影响

| 模块 | 改动 | 风险 |
| --- | --- | --- |
| `app/uploader.py` | 分享图片预设、ShareMeta、动态 robots/feed/json、增强 sitemap/llms、JSON-LD 数据组装 | 中 |
| `app/templates/article_view.html` | 文章页 meta、JSON-LD、复制短链按钮、微信/OG 图分离、JS-SDK 诊断 | 中 |
| `app/templates/public_articles.html` | 列表页 head meta 与 ItemList JSON-LD | 低 |
| `scripts/wechat_share_harness.py` | 分享卡片和复制按钮自检 | 低 |
| `scripts/seo_geo_harness.py` | GEO 动态文件和结构化数据自检 | 低 |
| `tests/test_social_publish.py` | 回归测试更新 | 低 |
| `portal/robots.txt` | 静态 robots 兜底更新 | 低 |

## 数据流

```text
Markdown post
  -> _parse_post
  -> ShareMeta derivation
  -> share image generator
       -> assets/images/share/*-wechat.jpg
       -> assets/images/share/*-og.jpg
  -> article_view.html
       -> OG/Twitter/itemprop
       -> WECHAT_SHARE
       -> fixed public WeChat API endpoints
       -> wx.ready/wx.error diagnostics
       -> JSON-LD @graph
       -> copy shortlink button
  -> sitemap/feed/articles.json/llms
```

## 微信分享配置链路

```text
https://aipd.me/s/<code>
  -> fetch https://aipd.me/PolaZhenjing/admin/api/wechat/share-config?url=<current-page-url>
  -> backend signs the exact current page URL with JSAPI ticket
  -> wx.config
  -> wx.ready
       -> updateAppMessageShareData / updateTimelineShareData
       -> POST share-diagnostics status=ready
  -> wx.error or fetch failure
       -> POST share-diagnostics status=error/config-unavailable/fetch-error
```

- 固定公网 API 前缀是必要条件，因为 root 短链页不带 `/PolaZhenjing` 反向代理上下文，模板内相对 `url_for` 会生成不可用的 `/admin/api/...`。
- 诊断接口只记录 status、page、share、err、User-Agent，不记录 token、ticket、signature、cookie。

## 分享图片生成

- 图片生成在请求时懒加载。
- 以源图 mtime 判断是否重新生成。
- 生成目录已在 `.gitignore` 中忽略，避免提交运行时缓存。
- Pillow 不可用或源图不可读时回退原图 URL。

## GEO 方案依据

- Google 生成式搜索官方指南强调：AI 搜索仍依赖核心 Search 索引与质量系统，基础 SEO、可抓取结构、清晰技术结构和高质量内容仍是核心。
- Google Article 结构化数据指南建议提供 headline、image、datePublished、dateModified、author 等适用属性。
- Google canonical 指南建议 canonical、sitemap 等信号叠加，帮助搜索引擎理解首选 URL。
- llms.txt 是社区提案，不是 Google 生成式搜索的特殊排名要求；本项目将其作为 AI/agent 友好的辅助索引，不替代 canonical/sitemap/HTML。

## 回滚点

- 回滚 `app/uploader.py`、`article_view.html`、`public_articles.html`、harness/test。
- 删除 `assets/images/share/*-wechat.jpg` 和 `*-og.jpg` 缓存不会影响文章。
- 若部署后动态 robots/feed/json 有问题，可恢复旧 nginx/static 文件或仅代理 sitemap/llms。

## 测试策略

- Python 语法检查。
- 社交发布 pytest。
- 微信分享 harness。
- GEO harness。
- 全量 pytest。
- `git diff --check`。
- 线上 curl 验证短链页包含固定微信 API 前缀、`wx.error`、1200x630 OG 图、300x300 微信图。
- 线上调用 share-config 验证 `configured=true` 或可解释的降级原因。

## 发布策略

用户已明确要求完成云服务器版本。本轮按最小同步发布：

- 只同步本次相关代码、模板、harness、测试、文档和 robots 兜底。
- 不同步 `_posts`、`.env`、运行时生成图片和用户已有无关改动。
- 如 nginx 未代理 `/feed.xml`、`/articles.json`、`/robots.txt`，备份配置后增加只读公开入口代理。
- 发布后运行云端 pytest/harness 和公网 curl 验证；失败则回滚同步文件或恢复 nginx 备份。
