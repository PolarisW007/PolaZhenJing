# 发布记录：分享卡片与 GEO 强化

日期：2026-06-12

## 发布范围

- `.gitignore`
- `app/uploader.py`
- `app/templates/article_view.html`
- `tests/test_social_publish.py`
- `scripts/wechat_share_harness.py`
- `scripts/seo_geo_harness.py`
- `docs/pola/arch-reference.md`
- `docs/pola/project-knowledge/requirements/2026-06-11-short-link-share-cards.md`
- `docs/pola/project-knowledge/specs/2026-06-11-short-link-share-cards-prd.md`
- `docs/pola/project-knowledge/architecture/2026-06-11-short-link-share-cards-sdd.md`
- `docs/pola/project-knowledge/devlogs/2026-06-11-short-link-share-cards.md`
- `docs/pola/project-knowledge/release/2026-06-11-short-link-share-cards-deploy.md`
- `docs/pola/project-knowledge/requirements/2026-06-12-share-card-geo-hardening.md`
- `docs/pola/project-knowledge/specs/2026-06-12-share-card-geo-hardening-prd.md`
- `docs/pola/project-knowledge/architecture/2026-06-12-share-card-geo-hardening-sdd.md`
- `docs/pola/project-knowledge/devlogs/2026-06-12-share-card-geo-hardening.md`
- `docs/pola/project-knowledge/test-reports/2026-06-12-share-card-geo-hardening-test.md`
- `docs/pola/project-knowledge/release/2026-06-12-share-card-geo-hardening-deploy.md`
- 服务器 nginx：`/etc/nginx/conf.d/polazj.conf`

## 部署方式

- 精确 `rsync` 代码、模板、测试、脚本和文档，不同步 `_posts`。
- nginx 备份后，将 `/sitemap.xml`、`/llms.txt` 代理给 Flask 动态路由。
- `nginx -t` 后 reload nginx。
- 重启 `polazj.service`。

## 本地发布前验证

- `py_compile`：通过。
- `tests/test_social_publish.py`：14 passed。
- `scripts/wechat_share_harness.py`：通过。
- `scripts/seo_geo_harness.py`：通过。
- 全量 `tests`：39 passed。

## 发布后验证

- nginx 备份：`/opt/backups/polazj-nginx-geo-dynamic-20260612113306.conf`。
- `nginx -t`：通过；nginx 已 reload。
- `polazj.service`：已 restart，服务 active。
- 云端 `py_compile`：通过。
- 云端 `tests/test_social_publish.py`：14 passed。
- 云端 `scripts/wechat_share_harness.py`：通过，示例文章短链 `https://aipd.me/s/49c0c4e8`，分享图为 `/assets/images/share/*.jpg`。
- 云端 `scripts/seo_geo_harness.py`：通过，输出 `{"ok": true, "error_count": 0}`。
- `https://aipd.me/s/49c0c4e8`：包含 canonical、shortlink、`og:url` 短链、300x300 JPEG 分享图 meta 和微信分享脚本配置。
- 分享缩略图：`200 OK`、`Content-Type: image/jpeg`、`Content-Length: 26353`。
- `https://aipd.me/sitemap.xml`：动态返回并包含具体文章 URL。
- `https://aipd.me/llms.txt`：动态返回并包含 Article Index、canonical、shortlink。
- 微信 share-config：对 `https://aipd.me/s/49c0c4e8` 返回 `configured=true`。

## 回滚

- 恢复 nginx 备份，`/sitemap.xml`、`/llms.txt` 回到静态文件。
- 回滚代码/模板/脚本并重启 `polazj.service`。
- 可删除 `assets/images/share/` 缩略图缓存。
