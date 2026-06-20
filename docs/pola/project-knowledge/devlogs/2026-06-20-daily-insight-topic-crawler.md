# 开发日志：每日选题线上信号抓取

## 背景

用户反馈每日选题目前像是从 AI 表格或静态底料来，期望参考 `last30days` 的多源抓取思路，并结合 PolaNews 周期数据，从全网线上信号生成更真实的洞察选题。

## 改动

- `app/insight_topics.py`
  - 新增 `InsightSignal`、PolaNews/Hacker News/GitHub/RSS 采集器。
  - 新增相关性过滤、评分、聚类、证据链接归一化。
  - 新增 `refresh_topics_from_sources()`，手动刷新线上信号并写入 `data/insight_topics.json`。
  - 扩展 topic 字段：`source_type`、`source_count`、`evidence_links`、`score`、`generated_at`、`cluster_key`。
  - 刷新合并保留人工状态，避免同一个钉钉 source_url 的种子选题互相串状态。
- `app/admin_workbench.py`
  - 新增 `POST /admin/insights/topics/refresh`。
  - 工作台和选题页传入最近刷新信息。
- `app/templates/insight_topics.html`
  - 新增线上信号刷新面板、周期选择、最近刷新摘要、证据链接展示。
- `app/templates/admin_workbench.html`
  - 更新洞察选题模块说明和最近刷新提示。
- `tests/test_admin_workbench_insight_topics.py`
  - 新增刷新、状态保留、证据导入测试。
- `docs/pola/arch-reference.md`
  - 补充洞察选题池数据流和抓取约束。
- 新增交付记录：
  - `docs/pola/project-knowledge/requirements/2026-06-20-daily-insight-topic-crawler.md`
  - `docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-crawler-prd.md`
  - `docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-crawler-spec.md`
  - `docs/pola/project-knowledge/architecture/2026-06-20-daily-insight-topic-crawler-sdd.md`
  - `docs/pola/project-knowledge/delivery/daily-insight-topic-crawler/`

## 验证

- `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`
  - 通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`
  - 通过，`6 passed`。
- 临时 JSON 真实网络 smoke：调用 `refresh_topics_from_sources(days=7)`，将 `INSIGHT_TOPICS_FILE` 指向 `/tmp/pzj-insight-topics-live-smoke.json`。
  - `signals=136`
  - `topics=24`
  - `source_counts={polanews:60,hackernews:46,github:19,rss:11}`
  - `errors=[]`
  - 样例：`NousResearch/hermes-agent`、`OpenCLI`、`AI生成和人类写作之间的区隔`、`用AI报高考志愿靠谱吗？`、`三天内连失两位传奇：谷歌的AI人才大坝，正在决堤？`
- `.venv/bin/python /Users/wangchang/.agents/skills/pola-test-gate/scripts/validate_function_test_cases.py --prd docs/pola/project-knowledge/requirements/2026-06-20-daily-insight-topic-crawler.md --prd docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-crawler-prd.md --sdd docs/pola/project-knowledge/architecture/2026-06-20-daily-insight-topic-crawler-sdd.md --spec docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-crawler-spec.md --cases docs/pola/project-knowledge/delivery/daily-insight-topic-crawler/function_test_cases.json`
  - 通过，覆盖 8 个验收点、5 个 feature、7 个 case。
- `git diff --check`
  - 通过。

## 风险与护栏

- 风险等级：P2。涉及外部网络抓取和后台管理数据刷新，但没有自动定时任务。
- 每个 HTTP 请求设置 8 秒超时；分源失败隔离，不影响现有选题池可用性。
- PolaNews 使用多关键词 search，不再只取全站最新流；同时加相关性过滤。
- 英文 `AI` 使用词边界匹配，避免 `train` 这类误命中。
- 选题必须带 `evidence_links`；导入上传时把证据链接写入 Markdown。
- 本次未修改正式 `data/insight_topics.json`，真实 smoke 写入 `/tmp`。
- 未提交 secret、token、cookie、私钥或 `.env`。

## Commit 状态

- 尚未提交。

## 云端发布

- 发布方式：精确 `rsync -avR` 同步本次相关 app/template/test/docs 文件到 `pola-server:/PolaZhenjing/`，未覆盖 `_posts/`、`.env`、正式 `data/insight_topics.json`。
- 备份目录：`/opt/backups/polazj-daily-insight-crawler-20260620144630`。
- 云端验证：
  - `.venv/bin/python -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：通过。
  - `PYTHONPATH=. .venv/bin/pytest tests/test_admin_workbench_insight_topics.py -q`：`6 passed in 0.99s`。
  - 云端临时 JSON 真实网络 smoke：`server_signals=132`、`server_topics=24`、`server_sources={'polanews': 60, 'hackernews': 47, 'github': 19, 'rss': 6}`、`server_errors=[]`。
  - 云端 function test cases harness：通过，覆盖 8 个验收点、5 个 feature、7 个 case。
- 服务重启：
  - `systemctl restart polazj.service`：成功。
  - `systemctl is-active polazj.service`：`active`。
  - `journalctl` 短窗口只看到正常 stop/start 和 worker boot。
- 公网 smoke：
  - `https://aipd.me/PolaZhenjing/admin/login`：200。
  - `https://aipd.me/PolaZhenjing/admin/workbench`：302 到登录，符合未登录保护。
  - `https://aipd.me/PolaZhenjing/admin/insights/topics`：302 到登录，符合未登录保护。
  - `https://aipd.me/PolaZhenjing/admin/upload`：302 到登录，符合未登录保护。
- 云端认证态 test-client smoke：
  - `/admin/workbench`：200，包含 `Admin 工作台`、`PolaNews`、`公开线上信号`。
  - `/admin/insights/topics`：200，包含 `洞察文章选题`、`刷新线上选题`、`PolaNews`、`线上信号刷新`。
