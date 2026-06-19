# SDD: End-to-End Share Card Implementation

## Architecture

```text
Article markdown
  -> _build_article_share_context()
       -> canonical URL / short URL / card URL
       -> 1200x630 OG image
       -> 300x300 WeChat image
  -> /s/<code> full article page
       -> reader UI + JS-SDK + diagnostics + share card canvas
  -> /c/<code> lightweight card page
       -> OG/Twitter meta only + open article CTA
```

## Data Flow

- `short_url`: `https://aipd.me/s/<code>`，保留阅读与微信 JS-SDK 链路。
- `share_card_url`: `https://aipd.me/c/<code>`，给即刻、X 和通用抓取器。
- `og_share_image`: 1200x630 JPEG，用于即刻/X/通用平台。
- `wechat_share_image`: 300x300 JPEG，用于微信 JS-SDK `imgUrl`。
- Canvas fallback：浏览器端读取 `og_share_image`、标题、摘要、短链，生成 PNG 图文卡。

## Safety

- 不引入新三方依赖。
- 不改动认证、secret、微信公众号凭据或服务器环境变量。
- 不改变文章正文渲染和历史短链路径。
- 生成卡片图片在客户端完成，不增加后台 CPU/磁盘压力。

## Verification

- Pytest 覆盖 `/s/<code>` 和 `/c/<code>`。
- Harness 校验轻量卡片页 meta、文章页按钮、图片链接。
- 云端 curl 验证卡片页、短链页、分享图响应。
