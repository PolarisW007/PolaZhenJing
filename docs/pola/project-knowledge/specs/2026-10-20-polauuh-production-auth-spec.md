# SPEC: PolaUUH 多身份登录生产行为

日期：2026-10-20

## 页面与路径

- 登录：`GET|POST /admin/login`
- 注册：`GET|POST /admin/register`
- OTP：`POST /admin/auth/otp/send`、`POST /admin/auth/otp/verify`
- Provider：`GET /admin/auth/<provider>/start`、`GET|POST /admin/auth/<provider>/callback`
- 身份管理：`POST /admin/account/identities/<provider>/unlink`
- 联系方式：`POST /admin/account/contacts/<id>/unlink`
- 线上经 Nginx `X-Script-Name=/PolaUUH` 暴露，标准回调为 `https://aipd.me/PolaUUH/admin/auth/<provider>/callback`。

## Provider 状态

- `enabled=false`：页面显示“未启用”，发起接口返回 `provider_disabled`。
- `enabled=true` 但必要配置不完整：页面显示“配置不完整”，发起接口返回 `provider_not_configured`。
- `enabled=true` 且配置完整：生成带 state 的官方授权 URL；OIDC 同时生成 nonce。
- callback 只接受同一浏览器 session 中未过期、未消费的 state/nonce。

## 账号创建与绑定

- 已存在 `(provider, provider_subject)`：登录该身份所属用户。
- 登录状态下 `mode=bind`：绑定到当前用户；已绑定其它用户则冲突。
- 未登录且 provider 返回已验证邮箱：邮箱未占用时创建账号；已占用时返回 `identity_conflict`，不自动合并。
- provider 未返回可信邮箱：创建内部占位邮箱账号，并将密码登录标记为不可用。
- 用户至少保留一种真实可用登录方式；不可用的随机密码不计入解绑保护。

## OTP

- 邮箱验证码：由显式配置的 SMTP 或 Aliyun DirectMail 投递。
- 短信验证码：顺序固定为 `Aliyun Captcha -> 频控 -> 生成 -> 短信投递`。
- 生产投递失败返回 `delivery_failed`，并使本次验证码不可消费。
- 发送频控至少包含同目标冷却和同 IP 小时上限；错误尝试达到上限后阻断。
- 测试环境可返回 `debug_code`，生产响应不得包含验证码。

## 错误契约

| 错误 | HTTP | 说明 |
| --- | --- | --- |
| `invalid_request` | 400 | 参数或联系方式无效 |
| `rate_limited` | 429 | 目标或 IP 发送过于频繁 |
| `delivery_failed` | 503 | 邮件或短信未投递 |
| `captcha_required` | 400 | 短信缺少真人验证 |
| `captcha_not_configured` | 503 | Captcha 配置不完整 |
| `provider_disabled` | 404 | Provider 未启用 |
| `provider_not_configured` | 503 | Provider 必要配置不完整 |
| `provider_network_error` | 502 | Provider 网络或返回异常 |
| `provider_callback_invalid` | 400 | state、nonce、code 或 token 无效 |
| `identity_conflict` | 409 | 第三方身份或可信邮箱与已有账号冲突 |
| `last_login_method` | 400 | 解绑后将没有真实登录方式 |

## 配置

Secret 只进入权限为 `0600` 的生产环境文件。五个平台各自使用 `POLAUUH_<PROVIDER>_ENABLED` 和 client/app/key 配置；回调 URI必须与上述线上标准回调完全一致。Aliyun 邮件、Captcha 和短信共享受保护 AccessKey，但各自仍需产品侧发送地址、Scene、签名和模板配置。

## 兼容性

- `/PolaUUH/admin/api/sso/check` 响应保留旧字段，只追加 `contacts`、`identity_providers`。
- 原密码用户默认 `password_enabled=1`；新 OTP/provider 用户为 `0`，设置密码后转为 `1`。
- 原头像处理、资料编辑、权限审批和文章后台不改变。
