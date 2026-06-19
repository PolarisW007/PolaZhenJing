# Test Report: 文章浏览页权限与导航优化

日期: 2026-06-14

## 测试矩阵

| 验收项 | 类型 | 方式 | 状态 |
| --- | --- | --- | --- |
| A2 普通文章页不显示管理/分享操作 | 单测/集成 | HTML 断言 | 通过 |
| A3 管理员文章页显示管理工具 | 单测/集成 | admin session HTML 断言 | 通过 |
| A4 单一摘要区域 | 单测/集成 | class/文本断言 | 通过 |
| A5 普通轻导航 | 单测/集成 | base nav HTML 断言 | 通过 |
| A6 上下篇与快速列表 | 单测/集成 | HTML 断言 | 通过 |
| A8 浏览器 harness | UI 回归 | Playwright/Chrome | 通过 |

## 命令记录

- `.venv/bin/python -m py_compile app/uploader.py app/auth.py app/__init__.py`
  - 结果: 通过。
- `.venv/bin/python -m pytest tests/test_article_reader_roles.py tests/test_social_publish.py::test_public_article_short_link_renders_share_card_metadata tests/test_social_publish.py::test_public_article_card_link_is_lightweight_for_social_crawlers -q`
  - 结果: `5 passed in 0.38s`。
- `.venv/bin/python -m pytest tests/test_social_publish.py tests/test_article_edit_rich_editor.py tests/test_article_reader_roles.py tests/test_polauuh_auth.py -q`
  - 结果: `29 passed in 0.58s`。
- `.venv/bin/python -m pytest tests -q`
  - 结果: `48 passed in 1.02s`。
- `.venv/bin/python -m pytest -q`
  - 结果: collection 阶段失败,原因是 `referene/TencentDB-Agent-Memory/hermes-plugin/...` 外部参考测试依赖 `agent.memory_provider`,不属于项目 `tests/`。

## 浏览器 Harness

本地服务:

```bash
.venv/bin/flask --app app run --host 127.0.0.1 --port 5014
```

Chrome/Playwright 结果:

| 角色 | 路径 | 摘要 | 快速 Wiki | 上下篇 | 管理工具 | 卡片按钮 | PolaUUH |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 游客 | `/articles/yi-ge-ren-you-zheng-zhi-you-jia-20260524.md` | 1 | 1 | 2 | 0 | 0 | 否 |
| 普通登录用户 | `/articles/yi-ge-ren-you-zheng-zhi-you-jia-20260524.md` | 1 | 1 | 2 | 0 | 0 | 是 |
| 管理员 | `/admin/articles/yi-ge-ren-you-zheng-zhi-you-jia-20260524.md` | 1 | 1 | 2 | 1 | 复制卡片 1 / 微信图文 1 | 否 |

## 云端验证

- 备份目录: `/opt/backups/polazj-article-reader-admin-split-20260614225747`。
- 云端语法检查:
  - `cd /PolaZhenjing && .venv/bin/python -m py_compile app/uploader.py app/auth.py app/__init__.py`
  - 结果: 通过。
- 云端相关测试:
  - `.venv/bin/python -m pytest tests/test_article_reader_roles.py tests/test_social_publish.py::test_public_article_short_link_renders_share_card_metadata tests/test_social_publish.py::test_public_article_card_link_is_lightweight_for_social_crawlers tests/test_article_edit_rich_editor.py -q`
  - 结果: `11 passed in 1.06s`。
- 云端 `tests/` 全集:
  - `.venv/bin/python -m pytest tests -q`
  - 结果: `45 passed in 1.36s`。
- 服务重启:
  - `systemctl restart polazj.service`
  - 结果: `active`,新 master PID `727538`。
- 线上目标文章:
  - `curl https://aipd.me/articles/fde-databricks-snowflake-20260610.md`
  - 结果: `200`,60803 bytes。
- 云端 harness:
  - `PYTHONPATH=. .venv/bin/python scripts/seo_geo_harness.py`
  - 结果: `{ "ok": true, "error_count": 0, "errors": [] }`。
  - `.venv/bin/python scripts/wechat_share_harness.py`
  - 结果: `wechat_share_harness: ok`,目标卡片 `https://aipd.me/c/49c0c4e8`。
- 线上 Chrome PC DOM:
  - `summaryCount=1`, `quickWikiCount=1`, `prevNextCards=2`, `copyCardControls=0`, `wechatCardControls=0`, `hasAdminNav=false`。
- 线上 Chrome mobile DOM:
  - `summaryCount=1`, `quickWikiCount=1`, `prevNextCards=2`, `copyCardControls=0`, `wechatCardControls=0`, `bodyWidth=390`。

## 残余风险

- 本地 dev server 没有 Nginx 的 `/PolaZhenjing` 反代前缀,旧文章内部分 `/PolaZhenjing/assets/...` 静态资源在本地 harness 里 404;线上由现有反代/静态资源规则覆盖,本次不改该路由。
- 本地 `_posts` 没有用户指定的 `fde-databricks-snowflake-20260610.md`,已在云服务用该线上 URL 完成真实 harness。
- 公开页仍保留微信 JS-SDK 原生分享配置脚本,但不显示管理员复制/海报/平台分享按钮;这是为了不回退微信右上角卡片分享能力。
