# 开发日志：文章短链与社交分享卡片

日期：2026-06-11

## 目标

为公开文章生成短链，并让微信、朋友圈、即刻等平台分享时尽量展示标题、摘要、封面卡片，而不是只有裸 URL。

## 改动

- `app/uploader.py`
  - 新增 `_article_short_code()`，根据真实 Jekyll 文件名生成稳定 8 位短码。
  - 新增 `/s/<code>` 公开路由，短链直接渲染同一篇文章。
  - 新增公网 URL helper，确保后台前缀下渲染时分享链接仍为根域 `https://aipd.me/s/<code>`。
  - 文章渲染新增 `canonical_url`、`short_code`、`short_url`。
- `app/templates/article_view.html`
  - canonical 指向长文章 URL。
  - `og:url`、`twitter:url`、微信 JS-SDK `link`、复制链接使用短链。
  - 增加 `og:image:url`，保留 OG/Twitter/itemprop/Schema.org 元数据。
  - 后台分享区增加“复制短链”“微信/朋友圈”“即刻”入口。
- `tests/test_social_publish.py`
  - 新增短链路由、元数据和未知短码 404 测试。
- `scripts/wechat_share_harness.py`
  - 验证分享 URL 为 `/s/<code>`。
  - 验证短链页和长链页都暴露卡片元数据。
  - 本机微信票据接口因 IP 白名单失败时允许降级为 `configured=false`。
- `docs/pola/arch-reference.md`
  - 补充 `/s/<code>` 公开短链路由约束。

## 本地验证

- `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：14 passed。
- `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py`：通过。
  - 样例短链：`https://aipd.me/s/1dfba0e0`。
  - 本机微信接口返回 invalid ip，harness 按降级路径通过。

## 发布注意

- nginx 需要新增 `/s/` 代理到 `127.0.0.1:5000/s/`。
- 部署时不覆盖服务器 `_posts`，因为线上已有 2026-06-10 新文章，本地仓库未包含。
- 线上需验证用户给出的 `fde-databricks-snowflake-20260610.md` 可生成短链。

## 云端验证

- nginx 备份：`/opt/backups/polazj-nginx-short-link-20260611223106.conf`。
- 云端 `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py`：通过。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：14 passed。
- 云端 `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py`：通过。
- 用户示例文章短链：`https://aipd.me/s/49c0c4e8`。
- 线上短链 `https://aipd.me/s/49c0c4e8`：200。
- 线上长链 `https://aipd.me/articles/fde-databricks-snowflake-20260610.md`：200。
- 线上 HTML：canonical 为长链，`og:url` 和 `twitter:url` 为短链，`og:image` 为文章封面。
- 微信 JS-SDK 配置接口：`configured=true`，返回 `appId`、`nonceStr`、`signature`、`timestamp`。

## Commit 状态

待提交：短链、分享卡片、测试和交付文档。
