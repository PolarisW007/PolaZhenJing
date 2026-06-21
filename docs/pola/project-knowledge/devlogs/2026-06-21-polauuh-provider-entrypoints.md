# PolaUUH 线上注册登录三方快捷入口开发日志

日期：2026-06-21

## 风险等级

P2。改动影响线上登录/注册主流程，但仅新增入口展示和安全兜底路由，不修改数据库、Cookie、SSO 校验逻辑或生产密钥。

## 背景

排查发现线上 `https://aipd.me/PolaUUH/admin/*` 仍由 PolaZhenJing 旧账号中心提供服务；独立 PolaUUH 仓库的模板改动不会直接影响该线上地址。因此本次在 PolaZhenJing 的真实服务模板中补齐快捷入口。

## 改动

- `app/auth.py`：新增第三方 provider 列表、登录/注册模板上下文和安全兜底 start 路由。
- `app/templates/login.html`：新增微信、支付宝、Google、Apple、华为快捷验证登录入口。
- `app/templates/register.html`：新增同一组快捷登录 / 注册入口。
- `app/templates/base.html`：补充 provider 按钮和分割线样式。
- `tests/test_polauuh_provider_entrypoints.py`：覆盖登录页、注册页入口与 `next` 参数。

## 不影响功能使用验证路径

- 旧密码登录表单保留原字段和提交路径。
- 旧邮箱注册与邮箱验证码路径保留原字段和提交路径。
- 旧 `/admin/api/sso/check`、`/api/sso/check` 不在本次改动范围。
- 旧登录态 session 字段不变。

## 验证记录

- `.venv/bin/python -m py_compile app/auth.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_polauuh_provider_entrypoints.py -q`：3 passed。
- `.venv/bin/python -m pytest tests/test_polauuh_auth.py tests/test_polauuh_provider_entrypoints.py -q`：5 passed。
- 服务器 `/PolaZhenjing` Flask test client：
  - `/admin/login?...`：200，微信、支付宝、Google、Apple、华为全部存在。
  - `/admin/register?...`：200，微信、支付宝、Google、Apple、华为全部存在。
- 公网 `https://aipd.me/PolaUUH/admin/login?...`：200，五个平台入口与 `/PolaUUH/admin/auth/<provider>/start` 链接全部存在。
- 公网 `https://aipd.me/PolaUUH/admin/register?...`：200，五个平台入口与 `/PolaUUH/admin/auth/<provider>/start` 链接全部存在。
- 公网 `https://aipd.me/PolaUUH/admin/auth/wechat/start?...`：302 到 `/PolaUUH/admin/login?...`，未配置完整授权参数时安全降级。

## 安全记录

- 未写入、打印或提交任何第三方平台 secret。
- 提交前执行 `git diff --check` 与 diff secret 关键词人工检查。

## 钉钉同步

- 钉钉文档已创建：`https://alidocs.dingtalk.com/i/nodes/7dx2rn0JbYvRkOd6fZ7PlmybVMGjLRb3`
- AI 表格 `各项目迭代记录日志` / `开发日志` 已新增记录：`NUG506VWFM`。
