# 发布记录：文章短链与社交分享卡片

日期：2026-06-11

## 发布范围

- `app/uploader.py`
- `app/templates/article_view.html`
- `tests/test_social_publish.py`
- `scripts/wechat_share_harness.py`
- `docs/pola/arch-reference.md`
- `docs/pola/project-knowledge/requirements/2026-06-11-short-link-share-cards.md`
- `docs/pola/project-knowledge/specs/2026-06-11-short-link-share-cards-prd.md`
- `docs/pola/project-knowledge/architecture/2026-06-11-short-link-share-cards-sdd.md`
- `docs/pola/project-knowledge/devlogs/2026-06-11-short-link-share-cards.md`
- `docs/pola/project-knowledge/release/2026-06-11-short-link-share-cards-deploy.md`
- 服务器 nginx：`/etc/nginx/conf.d/polazj.conf`

## 部署方式

- 精确 `rsync` 本次代码、模板、测试、脚本和文档。
- nginx 备份后新增 `/s/` 代理。
- 运行 `nginx -t`，reload nginx。
- 重启 `polazj.service`。

## 发布前本地验证

- `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：14 passed。
- `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py`：通过。

## 发布后验证

- nginx 备份：`/opt/backups/polazj-nginx-short-link-20260611223106.conf`。
- `nginx -t`：通过。
- `systemctl is-active nginx`：`active`。
- `systemctl is-active polazj.service`：`active`。
- 云端 `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py`：通过。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：14 passed。
- 云端 `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py`：通过，示例文章 `fde-databricks-snowflake-20260610.md` 的 `og_url=https://aipd.me/s/49c0c4e8`。
- `https://aipd.me/s/49c0c4e8`：200。
- `https://aipd.me/articles/fde-databricks-snowflake-20260610.md`：200。
- 短链 HTML：`canonical=https://aipd.me/articles/fde-databricks-snowflake-20260610.md`，`og:url=https://aipd.me/s/49c0c4e8`，`twitter:url=https://aipd.me/s/49c0c4e8`，`og:image` 指向文章生成封面。
- 微信 JS-SDK 配置：`/PolaZhenjing/admin/api/wechat/share-config?url=https%3A%2F%2Faipd.me%2Fs%2F49c0c4e8` 返回 `configured=true`。

## 回滚

- 恢复 nginx 备份，移除 `/s/` 代理并 reload nginx。
- 回滚本次代码和模板，重启 `polazj.service`。
- 无数据库迁移。
