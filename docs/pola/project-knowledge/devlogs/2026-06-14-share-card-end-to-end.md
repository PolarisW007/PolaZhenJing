# Devlog: End-to-End Share Card Experience

## Goal

实现文章分享到微信和即刻时的稳定图文展示能力，减少裸 URL 分享。

## Planned Changes

- 新增轻量卡片页 `/c/<code>`。
- 文章页分享按钮改为卡片链接、阅读短链、微信图文卡片三类入口。
- 增加客户端 Canvas 图文卡片复制/下载 fallback。
- 更新 tests 和 harness。

## Verification

- 待执行。

## Risk

- 微信 PC 直接粘贴 URL 的展示仍由微信客户端决定；本次通过图文卡片 fallback 提供可控可见展示。
- Canvas 图片剪贴板受浏览器能力限制，必须保留下载 fallback。
