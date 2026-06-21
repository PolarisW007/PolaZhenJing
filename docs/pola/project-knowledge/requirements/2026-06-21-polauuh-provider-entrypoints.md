# PolaUUH 线上注册登录三方快捷入口

日期：2026-06-21

## 原始需求

用户反馈 `https://aipd.me/PolaUUH/admin/register?...` 注册页没有微信、支付宝、Google、Apple 等快捷扫码/第三方登录入口，要求直接提交、部署到线上并完成验证；注册和登录都要支持三方快速验证登录。

## 目标

- 在线上真实生效的 PolaUUH 账号中心注册页展示第三方快捷入口。
- 登录页和注册页入口一致，覆盖微信、支付宝、Google、Apple、华为。
- 保持 `next` 跳转参数，避免破坏 SSO 回跳。
- 未配置第三方授权密钥时不能出现 500，必须安全降级。

## 非目标

- 本次不在 PolaZhenJing 旧账号中心内落地完整 OAuth 回调和身份绑定表迁移。
- 不提交任何 provider secret、cookie、token 或 `.env` 明文。
- 不调整 Nginx 路由或数据库结构。

## 验收标准

- `/PolaUUH/admin/login` 页面可看到微信、支付宝、Google、Apple、华为快捷入口。
- `/PolaUUH/admin/register` 页面可看到同一组快捷入口。
- 快捷入口链接保留 `next` 参数。
- 点击未完成授权配置的平台入口时返回登录页并给出提示，不影响密码/邮箱登录注册。
