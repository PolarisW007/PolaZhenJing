# 发布记录：分享卡片资产与 GEO v2 云端部署

日期：2026-06-13

## 发布目标

- 将分享卡片 v2、短链复制按钮、GEO 动态入口部署到 `https://aipd.me` 云服务器。
- 修复 root 短链页 `/s/<code>` 获取微信 JS-SDK 配置时可能请求错误 `/admin/api/...` 的问题。
- 增加微信 JS-SDK ready/error 诊断，便于线上确认手机端和 PC 端分享卡片链路。

## 发布范围

- 同步代码：`app/uploader.py`、`app/templates/article_view.html`、`app/templates/public_articles.html`。
- 同步 harness/test：`scripts/wechat_share_harness.py`、`scripts/seo_geo_harness.py`、`tests/test_social_publish.py`。
- 同步文档：`docs/pola/project-knowledge/` 本次相关记录。
- 同步静态兜底：`portal/robots.txt` 到项目和站点根 robots。

## 不发布范围

- 不覆盖服务器 `_posts`。
- 不覆盖服务器 `.env`、systemd/supervisor 密钥配置。
- 不覆盖 `assets/images/generated/`、`assets/images/share/` 的运行时资源；分享图由服务器按需生成。
- 不处理小红书、今日头条官方发帖 API。

## 发布前检查

- `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py scripts/seo_geo_harness.py`
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`
- `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py`
- `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`
- `PYTHONPATH=. .venv/bin/pytest tests -q`
- `git diff --check`

## 线上验证

- 云端运行同等 py_compile、pytest、wechat harness、GEO harness。
- 公网 curl 验证：
  - `https://aipd.me/s/49c0c4e8`
  - `https://aipd.me/PolaZhenjing/admin/api/wechat/share-config?url=https%3A%2F%2Faipd.me%2Fs%2F49c0c4e8`
  - `https://aipd.me/feed.xml`
  - `https://aipd.me/articles.json`
  - `https://aipd.me/robots.txt`
- 公网 HTML 必须包含：
  - `og:image` 横图 `*-og.jpg`
  - `thumbnail` / `WECHAT_SHARE.imgUrl` 方图 `*-wechat.jpg`
  - `WECHAT_SHARE_CONFIG_URL=https://aipd.me/PolaZhenjing/admin/api/wechat/share-config`
  - `wx.error`
  - `data-copy-shortlink`

## 回滚

- 恢复服务器部署前备份的相关文件。
- 如 nginx 调整失败，恢复 `/opt/backups/` 中的配置备份并 `nginx -t && systemctl reload nginx`。
- 删除 `assets/images/share/*-og.jpg` 与 `*-wechat.jpg` 缓存不会影响文章阅读。

## 执行记录

### 入口阻塞

- `ssh -vv -o ConnectTimeout=30 pola-server ...`：TCP established 后没有 SSH banner，最终 `Connection timed out during banner exchange`。
- `nc -vz -G 8 42.121.164.11 22/80/443`：端口均可建立 TCP 连接。
- `curl -v https://aipd.me/PolaZhenjing/skills/`：TCP connected 后 TLS `SSL connection timeout`。
- `curl -v https://aipd.me/articles/fde-databricks-snowflake-20260610.md`：同样 TLS `SSL connection timeout`。
- 连续 5 轮恢复探测均失败，`https_code=000`。

判断：本机到云服务器的网络路径能连到端口，但服务端 SSH/TLS 握手层无响应，无法执行 rsync、nginx 检查、服务重启和线上 harness。

### 恢复与发布

- 用户重启云服务器后入口恢复。
- 代码备份：`/opt/backups/polazj-share-card-geo-v2-20260613154729/`。
- nginx 备份：`/opt/backups/polazj-nginx-share-card-geo-v2-20260613154813.conf`。
- 精确 rsync 发布范围文件到 `/PolaZhenjing`，未覆盖 `_posts`、`.env`、运行时图片。
- nginx 已将 `/robots.txt`、`/feed.xml`、`/articles.json` 代理给 Flask。
- `nginx -t` 通过并已 reload。
- `polazj.service` 已 restart，状态 active。

## 发布后验证

- 云端 py_compile：通过。
- 云端 `tests/test_social_publish.py`：15 passed。
- 云端 `scripts/wechat_share_harness.py`：通过。
- 云端 `scripts/seo_geo_harness.py`：通过，`error_count=0`。
- 云端全量 tests：37 passed。
- `https://aipd.me/s/49c0c4e8`：200，包含 `og:image` 横图、`thumbnail` 方图、固定微信 API、`wx.error`、复制短链按钮、BreadcrumbList、wordCount。
- `...-og.jpg`：200 OK，JPEG，`1200x630`。
- `...-wechat.jpg`：200 OK，JPEG，`300x300`。
- `/robots.txt`、`/feed.xml`、`/articles.json`：200。
- 微信 share-config 对 `https://aipd.me/s/49c0c4e8` 返回 `configured=true`。
- share-diagnostics POST 返回 `{"ok": true}`，非 ready 状态可进入 journal warning 日志。
- 微信 JS接口安全域名校验文件：
  - 服务器路径：`/var/www/html/MP_verify_94QHBlDhbeGNvlAd.txt`。
  - nginx 备份：`/opt/backups/polazj-nginx-mp-verify-20260613165812.conf`。
  - nginx 已增加精确 `location = /MP_verify_94QHBlDhbeGNvlAd.txt` 并 reload。
  - 公网 URL：`https://aipd.me/MP_verify_94QHBlDhbeGNvlAd.txt`。
  - 验证结果：200 OK，`text/plain`，16 bytes，和用户提供文件一致。
  - 项目保留：`portal/MP_verify_94QHBlDhbeGNvlAd.txt`。
- 18:20 真机反馈：
  - 微信 WebView 内可打开右上角分享面板。
  - 朋友圈编辑页仍只出现 URL，没有卡片预览。
  - 同时服务器未收到真机 `ready/error` 诊断，说明原诊断发送方式不足以判断客户端状态。
- 微信分享诊断增强发布：
  - 备份：`/opt/backups/polazj-wechat-share-diagnostics-20260613183935/`。
  - `share-diagnostics` 支持 GET 图片探针。
  - 前端增加 `script-start`、`config-received`、`checkJsApi`、`menu-show`、`share-api-registered`、各分享 API success/fail/cancel/complete 诊断。
  - `wx.config` 增加 `checkJsApi`、`showOptionMenu`、`showMenuItems`。
  - 公网页面已包含 `checkJsApi`、`showMenuItems`、`reportWechatShareByImage`、`share-api-registered`。
  - 公网 GET 探针返回 204，并写入 journal。
  - 云端 `tests/test_social_publish.py`：16 passed。
  - 云端 `scripts/wechat_share_harness.py`：通过。
  - 云端 `scripts/seo_geo_harness.py`：通过。
  - 云端全量 tests：38 passed。

## 剩余风险

- 实际微信客户端诊断捕获过 `config:invalid url domain`。校验文件已配置，仍需在微信公众号后台“JS接口安全域名”页面点击校验/保存，让微信侧配置生效。
- PC/聊天输入框直接粘贴 URL 仍可能展示纯文本；网页可控的是微信内 WebView 右上角分享菜单。
- 下一次真机复验如仍失败，应直接根据 journal 中 `script-start/config-received/ready/checkJsApi/share-api-registered/*-fail` 状态定位，而不是继续猜测服务端 meta。
