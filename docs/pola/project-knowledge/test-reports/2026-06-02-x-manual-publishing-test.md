# X 手动发布模式测试报告

- 日期：2026-06-02
- 需求池记录：`XhcYwKVYha`

## 测试目标

- 确认 X 不再依赖 API token。
- 确认 X 手动发布包可生成并展示。
- 确认 X 文案长度不超过 280 字。
- 确认原有社交发布测试不回归。

## 测试命令

已执行：

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q
.venv/bin/python -m py_compile app/social_publish.py
```

浏览器验证：

```bash
FLASK_APP=app .venv/bin/flask run --host 127.0.0.1 --port 5001
# Playwright 打开 /admin/social/articles/2026-05-24-yi-ge-ren-you-zheng-zhi-you-jia-20260524.md 并截图
```

## 结果

- `app/social_publish.py` 语法检查通过。
- `tests/test_social_publish.py`：11 passed。
- 新增 `test_build_x_manual_package_is_copyable_and_limited`，确认 X 发布包使用 `build_x_post_text` 且长度不超过 280 字。
- 新增 `test_social_publish_x_uses_manual_package_ui`，确认页面出现 X 手动发布包入口，不再出现 `X_USER_ACCESS_TOKEN`、`发布到 X` 或 `/x/post` 自动发帖入口。
- 原有微信公众号、小红书、头条发布包测试继续通过。
- 本地浏览器截图：`.qa-artifacts/x-manual-publishing/x-manual-package-local.png`。
- 浏览器断言：`hasManualPackage=true`、`hasComposeUrl=true`、`hasTokenText=false`、`hasAutoPost=false`。
- 生产同步后验证：`polazj.service=active`；`/admin/social/` 未登录 `302`；`/admin/login` 为 `200`；生产 `scripts/x_publish_smoke.py` 和 `scripts/x_token_config.py` 已移除。
