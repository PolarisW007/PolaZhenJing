# Release: PolaUUH 多身份登录生产接入

日期：2026-10-21

状态：核心版本已发布并通过回归；外部 provider、邮件与短信按配置边界保持禁用。

## 发布面

- `app/__init__.py`：配置、幂等 schema 迁移、代理头和健康检查。
- `app/auth.py`、`app/identity/`、`app/mailer.py`、`app/sms.py`：统一身份、OTP、provider 和审计。
- 登录、注册、账号中心、密码模板及共享快捷入口。
- 新增依赖、测试、pytest collection 边界和 Harness。

Nginx 路由、端口、Cookie 域和生产数据库路径不改变；只正常重启 `polazj.service`。

## 发布前

1. Review、完整 pytest、Harness、secret scan、`git diff --check` 通过。
2. 提交并推送后核对本地、origin/main 和目标 commit。
3. 生产相关文件 clean，已有 `_posts`、图片和数据改动不覆盖。
4. 备份目标代码、依赖清单、当前 commit 和 SQLite 数据库。
5. 数据库副本执行迁移并核对 users/contacts/permissions/SSO；独立端口 canary 通过。

## 切换与观察

1. Fast-forward 或按发布清单更新本次文件，依赖安装到既有虚拟环境。
2. 正常重启 `polazj.service`，不重启 Nginx。
3. 检查 service active、启动日志、SQLite migration 和 upstream。
4. 公网验证 `/PolaUUH/admin/login`、`register`、`healthz`、SSO；桌面/手机检查页面。
5. 运行全系服务 Harness，并观察增量错误日志。

## 回滚

停止 `polazj.service`，恢复本次文件和数据库备份，重新启动；验证密码登录、SSO 和健康接口。新增表可保留，但数据库备份可在迁移异常时完整恢复。不得 reset 或覆盖生产已有内容改动。

## 配置边界

未配置的 provider 必须保持 disabled。Aliyun 邮件若权限不足则保留既有邮件通道。Captcha/SMS 四个必要产品参数未齐前禁止开放手机号发送。Google 在生产主机能稳定访问官方 token/JWKS 前禁止标记可用。

## 发布结果

- 代码提交 `56f8557` 已部署；发布备份位于 `/opt/pola-backups/polauuh-auth-20261021-195512`。
- 数据库迁移、5018 canary、生产编译、全量测试、身份 harness、跨应用 SSO、Nginx 和公开页面/API 回归通过。
- PolaRead 兼容修复通过独立分支交付，生产 SSO 新旧路径均正常；PolaRead 全量测试 381 项通过。
- 统一认证 harness 已升级为动态校验当前统一偏好，不再依赖旧的固定主题值。
