# Devlog: PolaUUH 多身份登录生产接入

日期：2026-10-21

状态：核心实现、Git、生产 canary/切换和线上回归完成；第三方供应商凭据、DirectMail 权限和短信产品参数仍待配置。

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
- 统一认证生产 harness 不再硬编码旧主题，改为动态比对统一账号当前 `theme` 与 `font_family`，避免用户修改偏好后出现假失败。

## 测试

- Python 编译：Pass。
- 全量 pytest：148 passed in 3.40s。
- `scripts/polauuh_auth_harness.py`：11/11，`ok=true`，审计记录 7。
- 动态偏好门禁目标测试：3 passed。
- 当前 `git diff --check`：Pass；提交前再次检查提交范围与敏感信息。

## 生产前置修复

生产主机的 Tailscale DNS 接管已按用户授权关闭，并备份原配置。因客户端为 `NeedsLogin` 且未自动恢复 resolv.conf，已恢复可用公共 DNS：Apple、微信、支付宝、华为和本站解析/HTTPS 延迟恢复到亚秒级；Google DNS 可解析但 HTTPS 仍超时。此变更不修改 Nginx、应用路由或 provider 开关。

## 生产发布与全系回归

- 发布前备份：`/opt/pola-backups/polauuh-auth-20261021-195512`；数据库发布前后 `quick_check=ok`，8 个用户和 5 张新增身份表完整。
- 独立 5018 canary、生产 Python 编译、147 项原全量测试和 11/11 身份 harness 均通过后，正常重启 `polazj.service`；服务 active 且 `/healthz` 返回 200。
- PolaRead 旧 `/api/auth/sso/aipd` 路径、首次用户映射提交和统一偏好同步已经修复；PolaRead 全量后端测试 `381 passed`。
- 公网只读服务 harness 的 102 项核心页面、API、资产和匿名鉴权合同全部通过；五个 provider 因未配置正式凭据保持禁用并返回站内提示，不计为核心服务故障。
- Nginx 配置检查通过，systemd 无失败单元，PolaNews 与 PolaRead Supervisor 进程均为 RUNNING。
- Aliyun DirectMail 真实请求返回 `Forbidden`，说明当前 RAM 账号只有短信权限；邮件 OTP 保持禁用，未伪报成功。
- 动态偏好门禁提交 `c4861fc` 已推送并发布到生产验收脚本，发布前备份位于 `/opt/pola-backups/unified-auth-harness-c4861fc-20261021-2138`；本地/生产 SHA-256 一致，生产跨应用检查 5/5。
- 最终增量日志窗口内 Nginx、PolaNews、PolaRead 无连接拒绝、upstream 超时、ASGI 异常或进程重启；仅有 1 条 760.83ms 的 PolaRead 慢查询。

## 外部同步

发布前开发日志已同步到 PolaZhenJing 项目文件夹：

- 钉钉文档：`https://alidocs.dingtalk.com/i/nodes/gpG2NdyVX37kymb5C544KPPyWMwvDqPk`
- AI 表格记录：`WVL1DdKpOq`
- 回读：`来源文件` 指向上述具体文档；`更新内容` 已回填 5 条实现、测试和生产待办摘要。

生产回归完成后更新同一文档和同一记录，不新建重复日志。
