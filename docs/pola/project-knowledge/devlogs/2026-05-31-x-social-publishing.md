# 开发日志：X 自动发布

日期：2026-05-31

## 目标

在现有多平台发布中心中接入 X 官方 API 自动发帖能力；小红书本次不实现。

## 改动记录

- `app/social_publish.py`
  - 新增 `x` 平台配置。
  - 新增 `X_USER_ACCESS_TOKEN` 配置状态读取。
  - 新增 X 文案生成，控制在 280 字符以内。
  - 新增 X 媒体上传和 `POST /2/tweets` 发帖调用。
  - 新增同篇文章 X 成功发布记录去重，重复任务标记为 `skipped_duplicate`。
  - 新增 `/admin/social/articles/<filename>/x/post` 路由。
- `app/templates/social_publish_index.html`
  - 发布中心列表新增 X 状态列。
- `app/templates/social_publish_article.html`
  - 单篇发布页新增 X 发布卡片。
- `tests/test_social_publish.py`
  - 增加 X 文案长度和配置读取测试。
- `docs/pola/project-knowledge/`
  - 新增 X 自动发布需求、PRD、SDD 和本开发日志。

## 配置

- 新增服务端环境变量：`X_USER_ACCESS_TOKEN`。
- token 不写入代码、文档正文、测试输出和 git diff。

## 验证记录

- `python3 -m py_compile app/social_publish.py app/__init__.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py`：9 passed。
- `PYTHONPATH=. .venv/bin/pytest tests`：19 passed。
- `git diff --check`：通过。
- Flask test client：未登录访问 `/admin/social/` 和单篇发布页均 302 到 `/admin/login`。
- 真实 X 发帖：待配置 `X_USER_ACCESS_TOKEN` 后验证；当前实现会在未配置时记录 `not_configured`，不会误调用 X API。
- 云端部署：已精确同步本次相关文件到 `/PolaZhenjing`，云端 `tests/test_social_publish.py` 9 passed，`polazj.service` 为 `active`，线上发布中心未登录 302 到登录页。
- 云端配置：`X_USER_ACCESS_TOKEN` 当前未配置，X 文案生成 smoke 长度 278。

## 风险

- X API 权限、额度、OAuth scope 不满足时会返回平台错误；系统会把错误写入发布记录。
- 当前未实现 OAuth 授权回调，token 由服务端环境变量维护。

## Commit 状态

待提交：X 自动发布实现、测试和交付文档。
