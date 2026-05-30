# 开发日志：文章多平台发布中心

日期：2026-05-30

## 目标

实现文章多平台发布中心第一阶段：微信公众号官方草稿同步，小红书/今日头条发布包生成和人工回填。

## 配置记录

- 已将微信公众号 `WECHAT_MP_APP_ID` / `WECHAT_MP_APP_SECRET` 写入本地 `.env`。
- `.env` 原本已被 `.gitignore` 忽略；本次补充忽略 `.env.bak-*`，避免备份文件误提交。
- 临时 `.env` 备份已删除，避免本地保留多份密钥副本。
- 密钥不写入代码、文档正文、测试输出和 git diff。

## 计划改动

- 新增 `app/social_publish.py`。
- 新增发布中心模板和发布任务状态模板。
- 注册 blueprint 和 SQLite schema。
- 在文章列表、文章详情、后台导航增加入口。
- 新增最小测试覆盖。
- 继续补齐微信公众号 `freepublish/submit` 发布提交和 `freepublish/get` 状态查询。

## 验证记录

- `python3 -m py_compile app/social_publish.py app/__init__.py app/uploader.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py`：4 passed。
- `PYTHONPATH=. .venv/bin/pytest tests`：14 passed。
- `git diff --check`：通过。
- Flask test client：`/admin/social/` 和 `/admin/social/articles/<filename>` 均返回 200，发布提交/查询按钮模板渲染通过。
- 本地开发服务 smoke：`http://127.0.0.1:5057/admin/social/` 未登录时返回 302 到 `/admin/login`。
- 微信 token 调用：本地配置已读取成功，但微信返回当前出口 IP `122.214.242.68` 不在公众号接口 IP 白名单内；需到微信公众平台后台添加该 IP 后再重试。

## 风险

- 微信接口需真实公众号、AppSecret 和 IP 白名单才能完成端到端验证。
- 小红书/今日头条第一阶段为发布包，不是官方自动发布。

## Commit 状态

未提交。
