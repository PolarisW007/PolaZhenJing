# Devlog: PolaUUH 多身份登录生产接入

日期：2026-10-21

状态：实现、本地 review 和测试完成；Git、生产 canary/切换、线上回归与钉钉同步待本次继续执行后回填。

## A2A 交付

- Requirement：`../requirements/2026-10-20-polauuh-production-auth.md`
- SPEC：`../specs/2026-10-20-polauuh-production-auth-spec.md`
- SDD：`../architecture/2026-10-20-polauuh-production-auth-sdd.md`
- Test：`../test-reports/2026-10-21-polauuh-production-auth.md`
- Release：`../release/2026-10-21-polauuh-production-auth.md`

## 实现摘要

- 在既有 Flask/SQLite/session 中合入 contacts、identities、verification、OAuth requests 和 audit，不切服务或数据库。
- 支持密码、邮箱 OTP、Captcha 前置手机号 OTP，以及微信、Apple、Google、支付宝、华为授权适配器。
- 增加 provider enabled/configured 状态、真实验签、身份冲突、无密码账号、最后登录方式保护和安全 next。
- OTP 与 OAuth state 使用条件更新实现原子单次消费，覆盖并发竞争失败路径。
- Apple `form_post` 使用短期签名 nonce cookie；provider token 不入库、不入 session、不写日志。
- 登录、注册、账号中心展示统一入口，未配置项可见但禁用。

## 测试

- Python 编译：Pass。
- 全量 pytest：147 passed in 3.25s。
- `scripts/polauuh_auth_harness.py`：11/11，`ok=true`，审计记录 7。
- 当前 `git diff --check`：Pass；提交前将再次运行 secret scan。

## 生产前置修复

生产主机的 Tailscale DNS 接管已按用户授权关闭，并备份原配置。因客户端为 `NeedsLogin` 且未自动恢复 resolv.conf，已恢复可用公共 DNS：Apple、微信、支付宝、华为和本站解析/HTTPS 延迟恢复到亚秒级；Google DNS 可解析但 HTTPS 仍超时。此变更不修改 Nginx、应用路由或 provider 开关。

## 外部同步

发布前开发日志已同步到 PolaZhenJing 项目文件夹：

- 钉钉文档：`https://alidocs.dingtalk.com/i/nodes/gpG2NdyVX37kymb5C544KPPyWMwvDqPk`
- AI 表格记录：`WVL1DdKpOq`
- 回读：`来源文件` 指向上述具体文档；`更新内容` 已回填 5 条实现、测试和生产待办摘要。

生产回归完成后将更新同一文档和同一记录，不新建重复日志。
