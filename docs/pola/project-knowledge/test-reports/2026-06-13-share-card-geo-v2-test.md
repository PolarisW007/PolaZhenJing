# 测试报告：分享卡片资产与 GEO v2

日期：2026-06-13

## 计划

| 命令 | 目标 |
| --- | --- |
| `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py scripts/seo_geo_harness.py` | 语法检查 |
| `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q` | 社交发布和分享卡片回归 |
| `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py` | 微信/通用分享卡片自检 |
| `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py` | GEO 动态文件与结构化数据自检 |
| `PYTHONPATH=. .venv/bin/pytest tests -q` | 全量测试 |
| 线上 `curl https://aipd.me/s/<code>` | 公网短链页 meta、微信 API 前缀、诊断钩子 |
| 线上 `curl https://aipd.me/PolaZhenjing/admin/api/wechat/share-config?...` | 云服务器出口 IP 下微信 JS-SDK 签名状态 |
| `git diff --check` | diff 格式检查 |

## 执行结果

| 命令 | 结果 | 说明 |
| --- | --- | --- |
| `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py scripts/seo_geo_harness.py` | 通过 | Python 语法检查 |
| `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q` | 15 passed | 分享卡片、短链、GEO feed、发布中心基础回归 |
| `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py` | 通过 | 验证短链、OG 横图、微信正方图、公开复制短链按钮、管理入口边界 |
| `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py` | 通过 | 输出 `{"ok": true, "error_count": 0}` |
| `PYTHONPATH=. .venv/bin/pytest tests -q` | 40 passed | 全量测试 |
| `scripts/wechat_share_harness.py` 新增断言 | 通过 | 固定公网微信 API 前缀、`wx.error`、诊断接口 |
| `git diff --check` | 通过 | diff 空白检查 |
| `file assets/images/share/*-1dfba0e0-*.jpg` | 通过 | OG 图 1200x630；微信图 300x300 |

## Harness 输出摘录

`scripts/wechat_share_harness.py`：

```text
wechat_share_harness: ok
article=yi-ge-ren-you-zheng-zhi-you-jia-20260524.md
og_url=https://aipd.me/s/1dfba0e0
og_image=https://aipd.me/PolaZhenjing/assets/images/share/2026-05-24-yi-ge-ren-you-zheng-zhi-you-jia-20260524-1dfba0e0-og.jpg
wechat_image=https://aipd.me/PolaZhenjing/assets/images/share/2026-05-24-yi-ge-ren-you-zheng-zhi-you-jia-20260524-1dfba0e0-wechat.jpg
```

本机出口 IP 不在微信公众号白名单，微信票据接口按预期降级并记录 warning；云端白名单环境部署后需验证 `configured=true`。

`scripts/seo_geo_harness.py`：

```json
{
  "ok": true,
  "error_count": 0,
  "errors": []
}
```

## 本地 HTTP 渲染验证

启动本地 Flask dev server：

```bash
PYTHONPATH=. .venv/bin/python -c "from app import create_app; app=create_app(); app.run(host='127.0.0.1', port=5002, debug=False, use_reloader=False)"
```

验证项：

- 文章页 HTML 包含 `data-copy-shortlink` 和 `复制短链接`。
- 文章页 HTML 包含 `og:image`、`thumbnail`、`WECHAT_SHARE`。
- 文章页 JSON-LD 包含 `BreadcrumbList`、`wordCount`、`articleSection`。
- `/articles` 包含 `ItemList`、`feed.xml`、`articles.json`。
- `/robots.txt` 包含 admin 禁止和 sitemap。
- `/articles.json` 返回文章 canonical URL、shortlink、summary、reading_time、word_count。

## 浏览器验证说明

尝试使用 Playwright 做真实浏览器检查，但当前 Node 环境未安装 `playwright`，in-app Browser 控制工具也未暴露，因此本轮降级为 Flask HTTP/HTML harness。可视化风险由模板测试、HTTP 渲染和 harness 覆盖；部署后建议用线上浏览器再点一次复制按钮。

## 云端验证记录

### 入口阻塞与恢复

- `ssh -vv -o ConnectTimeout=30 pola-server ...`：TCP connected，随后 `Connection timed out during banner exchange`。
- `nc -vz -G 8 42.121.164.11 22/80/443`：端口均可 TCP 连接。
- `curl -v https://aipd.me/PolaZhenjing/skills/`：TCP connected，随后 TLS `SSL connection timeout`。
- 5 轮恢复探测均失败：SSH banner timeout、HTTPS `https_code=000`。
- 用户重启云服务器后恢复，`polazj.service`、`nginx` 均 active。

### 服务器 harness

- 云端 `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py scripts/seo_geo_harness.py`：通过。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：15 passed。
- 云端 `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py`：通过，示例短链 `https://aipd.me/s/49c0c4e8`。
- 云端 `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`：通过，`error_count=0`。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests -q`：37 passed。
- 微信诊断增强后：
  - 本地 `tests/test_social_publish.py`：16 passed。
  - 本地 `scripts/wechat_share_harness.py`：通过，覆盖 GET 图片探针。
  - 云端 `tests/test_social_publish.py`：16 passed。
  - 云端 `scripts/wechat_share_harness.py`：通过。
  - 云端 `scripts/seo_geo_harness.py`：通过。
  - 云端全量 tests：38 passed。
- `polazj.service` restart 后 active。

### 公网验证

- `https://aipd.me/s/49c0c4e8` 包含：
  - `og:image=...-og.jpg`
  - `og:image:width=1200`
  - `og:image:height=630`
  - `thumbnail=...-wechat.jpg`
  - `WECHAT_SHARE_CONFIG_URL=https://aipd.me/PolaZhenjing/admin/api/wechat/share-config`
  - `WECHAT_SHARE_DIAGNOSTICS_URL=https://aipd.me/PolaZhenjing/admin/api/wechat/share-diagnostics`
  - `wx.error`
  - `data-copy-shortlink`
  - `BreadcrumbList`
  - `wordCount`
- `...-og.jpg`：200 OK，`Content-Type: image/jpeg`，服务器文件尺寸 `1200x630`。
- `...-wechat.jpg`：200 OK，`Content-Type: image/jpeg`，服务器文件尺寸 `300x300`。
- `/robots.txt`：200，禁止 `/admin/` 和 `/PolaZhenjing/admin/`。
- `/feed.xml`：200，RSS 包含文章 canonical URL。
- `/articles.json`：200，包含 canonical URL、shortlink、summary、word_count。
- `share-config?url=https://aipd.me/s/49c0c4e8`：返回 `configured=true`。
- `share-diagnostics` POST：返回 `{"ok": true}`，非 ready 状态可在 journal 记录 warning。
- `https://aipd.me/MP_verify_94QHBlDhbeGNvlAd.txt`：200 OK，`Content-Type: text/plain`，`Content-Length: 16`，与用户提供文件 `cmp` 一致。
- `share-diagnostics` GET 图片探针：公网返回 204，并在 journal 记录 `status=script-start`。
- 短链页包含 `checkJsApi`、`showMenuItems`、`share-api-registered`、`reportWechatShareByImage`、新旧分享 API 注册逻辑。

### 剩余风险

- 诊断日志捕获过真实微信客户端 `config:invalid url domain`。校验文件和 JS接口安全域名已配置后，需再次用微信内真机右上角分享复验。
- PC/聊天框直接粘贴 URL 仍可能显示纯文本；可控链路是微信内 WebView 右上角 `转发给朋友` / `分享到朋友圈`。
