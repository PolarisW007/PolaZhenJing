# 测试报告：分享卡片与 GEO 强化

日期：2026-06-12

## 本地测试

| 命令 | 结果 | 说明 |
| --- | --- | --- |
| `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py scripts/seo_geo_harness.py` | 通过 | Python 语法检查 |
| `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q` | 14 passed | 短链、分享 meta、多平台发布基础回归 |
| `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py` | 通过 | 验证短链、OG/Twitter/微信字段、分享 JPEG 缩略图 |
| `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py` | 通过 | 验证 Jekyll/Portal/Flask 动态 GEO |
| `PYTHONPATH=. .venv/bin/pytest tests -q` | 39 passed | 全量测试 |

## 关键证据

- 本地 `wechat_share_harness` 输出 `og_image=https://aipd.me/PolaZhenjing/assets/images/share/...jpg`。
- 本地 `seo_geo_harness` 输出 `{"ok": true, "error_count": 0}`。
- 本地微信取票失败是本机出口 IP 不在微信公众号白名单，harness 已按降级路径验证；云端需验证 `configured=true`。

## 云端测试

| 命令 / URL | 结果 | 说明 |
| --- | --- | --- |
| `python3 -m py_compile app/__init__.py app/uploader.py scripts/wechat_share_harness.py scripts/seo_geo_harness.py` | 通过 | 云端 Python 语法检查 |
| `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q` | 14 passed | 云端社交发布与短链回归 |
| `PYTHONPATH=. .venv/bin/python scripts/wechat_share_harness.py` | 通过 | 云端微信配置可取到签名，短链和分享图字段正确 |
| `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py` | 通过 | 云端动态 sitemap / llms / article meta 检查 |
| `https://aipd.me/s/49c0c4e8` | 通过 | 包含 canonical、shortlink、短链 og:url、300x300 JPEG 分享图 meta |
| `https://aipd.me/PolaZhenjing/assets/images/share/2026-06-10-fde-databricks-snowflake-20260610-49c0c4e8.jpg` | 通过 | `200 OK`、`Content-Type: image/jpeg`、`Content-Length: 26353` |
| `https://aipd.me/sitemap.xml` | 通过 | 包含示例文章 canonical URL |
| `https://aipd.me/llms.txt` | 通过 | 包含 Article Index、示例文章 canonical 和 shortlink |
| `/PolaZhenjing/admin/api/wechat/share-config?url=https%3A%2F%2Faipd.me%2Fs%2F49c0c4e8` | 通过 | 返回 `configured=true` |

## 风险与残余项

- 微信、朋友圈、即刻等平台最终是否展示卡片仍受客户端缓存、抓取节奏和平台策略影响；服务端已经提供标准 OG/Twitter meta、微信 JS-SDK 配置、HTTPS JPEG 缩略图和短链。
- sitemap 使用 canonical 长链接，短链用 `rel=shortlink` 和 JSON-LD `sameAs` 暴露，避免搜索引擎把同一文章重复索引。
