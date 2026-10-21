# Test Report: PolaUUH 多身份登录生产接入

日期：2026-10-21

状态：本地门禁通过，生产发布后补充线上证据。

## 结果

| 检查 | 结果 |
| --- | --- |
| Python 编译 | Pass |
| `python -m pytest -q` | 147 passed in 3.25s |
| `python scripts/polauuh_auth_harness.py` | Pass，11 checks，`ok=true` |
| Provider adapter 契约 | Google、Apple、微信、支付宝、华为 Pass |
| OTP/投递/身份/审计 | Pass |
| 旧密码、头像、权限与 SSO 回归 | Pass |

Harness 覆盖健康检查、登录/注册入口、密码注册登录、SSO、邮箱 OTP、手机号绑定、Google mock、identity payload、schema 和审计。测试使用临时 SQLite 和 mock provider，无真实 secret、短信或第三方 token。

## 风险用例

- 邮件/短信投递失败使验证码失效，不返回“已发送”。
- 目标和 IP 频控、最大尝试、单次消费。
- SMS 在 Captcha 之前不调用 provider。
- OIDC state/nonce/签名/issuer/audience/expiry；Apple `form_post` 临时 nonce cookie。
- OTP 与 OAuth state 的并发竞争只允许一个请求完成单次消费。
- 支付宝响应验签；Google 官方 issuer 兼容。
- 已验证邮箱和已绑定 subject 冲突不静默合并。
- provider 无邮箱时不创建可见 contact，随机密码不计登录方式。
- 解绑最后一种真实登录方式被阻止。
- provider 禁用、缺配置、网络/JSON 异常都有稳定错误码。

## 尚待线上证据

- 生产数据库副本迁移、canary、发布、浏览器桌面/手机回归和服务日志观察。
- Aliyun DirectMail 正式投递取决于 RAM DirectMail 权限。
- 五个平台真实授权取决于正式应用凭据；Google 另受当前生产出站限制。
- 短信需 Captcha Prefix/SceneId 和 SMS SignName/TemplateCode，当前应保持禁用。
