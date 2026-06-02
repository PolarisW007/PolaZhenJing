# X 手动发布模式生产同步记录

- 日期：2026-06-02
- 需求池记录：`XhcYwKVYha`
- 目标：去除 X API 对接，改为 X 内容生成 + 手动发布

## 同步内容

- `app/social_publish.py`
- `app/templates/social_publish_article.html`
- `docs/pola/project-knowledge/requirements/2026-06-02-x-manual-publishing.md`
- `docs/pola/project-knowledge/specs/2026-06-02-x-manual-publishing-prd.md`
- `docs/pola/project-knowledge/architecture/2026-06-02-x-manual-publishing-sdd.md`
- `docs/pola/project-knowledge/devlogs/2026-06-02-x-manual-publishing.md`
- `docs/pola/project-knowledge/test-reports/2026-06-02-x-manual-publishing-test.md`

## 移除内容

- 生产删除 `scripts/x_publish_smoke.py`
- 生产删除 `scripts/x_token_config.py`

## 验证

- 生产 `app/social_publish.py`：`py_compile` 通过。
- `polazj.service`：重启后 `active`。
- `http://127.0.0.1:5000/admin/social/`：未登录返回 `302`。
- `http://127.0.0.1:5000/admin/login`：返回 `200`。
- 生产脚本检查：`x_publish_smoke.py`、`x_token_config.py` 均已移除。

## 截图证据

- 本地浏览器截图：`.qa-artifacts/x-manual-publishing/x-manual-package-local.png`
- 说明：截图展示 X 卡片已改为手动发布包，包含“生成发布包”和 X 发布框链接；页面不再显示 token 缺失提示或自动发帖入口。

## 回滚

如需回滚，可恢复备份目录 `/opt/backups/polazj-x-manual-*` 中的 `app/social_publish.py` 和 `app/templates/social_publish_article.html`，并重启 `polazj.service`。不建议恢复 X API/token 脚本，除非重新确认 X API 方案。
