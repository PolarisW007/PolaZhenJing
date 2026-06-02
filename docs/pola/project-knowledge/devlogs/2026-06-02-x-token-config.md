# X token 配置工具开发日志

- 日期：2026-06-02
- 需求：PolaZhenJing 发布中心生产收口
- 状态：开发中，等待真实 `X_USER_ACCESS_TOKEN`

## 改动目标

把最后的生产收口阻塞点从“需要人工编辑 `.env`”降低为“运维按 runbook 安全写入 token 后执行 smoke”。新增工具必须避免 token 明文进入终端输出、文档、git diff 或钉钉记录。

## 改动文件

- `scripts/x_token_config.py`
- `docs/pola/project-knowledge/release/2026-06-02-x-token-config-runbook.md`
- `docs/pola/project-knowledge/test-reports/2026-06-02-x-token-config-test.md`
- `docs/pola/project-knowledge/devlogs/2026-06-02-x-token-config.md`

## 验证

- `.venv/bin/python -m py_compile scripts/x_token_config.py`
- 临时 env 文件执行 `--check --json`，确认空配置返回 `configured=false`。
- 通过 stdin 执行 `--dry-run --json`，确认只输出计划操作，不写文件。
- 通过 stdin 写入临时 env，确认返回 `updated=true`、`configured=true`。
- 覆盖已有 token 场景确认创建 `.bak.x-token-*` 备份。
- 验证输出仅包含 key、状态、备份路径，不包含 token 明文。
- `rsync -av scripts/x_token_config.py pola-server:/PolaZhenjing/scripts/x_token_config.py`
- 生产执行 `py_compile` 通过。
- 生产执行 `x_token_config.py --check --json` 返回 `configured=false`。
- 生产 `polazj.service` 为 `active`。

## 风险和后续

- 当前没有真实 X token，不能执行 `x_publish_smoke.py --post --yes`。
- token 配置完成后，需要重启 `polazj.service` 并记录真实 `post_id/post_url`。
- 真实发帖完成前，钉钉需求状态应继续保持 `开发中`。
