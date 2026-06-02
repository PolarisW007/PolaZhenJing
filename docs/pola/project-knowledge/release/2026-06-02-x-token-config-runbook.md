# X token 生产配置 Runbook

> 仅供历史/已废弃方案参考：2026-06-02 已按用户要求去除 X API 对接，当前不再需要配置 `X_USER_ACCESS_TOKEN`，生产中的 `scripts/x_token_config.py` 已移除。

- 日期：2026-06-02
- 需求：PolaZhenJing 发布中心生产收口
- 范围：生产环境 `X_USER_ACCESS_TOKEN` 安全配置、X smoke 真实发帖前置检查

## 背景

当前发布中心的 X 真实发帖 smoke 已具备脚本和生产同步能力，但生产 `.env` 未配置 `X_USER_ACCESS_TOKEN`。为避免人工编辑 `.env` 时误输出 token 或破坏原配置，新增 `scripts/x_token_config.py` 作为受控配置入口。

## 操作步骤

1. 登录生产机并进入项目目录。

```bash
cd /PolaZhenjing
```

2. 检查当前 token 状态。

```bash
.venv/bin/python scripts/x_token_config.py --check --json
```

3. 写入 token。脚本使用隐藏输入，不回显 token，并在覆盖已有 `.env` 前创建备份。

```bash
.venv/bin/python scripts/x_token_config.py --json
```

4. 重启服务，使 Flask 配置重新加载。

```bash
sudo systemctl restart polazj.service
sudo systemctl is-active polazj.service
```

5. 执行真实 X smoke。

```bash
.venv/bin/python scripts/x_publish_smoke.py --post --yes --json
```

## 验收标准

- `x_token_config.py --check --json` 返回 `configured=true`。
- `polazj.service` 重启后为 `active`。
- `x_publish_smoke.py --post --yes --json` 返回 `posted=true`、`post_id`、`post_url`。
- 发布中心页面出现对应 X 发布成功记录。
- 钉钉需求更新表记录 smoke 结果、BrowserUse 截图路径和说明。

## 安全约束

- 任何日志、终端输出、文档、钉钉记录都不得包含 token 明文。
- `.env.bak.x-token-*` 仅保留在生产机本地，不提交 git。
- 没有真实 token 时不得使用占位 token 执行真实发帖。
