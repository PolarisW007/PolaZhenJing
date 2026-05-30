# Release Manifest：文章多平台发布中心

日期：2026-05-30

## 变更摘要

- 新增后台多平台发布中心 `/admin/social/`。
- 微信公众号支持官方 API 草稿创建、确认发布、状态查询。
- 小红书和今日头条支持半自动发布包和人工 URL 回填。
- 新增 SQLite 发布记录表 `social_publications`、`social_publication_events`。

## 待发布范围

- Flask 后端：`app/social_publish.py`、`app/__init__.py`。
- Jinja 模板：发布中心模板、文章列表/详情入口、后台导航。
- 文档：需求、PRD、SDD、开发日志、发布清单。
- 测试：`tests/test_social_publish.py`。

## 部署面

- 云端目录：`/PolaZhenjing`。
- 服务：`polazj.service`。
- 配置：云端 `.env` 需要包含微信公众号 `WECHAT_MP_APP_ID` / `WECHAT_MP_APP_SECRET`。
- 数据：应用启动时幂等创建 SQLite 发布表，无破坏性迁移。

## 发布前验证

- `python3 -m py_compile app/social_publish.py app/__init__.py app/uploader.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests`：14 passed。
- `git diff --check`：通过。
- Flask test client：发布中心和单篇发布页均 200。

## 发布步骤

| 步骤 | 动作 | 风险 |
| --- | --- | --- |
| 1 | commit 并 push 到 `origin/main` | 推送失败则停止 |
| 2 | 云端 `/PolaZhenjing` 备份当前 commit 和 `.env` | 无 |
| 3 | 云端 `git pull --ff-only` | 若云端有未提交改动则停止 |
| 4 | 云端写入微信公众号环境变量 | 密钥不可回显 |
| 5 | 云端 `py_compile` 和最小测试 | 依赖不全则需补装 |
| 6 | 重启 `polazj.service` | 短暂服务重启 |
| 7 | 验证线上路由、云端出口 IP、微信 token | IP 白名单可能阻塞 |

## 发布后验证

- `systemctl is-active polazj.service`。
- `GET https://aipd.me/PolaZhenjing/admin/social/` 未登录返回登录流程。
- 云端 `curl https://api.ipify.org` 获取固定出口 IP。
- 云端调用微信 token 接口：若白名单未配置，记录微信返回的 IP；加入白名单后重试。

## 回滚方案

- `cd /PolaZhenjing && git reset --hard <previous_commit>`。
- 恢复 `.env` 备份。
- `systemctl restart polazj.service`。
- 新增 SQLite 表可保留，不影响旧功能。

## 观察项

- 微信接口是否报 IP 白名单、接口权限或素材上传错误。
- 发布中心是否可登录访问。
- 文章生成、编辑、公开展示路径是否保持正常。
