# PolaUUH 线上注册登录三方快捷入口测试报告

日期：2026-06-21

## 覆盖范围

- 登录页第三方快捷入口展示。
- 注册页第三方快捷入口展示。
- `next` 参数在 provider start 链接中的保留。
- 未配置授权参数时 provider start 路由安全返回登录页。

## 测试命令

```bash
.venv/bin/python -m py_compile app/auth.py app/__init__.py
.venv/bin/python -m pytest tests/test_polauuh_provider_entrypoints.py -q
.venv/bin/python -m pytest tests/test_polauuh_auth.py tests/test_polauuh_provider_entrypoints.py -q
```

## 本地结果

- 编译检查：通过。
- 新增 provider 入口测试：3 passed。
- PolaUUH 账号兼容测试：5 passed。

## 线上验证

- 部署目标：`/PolaZhenjing`，由 Nginx 对外承载 `/PolaUUH/admin/*`。
- 服务状态：`polazj.service` 重启后 active。
- 服务器端 Flask test client：
  - `/admin/login?next=...`：200，五个平台标签全部存在。
  - `/admin/register?next=...`：200，五个平台标签全部存在。
- 公网验证：
  - `https://aipd.me/PolaUUH/admin/login?next=...`：200，微信、支付宝、Google、Apple、华为标签和 start 链接全部存在。
  - `https://aipd.me/PolaUUH/admin/register?next=...`：200，微信、支付宝、Google、Apple、华为标签和 start 链接全部存在。
  - `https://aipd.me/PolaUUH/admin/auth/wechat/start?next=...`：302，回到登录页，未出现 500。

## 结论

通过。线上注册页和登录页均已支持三方快捷验证入口展示；未配置完整平台授权参数时按安全兜底处理，不影响原有密码登录、邮箱注册和 SSO 回跳。
