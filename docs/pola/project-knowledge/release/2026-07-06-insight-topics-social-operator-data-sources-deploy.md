# 2026-07-06 洞察选题社媒运营与数据源更新云端发布记录

## 发布对象

- 项目：PolaZhenJing
- 云端目录：`/PolaZhenjing`
- 服务：`polazj.service`
- 目标分支：`origin/main`
- 目标 commit：`d1f49b0 feat: 补强洞察选题数据源池`

## 发布面

- 后端：`app/insight_topics.py`
- 后台页面：`app/templates/insight_topics.html`
- 测试与文档：`tests/test_admin_workbench_insight_topics.py`、`docs/pola/project-knowledge/*`
- 不涉及：数据库迁移、依赖安装、环境变量、secret、systemd 配置、nginx 配置。

## 发布前验证

- `.venv/bin/python -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：`12 passed`。
- `.venv/bin/python -m pytest tests -q`：`105 passed`。
- RSS live smoke：`collect_rss_signals(days=30, limit_per_feed=4)` 采集 30 条信号。
- `validate_function_test_cases.py`：PASS，9 个验收项 / 6 个 feature / 9 个 case。
- `validate_pola_skills.py`：PASS。

## 发布步骤

1. 云端记录当前 HEAD、状态和服务状态。
2. 云端创建备份分支：`backup/pre-insight-social-operator-YYYYMMDDHHMMSS`。
3. 备份生产运行数据：`data/insight_topics.json`。
4. `git fetch origin main`。
5. `git merge --ff-only origin/main`。
6. 运行云端语法检查和相关测试。
7. 重启 `polazj.service`。
8. 验证服务 active、HTTP smoke 和日志。

## 回滚方案

```bash
cd /PolaZhenjing
git reset --hard <pre_deploy_head>
cp /root/polazj-backups/insight-social-operator-YYYYMMDDHHMMSS/insight_topics.json data/insight_topics.json
systemctl restart polazj.service
systemctl is-active polazj.service
```

回滚触发条件：

- `polazj.service` 重启失败。
- `/PolaZhenjing/admin/login` 或 `/PolaZhenjing/articles` 线上 smoke 失败。
- 选题相关测试在云端失败且无法立即定位。

## 实际发布记录

- 发布时间：2026-07-06 22:30 CST。
- 发布前云端 HEAD：`6cbadb63ea1c5ef4c0142fd3188e12fe0bb6912d`。
- 发布后云端 HEAD：`d1f49b0`。
- 备份分支：`backup/pre-insight-social-operator-20260706222858`。
- 数据备份：`/root/polazj-backups/insight-social-operator-20260706222858/insight_topics.json`。
- 代码更新方式：`git fetch origin main` 后 `git merge --ff-only origin/main`，保留云端 `_posts/`、图片、`data/insight_topics.json`、`data/theme.json` 等生产运行数据改动。
- 服务重启：`systemctl restart polazj.service`，重启后 `active`。
- 服务进程：gunicorn 2 workers，启动后内存约 88MB。

## 云端验证

- `.venv/bin/python -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：`12 passed in 1.20s`。
- `.venv/bin/python -m pytest tests -q`：`105 passed in 3.13s`。
- RSS live smoke：`26` 条信号，包含 `microsoft_official_blog=5`、`aws_ml_blog=8`、`github_ai_ml_blog=4`、`sequoia_stories=1`。
- HTTPS smoke：
  - `/PolaZhenjing/admin/login`：200。
  - `/PolaZhenjing/admin/insights/topics`：302，未登录保护正常。
  - `/PolaZhenjing/articles`：200。
- 管理员模板渲染 smoke：`/admin/insights/topics` 返回 200，包含 `AI 行业社媒运营选题`、`topic-lane`、`topic-hook`、`topic-structure`。
- 服务日志：发布后 5 分钟 `journalctl -u polazj.service -p warning..alert` 无记录。

## 发布结论

Deployed。线上代码已更新到 `d1f49b0`，服务 active，核心 smoke 通过。

## 同步记录

- 钉钉发布记录文档：`https://alidocs.dingtalk.com/i/nodes/OG9lyrgJPzp47NdBCvpRDjZyWzN67Mw4`。
- AI 表格 `开发日志` 表记录：`recordId=bEFPQt5IGz`。
- 同步校验：钉钉文档和 AI 表格记录均已回读成功。
