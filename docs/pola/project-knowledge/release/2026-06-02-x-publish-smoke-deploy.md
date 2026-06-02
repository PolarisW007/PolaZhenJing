# 发布记录：X 真实发帖 smoke 门禁

日期：2026-06-02

## 发布范围

- `scripts/x_publish_smoke.py`
- `docs/pola/project-knowledge/test-reports/2026-06-02-x-publish-smoke-test.md`
- `docs/pola/project-knowledge/devlogs/2026-06-02-x-publish-smoke.md`

## 部署方式

- 服务器：`/PolaZhenjing`
- 方式：精确 `rsync` 新增 smoke 脚本，不触碰上传页、文章、auth 或其他生产工作树改动。
- 服务：无需重启 `polazj.service`；脚本为手工 smoke/门禁入口。

## 发布后验证

- `systemctl is-active polazj.service`：`active`。
- 生产配置只读检查：`WECHAT_MP_APP_ID` 和 `WECHAT_MP_APP_SECRET` 已配置；`X_USER_ACCESS_TOKEN` 未配置。
- 远端 `.venv/bin/python -m py_compile scripts/x_publish_smoke.py`：通过。
- 远端 `.venv/bin/python scripts/x_publish_smoke.py --json`：退出码 `0`，生成待发文案，未真实发帖。
- 远端 `.venv/bin/python scripts/x_publish_smoke.py --json --require-token`：退出码 `2`，确认缺 token 时阻断真实发帖。

## 后续真实发帖命令

生产 `X_USER_ACCESS_TOKEN` 配置完成后执行：

```bash
cd /PolaZhenjing
.venv/bin/python scripts/x_publish_smoke.py --post --yes --json
```

成功后将输出 `post_id` 和 `post_url`，并写入 `social_publications`。

## 回滚

```bash
rm -f /PolaZhenjing/scripts/x_publish_smoke.py
```

该脚本未注册路由，不影响发布中心 Web UI。
