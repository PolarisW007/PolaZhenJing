# PolaZhenJing X 真实发帖 Smoke 入口开发日志

## 目标

继续推进需求池 `XhcYwKVYha`，在生产 `X_USER_ACCESS_TOKEN` 尚未配置前，补齐真实发帖的可执行验收脚本，确保 token 一旦配置即可一键完成 A2 并记录 post id。

## 改动文件

- `scripts/x_publish_smoke.py`
- `docs/pola/project-knowledge/test-reports/2026-06-02-x-publish-smoke-test.md`
- `docs/pola/project-knowledge/devlogs/2026-06-02-x-publish-smoke.md`

## 验证

- `.venv/bin/python -m py_compile scripts/x_publish_smoke.py`：通过。
- `.venv/bin/python scripts/x_publish_smoke.py --json`：退出码 `0`，dry-run 生成 X 文案长度 `278`，确认缺少 `X_USER_ACCESS_TOKEN` 且未真实发帖。
- `.venv/bin/python scripts/x_publish_smoke.py --json --require-token`：退出码 `2`，作为真实发帖前的 token 门禁。
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：10 passed。

## 风险

- 默认不真实发帖；必须显式传入 `--post --yes`。
- 脚本不输出 token 值，只输出是否配置。
- 当前若缺少 `X_USER_ACCESS_TOKEN`，A2 真实发帖仍是外部配置 blocker。

## Commit

待提交后回填。
