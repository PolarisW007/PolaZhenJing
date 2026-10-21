# SDD: PolaUUH 多身份登录生产合并

日期：2026-10-20

## 风险等级

P1。改动登录注册主流程、SQLite schema、生产 secret 和服务重启；必须经过副本迁移、完整回归、canary、备份和发布后观察。

## 架构决策

继续由 `/PolaZhenjing` 的 `polazj.service` 和 `data/wiki.db` 承载 PolaUUH。将独立仓库的 identity 子系统以模块形式并入，不启动独立服务。

理由：现有生产用户、session、头像、权限和多个 Pola 消费者都依赖该进程。直接切换独立服务会同时改变数据库、Cookie 和路由，风险明显高于模块合并。

## 模块

- `app/identity/contacts.py`：联系方式规范化、脱敏、唯一约束和登录方式计数。
- `app/identity/verification.py`：OTP 生成、频控、投递、消费、登录/绑定。
- `app/identity/captcha.py`：Aliyun Captcha 服务端验证。
- `app/identity/providers/`：Google、Apple、微信、支付宝、华为 adapter；统一 state/nonce 和身份归一化。
- `app/identity/audit.py`：脱敏审计。
- `app/auth.py`：保留头像和管理功能，接入 OTP/provider/身份管理。
- `app/__init__.py`：读取配置并执行幂等 schema 扩展。

## 数据迁移

只新增 identity 表、索引和 `users` 可空/有默认值字段。迁移时把已有真实邮箱写入 `user_contacts`，不修改原邮箱、密码、角色、头像或权限。

新增 `password_enabled`：已有用户迁移为 `1`；OTP/provider 创建用户写 `0`。这样解绑门禁只计算真实可用密码。

迁移流程：生产 DB 在线备份 -> 隔离副本执行迁移 -> 行数/主键/账号抽样和旧路径测试 -> 远端 canary -> 短暂停止 `polazj.service` -> 再备份 DB -> 替换代码 -> 启动和回归。SQLite DDL 失败时回滚事务；发布失败时恢复代码和 DB 备份。

## Provider 数据流

1. `start` 校验启用和完整配置，生成 state/nonce hash 与安全 next。
2. 浏览器跳转官方授权页。
3. callback 消费 state，校验 session nonce，并在服务端换 token。
4. OIDC 验证签名、issuer、audience、expiry、nonce；微信/支付宝调用官方用户接口。
5. 建立或绑定 `user_identities`，写审计，复用现有 Flask session。
6. 第三方 token 不写数据库、日志或 session。

## 稳定性与性能

- 外部请求 connect/read 总超时 10 秒；网络与返回解析错误统一降级，不能造成 500。
- auth 表查询均有 provider/state/target/user 索引；审计和请求记录后续可按保留期清理，本次不清理生产日志。
- OTP 有目标冷却、IP 小时上限、最大尝试和单次消费。
- 两个 Gunicorn worker 共享 SQLite 数据状态，不依赖进程内 OTP 或 OAuth state。

## 不影响功能路径

- 密码登录、邮箱密码注册和旧邮箱验证。
- 头像上传/裁剪、资料和偏好、权限申请/审批。
- `/PolaUUH/admin/api/me`、`/PolaUUH/admin/api/sso/check`。
- `/PolaZhenjing/admin/*` legacy 路径和全部文章后台。

## 发布与回滚

- 发布包只含本次账号模块、模板、依赖和测试，不覆盖生产文章、图片和其它脏文件。
- 代码备份与 DB 备份放在独立时间戳目录；记录 SHA256。
- canary 使用生产 DB 副本和独立端口，不写真实生产 DB。
- 切换只重启 `polazj.service`；Nginx 不改不重启。
- 回滚：停止服务、恢复逐文件备份和 DB 备份、启动、验证密码登录页/SSO/健康路径。

## 外部依赖

代码上线不等于 provider 可用。每个平台仍需已审核应用、准确回调和受保护凭据；Google 还依赖服务器能访问 Google OIDC/token/JWKS。缺一项就保持 provider 禁用，并在发布报告列为 blocker。
