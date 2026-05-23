# AIPD 统一账号中心测试报告

日期：2026-05-21

## 验证项

- `python -m py_compile app/__init__.py app/auth.py app/skillhub.py scripts/unified_auth_harness.py` 通过。
- 线上 `https://aipd.me/` 返回 200。
- 线上 `https://aipd.me/agent.html` 返回 200。
- 线上 `https://aipd.me/assets/portal.js?v=202605211520` 返回 200。
- 线上 `https://aipd.me/PolaRead/` 跟随跳转后返回 200，最终地址为 `/PolaRead/index.html`。
- 线上 `https://aipd.me/polanews` 返回 200。
- 匿名访问 `https://aipd.me/PolaZhenjing/admin/account` 返回 302，仍会进入统一登录流程。
- 匿名调用 PolaRead SSO 返回 401：`未登录织梦空间`。
- 匿名调用 PolaNews SSO 返回 401：`未登录织梦空间`。
- 服务器端 `polazj.service` 为 active。
- 服务器端 PolaZhenjing 数据库已创建 `user_preferences`、`user_permissions`、`permission_requests`、`app_user_links`。
- 服务器端 PolaRead uvicorn 监听 `0.0.0.0:8766`。
- 服务器端 PolaNews Next 监听 `0.0.0.0:3456`。

## Harness

执行命令：

```bash
cd /PolaZhenjing
.venv/bin/python scripts/unified_auth_harness.py --json
```

结果：`ok: true`

覆盖项：

- `pola-auth-check`：统一账号服务可识别 `wsyxjer@gmail.com` 会话，`articles.read` 权限通过。
- `polaread-sso`：PolaRead 可用同一 AIPD 会话换取本地 access token。
- `polaread-preferences-overlay`：PolaRead 设置接口返回 AIPD 统一 `theme=dream-gold`、`font_family=system`，同时保留本地 `tts_voice`、`tts_speed`、`auto_play_next`、`show_translation`。
- `polanews-sso`：PolaNews 可用同一 AIPD 会话换取本地 token。
- `polanews-preferences-overlay`：PolaNews 设置接口返回 AIPD 统一 `theme=dream-gold`、`font_family=system`、`font_scale=normal`、`density=comfortable`，同时保留本地 `digest_times`、`followed_categories`。

## 数据和迁移安全

- 上线前已备份 PolaZhenjing 数据库：`/PolaZhenjing/data/wiki.db.bak.unified-auth-20260521151720`。
- 上线前已备份 PolaRead/PolaNews 关键文件：`/opt/backups/aipd-unified-auth-20260521145014`。
- 新增表使用 `CREATE TABLE IF NOT EXISTS`，不重建旧表。
- PolaRead 本地业务偏好不迁移，仅由读取接口叠加统一主题和字体。
- PolaNews 本地业务偏好不迁移，仅由读取接口叠加统一主题、字体、字号和密度。

## 发现与处理

- PolaRead 首轮 harness 使用了错误的设置接口路径 `/api/user/settings`，返回 404；复查路由后修正为 `/api/settings`。
- PolaNews 服务器上存在另一个 Next 进程，但工作目录为 `/root/PolaVoyage/cross-border-agents/admin-backend`，不属于 PolaNews，本次未处理。
- PolaNews 日志中 ABC News RSS 源曾超时，属于抓取源波动，与统一账号改造无关。
