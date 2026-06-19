# 开发日志：根首页状态条移除

## 目标

根据用户截图反馈，移除 `aipd.me` 根首页 hero 下方的服务状态胶囊条，并让下方“AI Articles / 最近写下的 AI 思考”板块上移一点。

## 改动

- `portal/index.html`：删除 `.signal-strip` 状态条 DOM。
- `portal/assets/portal.css`：桌面 hero 从 `100svh` 调整为 `88svh`，底部 padding 从 `52px` 调整为 `28px`。
- `portal/assets/portal-sections.css`：删除不再使用的 `.signal-strip` 样式和移动端样式。

## 验证

- 本地静态检查：
  - `rg "signal-strip|Root: aipd.me|PolaZhenjing: active|PolaRead: active|PolaNews: active" portal/index.html portal/assets/portal.css portal/assets/portal-sections.css`：无匹配。
- 本地 Chrome harness：
  - URL：`http://127.0.0.1:8026/`
  - `hasSignalStrip=false`
  - `hasStatusText=false`
  - `articlesTop=1082`
  - `heroHeight=1082`
  - `viewportHeight=1229`
- 线上 curl：
  - `https://aipd.me/`：不含 `.signal-strip` 和状态文案。
  - `https://aipd.me/assets/portal.css`：包含 `min-height: 88svh`。
  - `https://aipd.me/assets/portal-sections.css`：不含 `.signal-strip`。
- 线上 Chrome harness：
  - URL：`https://aipd.me/?v=<timestamp>`
  - `hasSignalStrip=false`
  - `hasStatusText=false`
  - `articlesTop=1082`
  - `heroHeight=1082`
  - `viewportHeight=1229`
  - 控制台错误：无。
- `nginx -t`：通过。

## 发布

- 备份：`/opt/backups/polaindex-status-strip-20260616-113914/files.tgz`，额外备份 `/home/sirius/PolaIndex/index.html` 到 `polaindex-home.tgz`。
- 同步：
  - `/var/www/html/index.html`
  - `/var/www/html/assets/portal.css`
  - `/var/www/html/assets/portal-sections.css`
  - `/home/sirius/PolaIndex/index.html`
  - `/home/sirius/PolaIndex/assets/portal.css`
  - `/home/sirius/PolaIndex/assets/portal-sections.css`
- 本次是静态文件发布，不重启 Flask；nginx 配置未修改。
