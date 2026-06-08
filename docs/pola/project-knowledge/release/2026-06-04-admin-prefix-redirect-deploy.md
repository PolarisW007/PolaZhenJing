# 发布记录：后台无前缀 URL 404 兼容修复

日期：2026-06-04

## 发布范围

- 服务器 nginx：`/etc/nginx/conf.d/polazj.conf`
- `tests/test_social_publish.py`
- `docs/pola/project-knowledge/devlogs/2026-06-04-admin-prefix-redirect.md`
- `docs/pola/project-knowledge/release/2026-06-04-admin-prefix-redirect-deploy.md`

## 部署方式

- 备份 nginx 配置后，在 `/PolaZhenjing/` 代理前增加 `/admin` 和 `/admin/*` 兼容重定向。
- 运行 `nginx -t` 后 reload nginx。
- 同步本次测试与交付记录到 `/PolaZhenjing`。

## 发布后验证

- `nginx -t`：通过。
- `systemctl reload nginx`：完成。
- `systemctl is-active nginx`：`active`。
- `systemctl is-active polazj.service`：`active`。
- 本地 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：12 passed。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：12 passed。
- `https://aipd.me/admin/upload`：302 到 `https://aipd.me/PolaZhenjing/admin/upload`。
- `https://aipd.me/admin/articles/claude-code-claude-md-20260531.md/edit`：302 到 `https://aipd.me/PolaZhenjing/admin/articles/claude-code-claude-md-20260531.md/edit`。
- `https://aipd.me/PolaZhenjing/admin/upload`：302 到 `/PolaZhenjing/admin/login`，主路径仍进入 Flask。

## 回滚

- 恢复 nginx 备份配置并 reload nginx。
- 该修复不涉及数据库迁移。
