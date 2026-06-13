# 开发日志：分享卡片资产与 GEO v2

日期：2026-06-13

## 目标

- 按 Pola A2A 规范完成分享卡片、复制短链按钮和 GEO v2。
- 输出 PRD、SPEC、SDD、调研、测试报告和开发日志。
- 实现后提供 harness 过程。

## A2A 阶段记录

| 阶段 | 状态 | 产物 |
| --- | --- | --- |
| 项目上下文 | Done | `AGENTS.md`、`docs/pola/project-knowledge/README.md`、现有分享/GEO代码 |
| 需求分析 | Done | `requirements/2026-06-13-share-card-geo-v2.md` |
| PRD | Done | `specs/2026-06-13-share-card-geo-v2-prd.md` |
| SPEC | Done | `specs/2026-06-13-share-card-geo-v2-spec.md` |
| SDD | Done | `architecture/2026-06-13-share-card-geo-v2-sdd.md` |
| GEO 调研 | Done | `analysis/2026-06-13-geo-optimization-research.md` |
| 实现 | Done | 分享双图、复制短链按钮、动态 robots/feed/json、JSON-LD 图谱、微信公网 API 前缀和诊断 |
| 测试 | Done | `test-reports/2026-06-13-share-card-geo-v2-test.md` |
| 发布 | Done with external WeChat-domain risk | 用户重启云服务器后已完成最小同步、nginx reload、服务重启和线上 harness |

## 实现记录

- `app/uploader.py`
  - 新增 `SHARE_IMAGE_PRESETS`，生成 `*-wechat.jpg` 300x300 和 `*-og.jpg` 1200x630。
  - 分享字段支持 `share_title`、`share_summary`、`share_image` front matter 覆盖。
  - 文章页生成完整 `@graph` JSON-LD：WebSite、Organization、Person、BreadcrumbList、WebPage、Article。
  - Article 增加 `wordCount`、`timeRequired`、`articleSection`、`about`。
  - 新增动态 `/robots.txt`、`/feed.xml`、`/articles.json`。
  - 增强 `/llms.txt`，增加 Site Identity、Share Metadata Contract、Feeds。
  - 增强 `/sitemap.xml`，加入 feed、articles.json、llms。
  - 新增 `/admin/api/wechat/share-diagnostics`，记录非敏感 JS-SDK ready/error 状态。
  - 文章页渲染固定公网 `wechat_share_config_url` 和 `wechat_share_diagnostics_url`，避免 root 短链页生成错误 `/admin/api/...`。
- `app/templates/article_view.html`
  - OG/Twitter/itemprop 使用 1200x630 横图。
  - 微信 JS-SDK `imgUrl` 使用 300x300 正方图。
  - 所有读者可见“复制短链接”按钮，复制 `short_url`。
  - 微信 JS-SDK 成功/失败状态回传诊断接口，页面保留正常阅读和复制短链能力。
  - 管理员仍可见微信/朋友圈、即刻、X、LinkedIn 辅助入口。
- `app/templates/public_articles.html`
  - 文章列表页增加 canonical、alternate feed、OG/Twitter 和 ItemList JSON-LD。
- `portal/robots.txt`
  - 增加 admin 路径禁止抓取兜底。
- `scripts/wechat_share_harness.py`
  - 验证 OG 横图、微信正方图、复制按钮和公开/管理边界。
- `scripts/seo_geo_harness.py`
  - 验证文章页 JSON-LD、文章列表 ItemList、sitemap、robots、llms、RSS、JSON feed。
- `tests/test_social_publish.py`
  - 增加 GEO 动态文件和分享卡片 v2 回归。

## Harness 过程

- `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py scripts/seo_geo_harness.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：15 passed。
- `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py`：通过；输出 `og_image=...-og.jpg`、`wechat_image=...-wechat.jpg`。
- `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`：通过，`error_count=0`。
- `PYTHONPATH=. .venv/bin/pytest tests -q`：40 passed。
- `file assets/images/share/*-1dfba0e0-*.jpg`：确认 `1200x630` 和 `300x300`。
- 本地 Flask dev server + curl：确认文章页复制按钮、OG/thumbnail、BreadcrumbList、wordCount、articleSection；文章列表 ItemList；robots/articles.json 正常。
- 云端部署探测：
  - `ssh -vv -o ConnectTimeout=30 pola-server ...`：TCP established 后 `Connection timed out during banner exchange`。
  - `nc -vz -G 8 42.121.164.11 22/80/443`：端口可连接。
  - `curl -v https://aipd.me/PolaZhenjing/skills/`：TCP connected 后 TLS `SSL connection timeout`。
  - 5 轮恢复探测均为 SSH banner 超时、HTTPS `https_code=000`。
- 用户重启云服务器后入口恢复：
  - `polazj.service`、`nginx` 均 active。
  - 备份代码：`/opt/backups/polazj-share-card-geo-v2-20260613154729/`。
  - 备份 nginx：`/opt/backups/polazj-nginx-share-card-geo-v2-20260613154813.conf`。
  - 精确同步本次代码、模板、harness、测试和文档，不覆盖 `_posts`、`.env`、运行时图片。
  - nginx 已代理 `/robots.txt`、`/feed.xml`、`/articles.json` 到 Flask。
  - `polazj.service` 已 restart，服务 active。
- `git diff --check`：通过。

## 风险

- 微信、即刻等客户端卡片展示仍可能受平台缓存和抓取策略影响。
- 微信直接粘贴 URL 是否转换卡片受客户端策略和缓存影响；微信内右上角分享由 JS-SDK 控制，是本轮主要可控链路。
- 云端微信 share-config 对 `https://aipd.me/s/49c0c4e8` 返回 `configured=true`。
- 诊断接口已可写日志；实际捕获到微信客户端 `config:invalid url domain`，指向微信公众号后台 JS接口安全域名/校验文件配置风险，不是服务端签名接口不可用。
- 服务器根目录未发现 `MP_verify*.txt` 文件，需在公众号后台获得校验文件名和内容后补齐。
- 浏览器级 Playwright 检查因当前 Node 环境缺少 `playwright` 降级为 HTTP/HTML harness。

## Commit 状态

待提交；本轮云端已发布，仍需用户在微信公众号后台完成 JS接口安全域名校验后做真机复验。
