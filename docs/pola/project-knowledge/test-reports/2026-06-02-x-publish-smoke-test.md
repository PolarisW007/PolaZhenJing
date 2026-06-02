# PolaZhenJing X 真实发帖 Smoke 测试报告

> 仅供历史/已废弃方案参考：2026-06-02 已按用户要求去除 X API 对接，当前 X 改为内容生成 + 手动发布模式，本测试不再作为当前上线验收口径。

## 目标

为需求 `XhcYwKVYha` 的 A2 “配置 `X_USER_ACCESS_TOKEN` 后完成一篇真实 X 发帖并记录 post id”补齐可执行 smoke 入口。

## 命令

```bash
.venv/bin/python -m py_compile scripts/x_publish_smoke.py
.venv/bin/python scripts/x_publish_smoke.py --json
.venv/bin/python scripts/x_publish_smoke.py --json --require-token
PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q
```

真实发帖命令仅在生产 token 配置后执行：

```bash
.venv/bin/python scripts/x_publish_smoke.py --filename <article.md> --post --yes --json
```

## 预期

- 无 token 时 dry-run 成功输出待发文章、X 文案长度和缺失项，不调用 X API。
- `--require-token` 在缺 token 时返回非零，作为生产发帖门禁。
- token 配置后，`--post --yes` 真实调用 X API，成功后输出 `post_id` 和 `post_url` 并写入 `social_publications`。

## 实际结果

- `.venv/bin/python -m py_compile scripts/x_publish_smoke.py`：通过。
- `.venv/bin/python scripts/x_publish_smoke.py --json`：退出码 `0`，选取文章 `2026-05-24-yi-ge-ren-you-zheng-zhi-you-jia-20260524.md`，生成 X 文案长度 `278`，`configured=false`，`blocked_by=["X_USER_ACCESS_TOKEN"]`，未真实发帖。
- `.venv/bin/python scripts/x_publish_smoke.py --json --require-token`：退出码 `2`，作为缺 token 的生产发帖门禁。
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：10 passed。
- 真实发帖未执行，因为当前本地和已记录的生产配置均缺少 `X_USER_ACCESS_TOKEN`。
- 生产服务器 follow-up：
  - `ssh pola-server 'cd /PolaZhenjing && .venv/bin/python -m py_compile scripts/x_publish_smoke.py'`：通过。
  - 远端 `.venv/bin/python scripts/x_publish_smoke.py --json`：退出码 `0`，`configured=false`，`blocked_by=["X_USER_ACCESS_TOKEN"]`，未真实发帖。
  - 远端 `.venv/bin/python scripts/x_publish_smoke.py --json --require-token`：退出码 `2`，确认生产 token 仍缺失且门禁生效。
