# X token 配置工具测试记录

> 仅供历史/已废弃方案参考：2026-06-02 已按用户要求去除 X API 对接，当前不再需要配置 `X_USER_ACCESS_TOKEN`。

- 日期：2026-06-02
- 需求：PolaZhenJing 发布中心生产收口
- 对象：`scripts/x_token_config.py`

## 验证目标

- 支持只读检查 token 是否已配置。
- 支持通过 stdin 或隐藏输入写入 token。
- 写入时不打印 token 明文。
- 覆盖已有 `.env` 前创建备份。
- 生产同步后可在生产机执行只读检查。

## 本地验证

已执行：

```bash
.venv/bin/python -m py_compile scripts/x_token_config.py
tmp_env="$(mktemp)"
.venv/bin/python scripts/x_token_config.py --env-file "$tmp_env" --check --json
printf '%s' "$DUMMY_X_TOKEN" | .venv/bin/python scripts/x_token_config.py --env-file "$tmp_env" --stdin --dry-run --json
printf '%s' "$DUMMY_X_TOKEN" | .venv/bin/python scripts/x_token_config.py --env-file "$tmp_env" --stdin --json
.venv/bin/python scripts/x_token_config.py --env-file "$tmp_env" --check --json
```

结果：

- `py_compile` 通过。
- 空 env 检查返回 `configured=false`。
- `--dry-run` 返回 `would_configure=true` 且不写文件。
- stdin 写入返回 `updated=true`、`configured=true`。
- 再次检查返回 `configured=true`。
- 覆盖已有 token 时创建 `.bak.x-token-*` 备份。
- 终端输出未包含 token 明文。

## 生产验证

已执行：

```bash
rsync -av scripts/x_token_config.py pola-server:/PolaZhenjing/scripts/x_token_config.py
ssh pola-server 'cd /PolaZhenjing && .venv/bin/python -m py_compile scripts/x_token_config.py && .venv/bin/python scripts/x_token_config.py --check --json'
```

结果：

- `scripts/x_token_config.py` 已同步到 `/PolaZhenjing/scripts/x_token_config.py`。
- 生产 `py_compile` 通过。
- 生产只读检查返回 `configured=false`，确认仍未配置真实 X token。
- `polazj.service` 状态为 `active`。

## 结论

本地工具链可用。生产环境仍需配置真实 `X_USER_ACCESS_TOKEN` 后执行真实 X smoke。
