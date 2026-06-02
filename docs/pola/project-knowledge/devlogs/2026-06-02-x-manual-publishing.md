# X 手动发布模式开发日志

- 日期：2026-06-02
- 需求池记录：`XhcYwKVYha`
- 状态：已实现并同步生产，待钉钉回写

## 改动目标

按用户新要求去除 X API 对接和 token 依赖，将 X 改为内容生成后人工发布。完成后 `X_USER_ACCESS_TOKEN` 不再是需求上线 blocker。

## 计划改动文件

- `app/social_publish.py`
- `app/templates/social_publish_article.html`
- `tests/test_social_publish.py`
- `docs/pola/project-knowledge/requirements/2026-06-02-x-manual-publishing.md`
- `docs/pola/project-knowledge/specs/2026-06-02-x-manual-publishing-prd.md`
- `docs/pola/project-knowledge/architecture/2026-06-02-x-manual-publishing-sdd.md`
- `docs/pola/project-knowledge/test-reports/2026-06-02-x-manual-publishing-test.md`

## 验证

- `.venv/bin/python -m py_compile app/social_publish.py`
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：11 passed。
- 残留扫描确认应用代码和脚本中不再包含 `X_USER_ACCESS_TOKEN`、`api.x.com`、`x_post` 自动发帖入口或 X token 配置函数；测试文件仅保留 `X_USER_ACCESS_TOKEN` 作为页面负向断言。
- 本地 Playwright 浏览器截图：`.qa-artifacts/x-manual-publishing/x-manual-package-local.png`；断言 X 卡片出现手动发布包入口和 `https://x.com/compose/post`，不出现 token 文案和自动发帖入口。
- 生产同步后验证：`polazj.service=active`；`/admin/social/` 未登录 `302`；`/admin/login` 为 `200`；生产 `scripts/x_publish_smoke.py` 和 `scripts/x_token_config.py` 已移除。

## 结果

- X 平台 `mode` 改为 `manual_package`。
- `build_manual_package(ctx, "x")` 生成 280 字内 X 文案、封面提示、打开 X 链接和手动发布 checklist。
- 发布详情页将 X 纳入通用手动发布包卡片，支持生成包和回填链接。
- 删除 `scripts/x_publish_smoke.py` 和 `scripts/x_token_config.py`，避免继续保留 API/token 收口入口。
- `X_USER_ACCESS_TOKEN` 不再是当前方案 blocker。
