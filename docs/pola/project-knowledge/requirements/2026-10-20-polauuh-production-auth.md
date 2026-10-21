# Requirement: PolaUUH 多身份登录生产接入

日期：2026-10-20

## 原始需求

继续完成 PolaUUH 完整上线，使登录和注册支持微信、Apple、Google、支付宝、华为快捷登录，并保留邮箱验证码、手机号验证码、登录态、身份绑定和审计能力。完成代码、测试、Git 提交、生产发布和线上验证；确需平台配置时给出最小补充清单。

## 当前事实

- `https://aipd.me/PolaUUH/admin/*` 仍由 `/PolaZhenjing` 的 `polazj.service` 提供，不由独立 PolaUUH 进程提供。
- 生产账号模块现有五个平台按钮，但 `/admin/auth/<provider>/start` 只是占位回跳。
- 独立 PolaUUH 仓库已有 identity、OTP、Captcha、OAuth/OIDC adapter 和 SQLite 迁移实现。
- 生产用户、会话、头像和权限均在 PolaZhenJing 现有 SQLite 与 Flask session 中；不能直接切换服务或数据库。
- 生产尚无五个平台所需的 `POLAUUH_*` 应用凭据；公众号 `WECHAT_MP_*` 不能替代微信开放平台网站应用凭据。

## 目标与范围

- 在现有 `polazj.service` 内合入统一 identity 能力，不切服务端口、数据库文件、Cookie 域或 Nginx `/PolaUUH` 路由。
- 支持邮箱验证码注册/登录，手机号验证码在 Aliyun Captcha 后调用可配置短信 adapter。
- 支持 Google、Apple、微信、支付宝、华为真实授权发起、回调校验、身份创建/绑定和审计。
- 新增 `user_contacts`、`user_identities`、`verification_codes`、`auth_requests`、`auth_audit_logs`，并兼容扩展 `users`。
- 保留密码登录、旧注册验证、头像上传、资料设置、权限管理和 `/admin/api/sso/check`。
- provider 未配置时保持禁用并返回明确状态，不伪装为可用。

## 安全边界

- 不提交或输出 AccessKey、client secret、Apple/支付宝私钥、Cookie、验证码和 token。
- OAuth/OIDC 校验 state；OIDC 校验签名、issuer、audience、expiry 和 nonce。
- 第三方已验证邮箱命中已有账号时不自动合并，返回身份冲突；用户必须登录后显式绑定。
- provider/OTP 创建的账号不得把随机密码误算成可用登录方式。
- 验证码短期有效、单次使用、目标频控、IP 频控、失败次数限制；投递失败不能向用户显示已发送。
- 生产数据库迁移先在副本验证，只做可重复的增表、增列和索引；发布前备份代码与数据库。

## 验收标准

- A1：生产承载仓库包含真实 provider adapter，不再使用占位 start 路由。
- A2：五个平台发起和回调在 mock/契约测试中通过；禁用、缺配置、网络失败和冲突均有明确错误。
- A3：邮箱 OTP、短信 Captcha 门禁、频控、单次消费、投递失败和绑定/解绑测试通过。
- A4：生产数据库副本迁移后，原用户、密码登录、头像、权限和 SSO 契约回归通过。
- A5：本地全量 pytest、Python 编译、Harness、生产 canary 和公网浏览器/HTTP 回归通过。
- A6：代码和文档提交并推送；生产发布有逐文件备份、健康检查、观察和回滚命令。
- A7：只有完成平台应用创建、回调登记和受保护凭据配置的 provider 才能标记为线上可用；未满足项明确列为外部 blocker。

## 非目标

- 不自动复用微信公众号 AppID 作为网站扫码登录应用。
- 不删除旧账号、旧身份数据或旧登录方式。
- 不在本次切换独立 `polauuh.service`。
- 不为验证触发付费短信或创建第三方平台应用。
