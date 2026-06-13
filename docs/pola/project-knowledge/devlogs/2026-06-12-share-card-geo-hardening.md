# 开发日志：分享卡片与 GEO 强化

日期：2026-06-12

## 目标

回答并推进用户 4 个问题：

1. 多平台发布现状是否完成。
2. 微信聊天/朋友圈仍为裸链接，需要卡片化。
3. 链接太长，需要短链接。
4. Pola 真经整体做 GEO，并提供过程 harness。

## 现状结论

- 多平台发布：微信公众号官方 API 能力、X 手动发布包、小红书手动发布包已存在；小红书自动 API 不在当前实现范围。
- 短链：已存在 `/s/<code>`，用户示例文章短链 `https://aipd.me/s/49c0c4e8`。
- 微信裸链接根因：线上 `og:image` 指向 `.png` URL，但实际文件为 JPEG，nginx 返回 `image/png`，同时图片 1280x720、487877 bytes，容易导致微信抓取缩略图失败并退化为裸链接。
- GEO：已有静态基础，但 sitemap 未列具体文章，llms.txt 不随服务器 `_posts` 动态更新。

## 改动

- `.gitignore`
  - 忽略 `assets/images/share/` 运行时分享缩略图缓存。
- `app/uploader.py`
  - 新增本地资产解析与分享缩略图生成。
  - 文章渲染时将 `og:image` / 微信 `imgUrl` 指向 300x300 JPEG 缩略图。
  - 新增动态 `/sitemap.xml`，列出根入口、文章列表和具体文章 canonical URL。
  - 新增动态 `/llms.txt`，输出站点说明、关键入口、最近文章 canonical/shortlink/summary/keywords。
  - 补文章关键词、发布时间、修改时间数据。
- `app/templates/article_view.html`
  - 补 `robots`、`keywords`、`rel=shortlink`。
  - 补 `og:image:type/width/height`、`twitter:image:alt`。
  - JSON-LD Article 增加 `sameAs`、`datePublished`、`dateModified`、`keywords`。
- `scripts/wechat_share_harness.py`
  - 断言分享图为 `/assets/images/share/*.jpg`。
- `scripts/seo_geo_harness.py`
  - 增加 Flask 动态文章、短链、sitemap、llms.txt 检查。
- `tests/test_social_publish.py`
  - 增加分享图 MIME/尺寸 meta 断言。

## 本地验证

- `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py scripts/seo_geo_harness.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：14 passed。
- `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py`：通过，本地微信取票因 IP 白名单降级为 `wechat-api-error`。
- `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests -q`：39 passed。

## 云端部署与验证

- 精确同步代码、模板、测试、harness 和文档到 `/PolaZhenjing`，未同步服务器 `_posts`。
- nginx 配置备份：`/opt/backups/polazj-nginx-geo-dynamic-20260612113306.conf`。
- nginx 已将 `/sitemap.xml`、`/llms.txt` 代理到 Flask 动态路由；`nginx -t` 通过并已 reload。
- `polazj.service` 已重启并保持 active。
- 云端 `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py scripts/seo_geo_harness.py`：通过。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：14 passed。
- 云端 `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py`：通过，示例短链 `https://aipd.me/s/49c0c4e8`，分享图 `https://aipd.me/PolaZhenjing/assets/images/share/2026-06-10-fde-databricks-snowflake-20260610-49c0c4e8.jpg`。
- 云端 `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`：通过，输出 `{"ok": true, "error_count": 0}`。
- 线上短链页已包含 `canonical`、`shortlink`、`og:url=https://aipd.me/s/49c0c4e8`、`og:image:type=image/jpeg`、`og:image:width=300`、`og:image:height=300`。
- 分享缩略图 HTTP 头：`200 OK`、`Content-Type: image/jpeg`、`Content-Length: 26353`。
- 线上 `/sitemap.xml` 已包含 `https://aipd.me/articles/fde-databricks-snowflake-20260610.md`。
- 线上 `/llms.txt` 已包含 Article Index、示例文章 canonical 和 shortlink。
- 线上微信 share-config 对 `https://aipd.me/s/49c0c4e8` 返回 `configured=true`。

## 发布注意

- nginx 需要将 `/sitemap.xml` 和 `/llms.txt` 从静态文件改为代理到 Flask 动态路由。
- 部署不覆盖服务器 `_posts`。
- 发布后必须验证微信卡片图 URL 为 `.jpg` 且 `Content-Type: image/jpeg`。

## Commit 状态

待提交：短链/分享卡片/GEO 强化、harness 和交付文档。
