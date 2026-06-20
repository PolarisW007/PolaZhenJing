# 发布记录：每日选题线上信号抓取上线

日期：2026-06-20

## 发布目标

- 将 Admin 洞察选题池从静态种子/人工底料升级为可手动刷新线上信号。
- 支持从 PolaNews、Hacker News、GitHub Search、公开 RSS 提取周期信号并生成候选选题。
- 保持既有工作台、状态打标、一键导入上传、未登录保护不回归。

## 发布范围

- `app/insight_topics.py`
- `app/admin_workbench.py`
- `app/templates/insight_topics.html`
- `app/templates/admin_workbench.html`
- `tests/test_admin_workbench_insight_topics.py`
- `docs/pola/arch-reference.md`
- `docs/pola/project-knowledge/requirements/2026-06-20-daily-insight-topic-crawler.md`
- `docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-crawler-prd.md`
- `docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-crawler-spec.md`
- `docs/pola/project-knowledge/architecture/2026-06-20-daily-insight-topic-crawler-sdd.md`
- `docs/pola/project-knowledge/devlogs/2026-06-20-daily-insight-topic-crawler.md`
- `docs/pola/project-knowledge/delivery/daily-insight-topic-crawler/`

## 不发布范围

- 不覆盖 `_posts/`。
- 不覆盖 `.env`、数据库、正式 `data/insight_topics.json`、上传图片和运行时缓存。
- 不新增 cron/systemd 定时任务；刷新仍由管理员手动触发。
- 不抓取登录态平台内容，不使用 X/Twitter 私有抓取。

## 本机验证

- `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：Pass。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：`6 passed`。
- 临时 JSON 真实网络 smoke：`signals=136`、`topics=24`、`source_counts={polanews:60,hackernews:46,github:19,rss:11}`、`errors=[]`。
- Function test cases harness：Pass，覆盖 8 个验收点、5 个 feature、7 个 case。
- `git diff --check`：Pass。

## 云端发布

- 服务器：`pola-server` / `/PolaZhenjing`。
- 发布方式：精确 `rsync -avR` 发布范围文件，未执行 `git pull`，避免服务器既有 `_posts` 脏改被影响。
- 发布前服务状态：`polazj.service active`。
- 备份目录：`/opt/backups/polazj-daily-insight-crawler-20260620144630`。

## 云端验证

- `.venv/bin/python -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：Pass。
- `PYTHONPATH=. .venv/bin/pytest tests/test_admin_workbench_insight_topics.py -q`：`6 passed in 0.99s`。
- 云端临时 JSON 真实网络 smoke：
  - `server_signals=132`
  - `server_topics=24`
  - `server_sources={'polanews': 60, 'hackernews': 47, 'github': 19, 'rss': 6}`
  - `server_errors=[]`
- Function test cases harness：Pass，覆盖 8 个验收点、5 个 feature、7 个 case。
- `systemctl restart polazj.service`：成功。
- `systemctl is-active polazj.service`：`active`。
- 公网 smoke：
  - `/PolaZhenjing/admin/login`：200。
  - `/PolaZhenjing/admin/workbench`：302 到登录。
  - `/PolaZhenjing/admin/insights/topics`：302 到登录。
  - `/PolaZhenjing/admin/upload`：302 到登录。
- 云端认证态 test-client smoke：
  - `/admin/workbench`：200，包含 `Admin 工作台`、`PolaNews`、`公开线上信号`。
  - `/admin/insights/topics`：200，包含 `洞察文章选题`、`刷新线上选题`、`PolaNews`、`线上信号刷新`。

## 回滚

```bash
ssh pola-server
cd /PolaZhenjing
BACKUP_DIR=/opt/backups/polazj-daily-insight-crawler-20260620144630
tar -xzf "$BACKUP_DIR/app-insight-crawler.tgz" -C /PolaZhenjing
tar -xzf "$BACKUP_DIR/project-knowledge-snapshot.tgz" -C /PolaZhenjing
systemctl restart polazj.service
systemctl is-active polazj.service
```

## 风险记录

- 外部源网络延迟存在，当前仅管理员手动刷新触发；普通文章浏览、上传页打开和工作台列表不主动抓取。
- 每个 HTTP 请求有 8 秒超时，分源失败隔离。
- 真实网络 smoke 使用 `/tmp` 临时 JSON，未污染正式选题池。
