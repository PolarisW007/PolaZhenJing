# 开发日志：后台无前缀 URL 404 兼容修复

日期：2026-06-04

## 需求与问题

用户反馈线上后台出现 nginx 404，截图 URL 包括：

- `https://aipd.me/admin/upload`
- `https://aipd.me/admin/articles/claude-code-claude-md-20260531.md/edit`

正确线上入口应为 `/PolaZhenjing/admin/*`。本次目标是确认 404 根因，并修复旧链接、旧标签页或漏前缀跳转导致的不可用问题。

## 排查结论

- 线上 `https://aipd.me/admin/upload` 返回 nginx 404。
- 线上 `https://aipd.me/PolaZhenjing/admin/upload` 正常进入 Flask，未登录时 302 到 `/PolaZhenjing/admin/login`。
- nginx 的 `/PolaZhenjing/` 代理已设置 `X-Script-Name /PolaZhenjing`。
- Flask `ReverseProxied` 在收到 `X-Script-Name` 时，`url_for()` 可生成 `/PolaZhenjing/admin/*`。
- 截图中的 404 来自无前缀 `/admin/*` 请求直接命中 nginx，未进入 Flask。

## 改动

- 新增测试：`test_admin_links_respect_script_name_prefix`，验证带 `X-Script-Name: /PolaZhenjing` 时后台链接包含 `/PolaZhenjing/admin/*`，且不输出无前缀 `/admin/*`。
- 云端 nginx 增加兼容重定向：`/admin/*` 临时跳转到 `/PolaZhenjing/admin/*`，避免旧入口直接 404。

## 验证

- 本地 Flask test client：带 `X-Script-Name` 的 `/admin/articles` 输出 `/PolaZhenjing/admin/*` 链接，无 `href="/admin...`。
- 本地 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：12 passed。
- 本地 `python3 -m py_compile app/__init__.py app/uploader.py`：通过。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：12 passed。
- 线上 `https://aipd.me/admin/upload`：302 到 `https://aipd.me/PolaZhenjing/admin/upload`。
- 线上 `https://aipd.me/admin/articles/claude-code-claude-md-20260531.md/edit`：302 到对应带前缀路径。
- 线上 `https://aipd.me/PolaZhenjing/admin/upload`：继续返回 302 到 `/PolaZhenjing/admin/login`。

## 风险

- `/admin/*` 兼容跳转只用于 PolaZhenjing 后台旧入口，不改变 `/PolaZhenjing/admin/*` 主路径。
- 使用临时跳转，避免浏览器永久缓存错误策略。

## Commit 状态

待提交：后台前缀兼容测试、排障记录和云端 nginx 兼容配置说明。
